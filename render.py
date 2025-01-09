#!/usr/bin/env python3
"""
Render HTML pages from podcast episode segment data.

This script processes JSONL files containing podcast episode segments,
combines them with metadata, and generates an HTML page using Jinja2 templates.
The output is a searchable, filterable interface for browsing podcast segments.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import jsonlines
from jinja2 import Environment, FileSystemLoader

from dump import dump  # Debugging utility for printing values


def generate_html(input_files):
    """
    Generate HTML content from segment JSONL files and their metadata.

    Args:
        input_files (list): List of paths to segment JSONL files

    Returns:
        str: Rendered HTML content ready to be written to a file
    """
    # Set up Jinja2 environment and load template
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("index.html")

    # List to collect all segments from all input files
    all_segments = []

    for input_file in input_files:
        base_path = Path(input_file).with_suffix("")
        input_path = base_path.with_suffix(".synced.jsonl")
        metadata_path = base_path.with_suffix(".json")

        with open(metadata_path) as f:
            metadata = json.load(f)

        print()  # Spacer for debug output
        dump(input_file)  # Debug print current file being processed

        # Determine which URL to use (prefer final_url if available)
        chosen_url = metadata["url"]  # Default to original URL
        if "final_url" in metadata and metadata["final_url"] is not None:
            chosen_url = metadata["final_url"]
        dump(chosen_url)  # Debug print chosen URL

        with jsonlines.open(input_path) as reader:
            for segment in reader:
                # Extract and process segment timing information
                start = int(segment["start"])
                end = int(segment["end"])
                duration = end - start
                # Format duration as "XmYYs" for >=60s, else "Xs"
                duration_str = (
                    f"{duration // 60}m{duration % 60:02d}s"
                    if duration >= 60
                    else f"{duration}s"
                )

                # Process segment text (currently using full text without truncation)
                full_text = segment["text"].replace("\n", " ")
                """
                # Example of text truncation logic (currently commented out)
                TRUNC = 200
                if len(full_text) > TRUNC:
                    trunc_at = full_text[:TRUNC].rfind(' ')
                    text = full_text[:trunc_at] + "..." if trunc_at > TRUNC - 50 else full_text[:TRUNC - 3] + "..."
                else:
                """
                text = full_text  # Currently using full text without truncation

                # Parse and format the episode date
                date_obj = datetime.strptime(
                    metadata["date"], "%a, %d %b %Y %H:%M:%S %z"
                )
                formatted_date = date_obj.strftime("%b %Y")  # Short format for display
                full_date = date_obj.strftime("%Y-%m-%d")  # Full date for filtering

                all_segments.append(
                    {
                        "start": start,
                        "end": end,
                        "duration_str": duration_str,
                        "text": text,
                        "url": chosen_url,
                        "title": metadata["title"],
                        "date": formatted_date,
                        "full_date": full_date,  # Add full date for filtering
                        "date_obj": date_obj,  # Store the datetime object for sorting
                    }
                )

    # Create list of unique episodes for filtering dropdown
    episodes = sorted(
        set(
            (
                segment["date_obj"].strftime("%Y-%m-%d"),  # Sort key
                segment["date_obj"].strftime("%Y %B"),  # Display text
            )
            for segment in all_segments
        ),
        key=lambda x: x[0],  # Sort by date string
        reverse=True,  # Newest first
    )

    # Sort segments by:
    # 1. Episode date (newest first)
    # 2. Start time within episode (latest first)
    sorted_segments = sorted(
        all_segments,
        key=lambda x: (x["date_obj"].strftime("%Y-%m-%d"), -x["start"]),
        reverse=True,
    )

    # Clean up segments by removing temporary date_obj before rendering
    for segment in sorted_segments:
        del segment["date_obj"]  # Not needed in template after sorting

    return template.render(segments=sorted_segments, episodes=episodes)


def main():
    """
    Main entry point for the render script.

    Processes command line arguments, generates HTML, and writes output file.
    """
    if len(sys.argv) < 2:
        print("Usage: python render.py file1_segments.jsonl [file2_segments.jsonl ...]")
        sys.exit(1)

    # Get input files from command line arguments
    input_files = sys.argv[1:]

    # Generate HTML content
    html = generate_html(input_files)

    # Write output to website/index.html
    output_file = Path("website") / "index.html"
    with open(output_file, "w") as f:
        f.write(html)

    print(f"Saved to {output_file}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3

import json
import sys
from datetime import datetime
from pathlib import Path

import jsonlines
from jinja2 import Environment, FileSystemLoader

from dump import dump


def generate_html(input_files):
    # Set up Jinja2 environment
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("index.html")

    all_segments = []

    for input_file in input_files:
        base_path = Path(input_file).with_suffix("")
        input_path = base_path.with_suffix(".synced.jsonl")
        metadata_path = base_path.with_suffix(".json")

        with open(metadata_path) as f:
            metadata = json.load(f)

        print()
        dump(input_file)
        # Use final_url if it exists in metadata, otherwise use url
        chosen_url = metadata["url"]  # Always use url as default
        if "final_url" in metadata and metadata["final_url"] is not None:
            chosen_url = metadata["final_url"]
        dump(chosen_url)

        with jsonlines.open(input_path) as reader:
            for segment in reader:
                start = int(segment["start"])
                end = int(segment["end"])
                duration = end - start
                duration_str = (
                    f"{duration // 60}m{duration % 60:02d}s"
                    if duration >= 60
                    else f"{duration}s"
                )

                full_text = segment["text"].replace("\n", " ")
                """
                TRUNC = 200
                if len(full_text) > TRUNC:
                    trunc_at = full_text[:TRUNC].rfind(' ')
                    text = full_text[:trunc_at] + "..." if trunc_at > TRUNC - 50 else full_text[:TRUNC - 3] + "..."
                else:
                """
                text = full_text

                # Parse and format the date
                date_obj = datetime.strptime(
                    metadata["date"], "%a, %d %b %Y %H:%M:%S %z"
                )
                formatted_date = date_obj.strftime("%b %Y")
                full_date = date_obj.strftime("%Y-%m-%d")  # Add full date for filtering

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

    # Extract unique episodes (year-month combinations) from segments
    episodes = sorted(set(
        (segment["date_obj"].strftime("%Y-%m-%d"), segment["date_obj"].strftime("%Y %B"))
        for segment in all_segments
    ), key=lambda x: x[0], reverse=True)
    
    # Sort segments by date (newest first) and then by start time within each episode
    sorted_segments = sorted(all_segments,
                           key=lambda x: (x["date_obj"].strftime("%Y %B"), x["start"]),
                           reverse=True)
    
    # Remove date_obj before rendering as it's not needed in the template
    for segment in sorted_segments:
        del segment["date_obj"]
        
    return template.render(segments=sorted_segments, episodes=episodes)


def main():
    if len(sys.argv) < 2:
        print("Usage: python render.py file1_segments.jsonl [file2_segments.jsonl ...]")
        sys.exit(1)

    input_files = sys.argv[1:]
    html = generate_html(input_files)

    output_file = Path("website") / "index.html"
    with open(output_file, "w") as f:
        f.write(html)

    print(f"Saved to {output_file}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3

"""
Transcription Alignment and Punctuation Processing

This module handles the alignment of transcription chunks from audio files,
ensuring proper word boundaries and punctuation. It processes JSONL files
containing word-level transcription data and produces aligned output with
proper text formatting.

The main functions:
- align_transcription: Aligns transcription chunks and handles overlapping sections of audio transcription
- main: CLI interface for processing multiple transcription files
"""

import re
import sys
import textwrap
from pathlib import Path

import jsonlines

from dump import dump


def align_transcription(input_file, output_file, output_text):
    """
    Align transcription chunks by removing overlapping words between chunks.

    Processes a JSONL file containing word-level transcription data and:
    1. Aligns words with their corresponding text segments
    2. Handles overlapping timestamps between chunks
    3. Produces clean, aligned output with proper word boundaries
    4. Generates a formatted text file with word wrapping

    The alignment process:
    - Matches words to their position in the transcription text
    - Removes non-alphanumeric characters from word boundaries
    - Handles cases where words span chunk boundaries
    - Merges overlapping segments using a time threshold

    Args:
        input_file: Path to input JSONL file with transcription data
        output_file: Path to output JSONL file for aligned transcription
        output_text: Path to output text file for word-wrapped transcription
    """
    overlap_threshold = 0.05  # seconds for considering words as overlapping

    aligned = []
    words = []

    with jsonlines.open(input_file) as reader:
        for obj in reader:
            if "word" in obj:
                words.append(obj)
                continue

            text = obj["text"]

            for wobj in words:
                word = wobj["word"]

                if not [c for c in word if c.isalnum()]:
                    print("skipping non-alphanum:", word)
                    continue

                # Strip non-alnums from ends only
                clean_word = word.strip("".join(c for c in word if not c.isalnum()))
                # Try splitting with original word first
                parts = text.split(clean_word, 1)
                if len(parts) != 2:
                    print(
                        f"Warning: Could not align word '{word}' in text: {text[:100]}"
                    )
                    continue

                rest = parts[1]
                rest = rest.lstrip(" ".join(c for c in rest if not c.isalnum()))

                this = text[: len(text) - len(rest)]
                wobj["text"] = this

                # assert abs(len(this) - len(word)) < 10, f"{word} // {this}"

                aligned.append(wobj)

                text = rest

            words = []

    merged = []
    last_time = 0
    aligned.reverse()
    while aligned:
        obj = aligned.pop()

        start = obj["start"]
        if start < last_time:
            mid = (start + last_time) / 2.0
            merged = [m for m in merged if m["start"] <= mid]

            while obj["start"] < mid and aligned:
                obj = aligned.pop()

        last_time = obj["start"]

        merged.append(obj)

    with jsonlines.open(input_file) as reader, jsonlines.open(
        output_file, mode="w"
    ) as writer, open(output_text, "w") as txt_writer:
        full_text = ""
        for obj in merged:
            writer.write(obj)
            full_text += obj.get("text", "")

        # Write word-wrapped text to output file
        wrapped_text = "\n".join(textwrap.wrap(full_text, width=80))
        txt_writer.write(wrapped_text)
        # print(wrapped_text)


def main():
    """
    Command-line interface for processing transcription files.

    Processes one or more JSONL transcription files, producing:
    - Aligned JSONL output with proper word boundaries
    - Formatted text output with word wrapping

    Handles:
    - Multiple input files
    - File existence checking
    - Overwrite protection (unless --force is specified)
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Align transcription chunks and process punctuation",
        epilog="Example: punct.py *.jsonl --force",
    )
    parser.add_argument("files", nargs="+", help="Input JSONL files to process")
    parser.add_argument(
        "--force", action="store_true", help="Overwrite existing output files"
    )
    args = parser.parse_args()

    for input_file in args.files:
        if not Path(input_file).exists():
            print(f"Error: File {input_file} not found")
            continue

        # Create output file with same path prefix but new suffix
        base_path = Path(input_file).with_suffix("")
        input_path = base_path.with_suffix(".transcription.jsonl")
        output_path = base_path.with_suffix(".punct.jsonl")
        output_text = base_path.with_suffix(".punct.txt")

        if output_path.exists() and not args.force:
            print(f"Skipping {input_path} - output already exists at {output_path}")
            print("Use --force to overwrite existing files")
            continue

        align_transcription(input_path, output_path, output_text)
        print(f"Aligned transcription saved to {output_path}")
        print(f"Word-wrapped text saved to {output_text}")


if __name__ == "__main__":
    """
    Entry point for the script when run directly from command line.
    Processes transcription files according to command line arguments.
    """
    main()

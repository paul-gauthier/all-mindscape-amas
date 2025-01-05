#!/usr/bin/env python3

import jsonlines
import re
import sys
from pathlib import Path

def align_transcription(input_file, output_file):
    """
    Align transcription chunks by removing overlapping words between chunks.

    Args:
        input_file: Path to input JSONL file with transcription data
        output_file: Path to output JSONL file for aligned transcription
    """
    overlap_threshold = 0.1  # seconds for considering words as overlapping

    prev_chunk_end = 0
    skipped_words = []

    with jsonlines.open(input_file) as reader, jsonlines.open(output_file, mode='w') as writer:
        for obj in reader:
            if "text" in obj:
                text = obj["text"]
                for word in skipped_words:
                    parts = re.split(r'\b' + re.escape(word) + r'\b', text, maxsplit=1)
                    text = parts[1].lstrip() if len(parts) > 1 else text
                obj["text"] = text

                # Write the text segment
                writer.write(obj)
                # Clear previous words for next chunk
                prev_chunk_end = obj["end"]
                skipped_words = []
            elif "word" in obj:
                # If current word starts before last word ends (with some threshold)
                if obj["start"] <= last_word["end"]:
                    skipped_words.append(obj["word"])
                    continue

                write.write(obj)

        # Write any remaining words after the last text segment
        for word in previous_words:
            writer.write(word)

def main():
    if len(sys.argv) != 2:
        print("Usage: python align.py <transcription_file.jsonl>")
        sys.exit(1)

    input_file = sys.argv[1]
    if not Path(input_file).exists():
        print(f"Error: File {input_file} not found")
        sys.exit(1)

    output_file = Path(input_file).stem + "_aligned.jsonl"
    align_transcription(input_file, output_file)
    print(f"Aligned transcription saved to {output_file}")

if __name__ == "__main__":
    main()

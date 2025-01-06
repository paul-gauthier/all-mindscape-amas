#!/usr/bin/env python3

import jsonlines
import re
import sys
from pathlib import Path
from dump import dump

def align_transcription(input_file, output_file):
    """
    Align transcription chunks by removing overlapping words between chunks.

    Args:
        input_file: Path to input JSONL file with transcription data
        output_file: Path to output JSONL file for aligned transcription
    """
    overlap_threshold = 0.05  # seconds for considering words as overlapping

    prev_chunk_end = 0
    skipped_words = []

    with jsonlines.open(input_file) as reader, jsonlines.open(output_file, mode='w') as writer:
        for obj in reader:
            if "text" in obj:
                orig_text = text = obj["text"]
                for word in skipped_words:
                    #dump(word)
                    parts = re.split(r'\b' + re.escape(word) + r'\b', text, maxsplit=1)

                    text = parts[1].lstrip(''.join(c for c in parts[1] if not c.isalnum())) if len(parts) > 1 else text

                    #dump(text[:100])

                trimmed = len(orig_text) - len(text) -1

                obj["text"] = text
                print("...", orig_text[:100])
                print("...", " "*trimmed, text[:100])
                print()
                print(text[-100:], "...")

                # Write the text segment
                writer.write(obj)
                # Clear previous words for next chunk
                prev_chunk_end = obj["end"]
                skipped_words = []
            elif "word" in obj:
                # If current word starts before last word ends (with some threshold)
                if obj["start"] <= prev_chunk_end + overlap_threshold:
                    skipped_words.append(obj["word"])
                    continue

                writer.write(obj)

def main():
    if len(sys.argv) < 2:
        print("Usage: python align.py <transcription_file1.jsonl> [file2.jsonl ...]")
        sys.exit(1)

    for input_file in sys.argv[1:]:
        if not Path(input_file).exists():
            print(f"Error: File {input_file} not found")
            continue

        output_file = Path(input_file).stem + "_aligned.jsonl"
        align_transcription(input_file, output_file)
        print(f"Aligned transcription saved to {output_file}")

if __name__ == "__main__":
    main()

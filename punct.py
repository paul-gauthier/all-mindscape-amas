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
                    dump(word)
                    continue

                parts = re.split(r'\b' + re.escape(word) + r'\b', text, maxsplit=1)
                if len(parts) != 2:
                    dump(word)
                    dump(text[:100])
                    dump(len(parts))
                    assert False

                rest = parts[1].lstrip(''.join(c for c in parts[1] if not c.isalnum()))

                this = text[:len(text) - len(rest)]
                wobj["text"] = this

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
            mid = (start + last_time)/2.0
            merged = [m for m in merged if m["start"] < mid]

            while obj["start"] < mid and aligned:
                obj = aligned.pop()

        last_time = obj["start"]

        merged.append(obj)

    with jsonlines.open(input_file) as reader, jsonlines.open(output_file, mode='w') as writer:
        for obj in merged:
            writer.write(obj)

        # print all the obj["text"] word wrapped to 80 cols. ai!

def main():
    if len(sys.argv) != 2:
        print("Usage: python align.py <transcription_file.jsonl>")
        sys.exit(1)

    input_file = sys.argv[1]
    if not Path(input_file).exists():
        print(f"Error: File {input_file} not found")
        sys.exit(1)

    output_file = Path(input_file).stem + "_punct.jsonl"
    align_transcription(input_file, output_file)
    print(f"Aligned transcription saved to {output_file}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3

import jsonlines
import re
import sys
from pathlib import Path
from dump import dump

def align_transcription(input_file, output_file, output_text):
    """
    Align transcription chunks by removing overlapping words between chunks.

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

                parts = text.split(word, 1)
                if len(parts) != 2:
                    dump(word)
                    dump(text[:100])
                    dump(len(parts))
                    assert False

                rest = parts[1]

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
            merged = [m for m in merged if m["start"] <= mid]

            while obj["start"] < mid and aligned:
                obj = aligned.pop()

        last_time = obj["start"]

        merged.append(obj)

    with jsonlines.open(input_file) as reader, jsonlines.open(output_file, mode='w') as writer, open(output_text, 'w') as txt_writer:
        full_text = ""
        for obj in merged:
            writer.write(obj)
            full_text += obj.get("text", "")

        # Write word-wrapped text to output file
        import textwrap
        wrapped_text = "\n".join(textwrap.wrap(full_text, width=80))
        txt_writer.write(wrapped_text)
        #print(wrapped_text)

def main():
    if len(sys.argv) < 2:
        print("Usage: python punct.py <transcription_file1.jsonl> [file2.jsonl ...]")
        sys.exit(1)

    for input_file in sys.argv[1:]:
        if not Path(input_file).exists():
            print(f"Error: File {input_file} not found")
            continue

        # Create output file with same path prefix but new suffix
        input_path = Path(input_file).with_suffix(".transcription.jsonl")
        output_file = input_path.with_suffix(".punct.jsonl")
        output_text = input_path.with_suffix(".punct.txt")
        align_transcription(input_path, output_file, output_text)
        print(f"Aligned transcription saved to {output_file}")
        # print text filename. ai!

if __name__ == "__main__":
    main()

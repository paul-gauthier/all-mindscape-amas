#!/usr/bin/env python3

import jsonlines
import re
import sys
from pathlib import Path
from dump import dump

# load_dotenv. ai!


def find_questions(text):
    pass

def align_transcription(input_file, output_file):
    with jsonlines.open(input_file) as reader:
        words = [obj for obj in reader]

    while words:
        text = pretty(words[:5000])
        dump(len(text))


        find_questions(text)


        break



def pretty(merged):
    full_text = ""
    for obj in merged:
        full_text += obj.get("text", "")

    # Print word-wrapped text
    import textwrap
    return "\n".join(textwrap.wrap(full_text, width=80))

def main():
    if len(sys.argv) != 2:
        print("Usage: python segment.py file.jsonl>")
        sys.exit(1)

    input_file = sys.argv[1]
    if not Path(input_file).exists():
        print(f"Error: File {input_file} not found")
        sys.exit(1)

    output_file = Path(input_file).stem + "_segments.jsonl"
    align_transcription(input_file, output_file)
    print(f"Saved to {output_file}")

if __name__ == "__main__":
    main()

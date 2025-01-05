#!/usr/bin/env python3

import litellm
import jsonlines
import re
import sys
from pathlib import Path
from dump import dump
from dotenv import load_dotenv

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic._internal._config")

load_dotenv()

SYSTEM="""
The user will share the transcript of a podcast episode.
It's an "Ask Me Anything" episode from Sean Carroll's Mindscape podcast.
He reads a series of questions from listeners and then answers them.

The questions often start like:
- Raul says why is the sky blue?
- AbacusPowerUser asks why do apples fall from trees?
- etc

Find all the sentences in the transcript which denote the start of a new
question.
Return every such sentence, one per line in a bullet list like this:

- Raul says why is the sky blue?
- AbacusPowerUser asks why do apples fall from trees?
""".strip()

def find_questions(text):
    model = "deepseek/deepseek-chat"

    messages=[
        dict(role="system", content=SYSTEM),
        dict(role="user", content=text),
    ]

    comp = litellm.completion(model=model, messages=messages)
    res = comp.choices[0].message.content
    print(res)

    # Parse bullet points and verify they exist in text
    questions = []
    for line in res.splitlines():
        if line.startswith("- "):
            question = line[2:].strip()
            present = question in text
            print()
            print(present, question)

    return questions


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

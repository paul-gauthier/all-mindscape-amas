#!/usr/bin/env python3

import warnings
warnings.filterwarnings("ignore", category=UserWarning)

import lox
import litellm
import jsonlines
import re
import sys
from pathlib import Path
from dump import dump
from dotenv import load_dotenv

load_dotenv()

SYSTEM="""
The user will share a transcript from a podcast episode.
It's from an "Ask Me Anything" episode from Sean Carroll's Mindscape podcast.
He reads a series of questions from listeners and then answers them.

Reply 2 concise sentences: a summary of the question and a summary of Sean's answer.

Start the first sentence with "<NAME> ...".

Or start it with "<NAME1>, <NAME2> and <NAME3> ..." if the user gives you a set of questions from multiple users (Sean sometimes groups related questions together). Only provide a single concise sentence that summarizes the question topic that has been grouped.

Start the second sentence with "Sean ..."

ONLY REPLY WITH THE 2 SENTENCES THAT SUMMARIZE THE QUESTION AND SEAN'S ANSWER.
BE VERY CONCISE!
TWO **SHORT** SENTENCES!
""".strip()


@lox.thread(25)
def summarize_one(text):
    model = "deepseek/deepseek-chat"

    messages=[
        dict(role="system", content=SYSTEM),
        dict(role="user", content=text),
    ]

    #print()
    #print()
    #dump(text)

    comp = litellm.completion(model=model, messages=messages, temperature=0)
    reply = comp.choices[0].message.content

    num_words = len(reply.split())
    max_words = 100
    while num_words > max_words: # max 3 rounds ai!
        messages += [
            dict(role="assistant", content=reply),
            dict(role="user", content="That is too long! Make it less than {max_words} words!"),
        ]
        comp = litellm.completion(model=model, messages=messages, temperature=0)
        reply = comp.choices[0].message.content

    #print()
    #dump(reply)

    return reply

def summarize(input_file, output_file, text_file):
    # Read input segments
    segments = []
    with jsonlines.open(input_file) as reader:
        segments = list(reader)

    print(f"Summarizing {len(segments)} segments...")

    # Process each segment
    for segment in segments:
        summary = summarize_one.scatter(segment['text'])

    summaries = summarize_one.gather(tqdm=True)
    for segment,summary in zip(segments,summaries):
        segment['text'] = summary

    # Save summarized JSONL
    with jsonlines.open(output_file, mode='w') as writer:
        writer.write_all(segments)

    # Save text summaries
    with open(text_file, 'w') as f:
        for summary in summaries:
            f.write(summary + '\n\n')


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Summarize podcast questions')
    parser.add_argument('files', nargs='+', help='Input JSONL files to process')
    parser.add_argument('--force', action='store_true', help='Overwrite existing output files')
    args = parser.parse_args()

    for input_file in args.files:
        base_path = Path(input_file).with_suffix("")
        input_path = base_path.with_suffix('.segments.jsonl')
        output_path = base_path.with_suffix(".summarized.jsonl")
        text_path = base_path.with_suffix(".summarized.txt")

        if not Path(input_path).exists():
            print(f"Error: File {input_path} not found")
            continue

        if output_path.exists() and not args.force:
            print(f"Skipping {input_path} - output already exists at {output_path}")
            print("Use --force to overwrite existing files")
            continue

        summarize(input_path, output_path, text_path)
        print(f"Saved to {output_path}")
        print(f"Text segments saved to {text_path}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
This module provides functionality to summarize podcast episode transcripts from Sean Carroll's
Mindscape podcast. It processes JSONL files containing question/answer segments, generates concise
summaries using AI models, and outputs both JSONL and text files with the summarized content.

Key Features:
- Processes multiple input files in parallel using threading
- Uses AI models to generate concise summaries of questions and answers
- Maintains original JSONL structure while replacing full text with summaries
- Produces both structured (JSONL) and plain text output formats
"""
import warnings

warnings.filterwarnings("ignore", category=UserWarning)

import re
import sys
from pathlib import Path

import jsonlines
import litellm
import lox
from dotenv import load_dotenv

from dump import dump

load_dotenv()


SYSTEM = """
The user will share a transcript from a podcast episode.
It's from an "Ask Me Anything" episode from Sean Carroll's Mindscape podcast.
He reads a series of questions from listeners and then answers them.

Reply 2 concise sentences: a summary of the question and a summary of Sean's answer.

Start the first sentence with "<NAME> ...".

Or start it with "<NAME1>, <NAME2> and <NAME3> ..." if the user gives you a set of questions from multiple users (Sean sometimes groups related questions together). Only provide a single concise sentence that summarizes the question topic that has been grouped.

Start the second sentence with "Sean ..."

ONLY REPLY WITH THE 2 SENTENCES THAT SUMMARIZE THE QUESTION AND SEAN'S ANSWER.
BE VERY CONCISE, AT MOST {max_words} TOTAL!
TWO **SHORT** SENTENCES!
""".strip()


@lox.thread(25)
def summarize_one(text):
    """
    Generate a concise summary of a single podcast question/answer segment using AI.

    Args:
        text (str): The full text of the question/answer segment to summarize

    Returns:
        str: A two-sentence summary containing:
             - A concise summary of the question(s)
             - A concise summary of Sean's answer
    """
    model = "deepseek/deepseek-chat"  # AI model to use for summarization

    max_words = 50  # Target maximum words for the summary

    messages = [
        dict(role="system", content=SYSTEM.format(max_words=max_words)),
        dict(role="user", content=text),
    ]

    # print()
    # print()
    # dump(text)

    comp = litellm.completion(model=model, messages=messages, temperature=0)
    reply = comp.choices[0].message.content

    num_words = len(reply.split())
    rounds = 0
    while num_words > max_words * 1.5 and rounds <= 3:
        messages += [
            dict(role="assistant", content=reply),
            dict(
                role="user",
                content=f"That is too long! Make it less than {max_words} words!",
            ),
        ]
        comp = litellm.completion(model=model, messages=messages, temperature=0)
        reply = comp.choices[0].message.content
        rounds += 1

    # print()
    # dump(reply)

    return reply


def summarize(input_file, output_file, text_file):
    """
    Process a JSONL file of podcast segments, generate summaries, and save results.

    Args:
        input_file (str): Path to input JSONL file containing full segments
        output_file (str): Path to save summarized JSONL output
        text_file (str): Path to save plain text version of summaries

    The function:
    1. Reads the input JSONL file containing question/answer segments
    2. Generates concise summaries for each segment in parallel
    3. Saves the summarized segments in JSONL format
    4. Creates a plain text version of all summaries
    """
    # Read input segments from JSONL file
    segments = []
    with jsonlines.open(input_file) as reader:
        segments = list(reader)

    print(f"Summarizing {len(segments)} segments...")

    # Process each segment
    for segment in segments:
        summary = summarize_one.scatter(segment["text"])

    summaries = summarize_one.gather(tqdm=True)
    for segment, summary in zip(segments, summaries):
        segment["text"] = summary

    # Save summarized JSONL
    with jsonlines.open(output_file, mode="w") as writer:
        writer.write_all(segments)

    # Save text summaries
    with open(text_file, "w") as f:
        for summary in summaries:
            f.write(summary + "\n\n")


def main():
    """
    Command-line interface for summarizing podcast question/answer segments.

    Processes one or more input files, generating summarized versions in both JSONL and text formats.
    Handles file existence checks and provides --force option to overwrite existing files.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Summarize podcast questions and answers from Sean Carroll's Mindscape podcast"
    )
    parser.add_argument("files", nargs="+", help="Input JSONL files to process")
    parser.add_argument(
        "--force", action="store_true", help="Overwrite existing output files"
    )
    args = parser.parse_args()

    for input_file in args.files:
        base_path = Path(input_file).with_suffix("")
        input_path = base_path.with_suffix(".segments.jsonl")
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

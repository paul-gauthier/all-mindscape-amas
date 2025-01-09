#!/usr/bin/env python3

"""
Transcription module using OpenAI Whisper API with word-level timestamps.

This module handles:
- Large audio file processing by splitting into chunks
- Word-level timestamp generation
- Parallel processing of audio chunks
- Output in both JSONL and text formats
"""

import warnings

# Suppress Pydantic warnings that can be noisy
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

import json
import os
import sys
from pathlib import Path

import jsonlines
import litellm
import lox
from dotenv import load_dotenv
from openai import OpenAI
from pydub import AudioSegment

from dump import dump

# Load environment variables from .env file
load_dotenv()


@lox.thread(10)
def transcribe_audio(chunk, audio_path):
    """
    Transcribe an audio chunk using OpenAI Whisper API with word-level timestamps.

    Args:
        chunk (AudioSegment): Audio chunk to transcribe
        audio_path (str): Temporary file path to save chunk for processing

    Returns:
        tuple: (list of word dicts, text segment dict)
            Word dict format: {"word": str, "start": float, "end": float}
            Text segment format: {"text": str, "start": float, "end": float}
    """

    print(f"Exporting chunk to {audio_path}...")
    chunk.export(audio_path, format="mp3")
    chunk_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
    print(f"Chunk size: {chunk_size_mb:.1f}MB")

    # Open audio file
    with open(audio_path, "rb") as audio_file:
        response = litellm.transcription(
            model="fireworks_ai/whisper-v3",
            # model="groq/whisper-large-v3-turbo",
            file=audio_file,
            response_format="verbose_json",
            timestamp_granularities=["word"],
        )

    # Extract words and full text with timestamps
    words = []
    for word in response.words:
        words.append(
            {
                "word": word["word"],
                "start": round(word["start"], 6),
                "end": round(word["end"], 6),
            }
        )

    # Add the full text with timestamps
    text_segment = {
        "text": response.text,
        "start": round(response.words[0]["start"], 6) if response.words else 0,
        "end": round(response.words[-1]["end"], 6)
        if response.words
        else response.duration,
    }

    return words, text_segment


def transcribe_large_audio(audio_path, output_file):
    """
    Handle large audio files by splitting into chunks and processing in parallel.

    Args:
        audio_path (str): Path to input audio file
        output_file (str): Path to save JSONL transcription output

    Processing details:
    - Splits audio into 10 minute chunks with 10 second overlap
    - Uses temporary directory for chunk storage
    - Processes chunks in parallel using lox threads
    - Adjusts timestamps to account for chunk offsets
    - Saves results in JSONL format with word-level timestamps
    """
    # Number of words to overlap between chunks
    OVERLAP_WORDS = 10

    audio = AudioSegment.from_file(audio_path)
    total_duration_ms = len(audio)
    print(f"Total duration: {total_duration_ms/(1000*60):.1f} minutes")

    # Start with a chunk size that's safely under 25MB (e.g., 10 minutes)
    chunk_duration_ms = 10 * 60 * 1000  # 10 minutes in milliseconds

    # Precompute all chunk positions
    chunk_positions = []
    current_position_ms = 0
    while current_position_ms < total_duration_ms:
        chunk_positions.append(current_position_ms)
        current_position_ms += chunk_duration_ms - 10 * 1000

    ###
    # chunk_positions = chunk_positions[:1]

    # Create temporary directory for chunk files
    import tempfile

    with tempfile.TemporaryDirectory() as temp_dir:
        for current_position_ms in chunk_positions:
            print()
            dump(current_position_ms)

            # Extract chunk with overlap
            chunk_end = min(current_position_ms + chunk_duration_ms, total_duration_ms)

            # Calculate and display progress
            percent_complete = (current_position_ms / total_duration_ms) * 100
            print(f"\nProgress: {percent_complete:.1f}% done chunking file")
            print(
                f"Extracting chunk from {current_position_ms/1000:.2f}s to {chunk_end/1000:.2f}s"
            )
            chunk = audio[current_position_ms:chunk_end]

            # Save chunk to unique temp file
            temp_path = os.path.join(temp_dir, f"chunk_{current_position_ms}.mp3")
            dump(temp_path)

            # Transcribe chunk
            print("Sending chunk to OpenAI API for transcription...")
            transcribe_audio.scatter(chunk, temp_path)

        results = transcribe_audio.gather(tqdm=True)

    with jsonlines.open(output_file, mode="w", flush=True) as writer:
        for current_position_ms, (chunk_words, chunk_text) in zip(
            chunk_positions, results
        ):
            dump(current_position_ms)
            print_words((chunk_words, chunk_text))

            if not chunk_words:
                break

            # Adjust timestamps with offset
            for word in chunk_words:
                word["start"] += current_position_ms / 1000  # Convert ms to seconds
                word["end"] += current_position_ms / 1000

            # Adjust text segment timestamps
            chunk_text["start"] += current_position_ms / 1000
            chunk_text["end"] += current_position_ms / 1000

            for word in chunk_words:
                writer.write(word)
            writer.write(chunk_text)

            print(f"Processed up to {current_position_ms/1000:.2f} seconds")


def print_words(words_and_text):
    """
    Print transcription results with timestamps for debugging.

    Args:
        words_and_text (tuple or list): Contains either:
            - Tuple of (words, text_segment)
            - List of word dicts
    """
    words, text = (
        words_and_text if isinstance(words_and_text, tuple) else (words_and_text, None)
    )

    # Print word-level timestamps
    # for word in words:
    #    print(f"[{word['start']:.2f} - {word['end']:.2f}] {word['text']}")

    # Print full text segment if available
    if text:
        # print("\nFull text segment:")
        print(f"[{text['start']:.2f} - {text['end']:.2f}]")
        print(text["text"])


def main():
    """
    Main entry point for transcription script.

    Handles:
    - Command line argument parsing
    - File path management
    - Transcription process orchestration
    - Output file generation
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Transcribe audio files using Whisper API with word-level timestamps"
    )
    parser.add_argument("files", nargs="+", help="Audio files to transcribe")
    parser.add_argument(
        "--force", action="store_true", help="Overwrite existing transcription files"
    )
    args = parser.parse_args()

    for audio_path in args.files:
        # Create output file with same path prefix but new suffix
        base_path = Path(audio_path).with_suffix("")
        output_file = base_path.with_suffix(".transcription.jsonl")
        output_text = base_path.with_suffix(".transcription.txt")
        audio_path = base_path.with_suffix(".mp3")

        dump(audio_path)

        if not Path(audio_path).exists():
            print(f"Error: File {audio_path} not found")
            continue

        if output_file.exists() and not args.force:
            print(f"Skipping {audio_path} - transcription files already exist")
            print("Use --force to overwrite existing files")
            continue

        # Create output file paths once
        input_path = Path(audio_path)
        transcribe_large_audio(audio_path, output_file)

        # Create text file with wrapped text
        with open(output_text, "w") as txt_file:
            with jsonlines.open(output_file) as reader:
                for obj in reader:
                    if obj.get("text"):
                        # Wrap text at 80 columns
                        import textwrap

                        wrapped_text = textwrap.fill(obj["text"], width=80)
                        txt_file.write(wrapped_text + "\n\n")

        print(f"Transcription saved to {output_file} and {output_text}")


if __name__ == "__main__":
    main()

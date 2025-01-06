#!/usr/bin/env python3

import os
import sys
import json
import jsonlines
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from dump import dump
from pydub import AudioSegment
import lox

# Load environment variables from .env file
load_dotenv()

@lox.thread(10)
def transcribe_audio(audio_path):
    """
    Transcribe audio file using OpenAI Whisper API with word-level timestamps
    Returns list of words with timestamps
    """
    # Get API key from environment variable
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")

    client = OpenAI(api_key=api_key)

    # Open audio file
    with open(audio_path, "rb") as audio_file:
        # Call OpenAI API
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json",
            timestamp_granularities=["word"]
        )

    # Extract words and full text with timestamps
    words = []
    for word in response.words:
        words.append({
            "word": word.word,
            "start": round(word.start, 6),
            "end": round(word.end, 6)
        })

    # Add the full text with timestamps
    text_segment = {
        "text": response.text,
        "start": round(response.words[0].start, 6) if response.words else 0,
        "end": round(response.words[-1].end, 6) if response.words else response.duration
    }

    return words, text_segment

def transcribe_large_audio(audio_path, output_file):
    """
    Handle large audio files by processing chunks sequentially,
    using word timestamps to determine clean cut points.
    Includes overlap between chunks to ensure no words are lost.
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
        current_position_ms += chunk_duration_ms - 10*1000

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
            print(f"Extracting chunk from {current_position_ms/1000:.2f}s to {chunk_end/1000:.2f}s")
            chunk = audio[current_position_ms:chunk_end]

            # Save chunk to unique temp file
            temp_path = os.path.join(temp_dir, f"chunk_{current_position_ms}.mp3")
            dump(temp_path)
            print(f"Exporting chunk to {temp_path}...")
            chunk.export(temp_path, format="mp3")
            chunk_size_mb = os.path.getsize(temp_path) / (1024 * 1024)
            print(f"Chunk size: {chunk_size_mb:.1f}MB")

            # Transcribe chunk
            print("Sending chunk to OpenAI API for transcription...")
            transcribe_audio.scatter(temp_path)

        results = transcribe_audio.gather(tqdm=True)

    with jsonlines.open(output_file, mode='w', flush=True) as writer:
        for current_position_ms,(chunk_words, chunk_text) in zip(chunk_positions, results):
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
    """Print words and text segments with their timestamps"""
    words, text = words_and_text if isinstance(words_and_text, tuple) else (words_and_text, None)

    # Print word-level timestamps
    #for word in words:
    #    print(f"[{word['start']:.2f} - {word['end']:.2f}] {word['text']}")

    # Print full text segment if available
    if text:
        #print("\nFull text segment:")
        print(f"[{text['start']:.2f} - {text['end']:.2f}]")
        print(text['text'])

def main():
    if len(sys.argv) < 2:
        print("Usage: python transcribe.py <audio_file1.mp3> [file2.mp3 ...]")
        sys.exit(1)

    for audio_path in sys.argv[1:]:
        if not Path(audio_path).exists():
            print(f"Error: File {audio_path} not found")
            continue

        # Check if transcription files already exist
        output_file = Path(audio_path).with_suffix(".transcription.jsonl")
        output_text = Path(audio_path).with_suffix(".transcription.txt")
        dump(output_file)
        dump(output_text)

        if Path(output_file).exists() or Path(output_text).exists():
            print(f"Skipping {audio_path} - transcription files already exist")
            continue

        # Create output file paths once
        input_path = Path(audio_path)
        transcribe_large_audio(audio_path, output_file)

        # Create text file with wrapped text
        with open(output_text, 'w') as txt_file:
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

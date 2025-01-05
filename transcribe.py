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

# Load environment variables from .env file
load_dotenv()

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

    dump(response)

    # Extract words and full text with timestamps
    words = []
    for word in response.words:
        words.append({
            "text": word.word,
            "start": round(word.start, 2),
            "end": round(word.end, 2)
        })

    # Add the full text with timestamps
    text_segment = {
        "type": "text",
        "text": response.text,
        "start": round(response.words[0].start, 2) if response.words else 0,
        "end": round(response.words[-1].end, 2) if response.words else response.duration
    }

    return words, text_segment

def transcribe_large_audio(audio_path):
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
    chunk_duration_ms = 1 * 60 * 1000  # 10 minutes in milliseconds

    current_position_ms = 0
    all_words = []

    while current_position_ms < total_duration_ms:
        dump(current_position_ms)

        # Extract chunk with overlap
        chunk_end = min(current_position_ms + chunk_duration_ms, total_duration_ms)
        print(f"Extracting chunk from {current_position_ms/1000:.2f}s to {chunk_end/1000:.2f}s")
        chunk = audio[current_position_ms:chunk_end]

        # Save chunk temporarily
        temp_path = "temp_chunk.mp3"
        print("Exporting chunk to temporary file...")
        chunk.export(temp_path, format="mp3")
        chunk_size_mb = os.path.getsize(temp_path) / (1024 * 1024)
        print(f"Chunk size: {chunk_size_mb:.1f}MB")

        # Transcribe chunk
        print("Sending chunk to OpenAI API for transcription...")
        chunk_words, chunk_text = transcribe_audio(temp_path)
        print_words((chunk_words, chunk_text))

        # Clean up temporary file
        os.remove(temp_path)

        if not chunk_words:
            break

        # Adjust timestamps with offset
        for word in chunk_words:
            word["start"] += current_position_ms / 1000  # Convert ms to seconds
            word["end"] += current_position_ms / 1000
        
        # Adjust text segment timestamps
        chunk_text["start"] += current_position_ms / 1000
        chunk_text["end"] += current_position_ms / 1000

        # Find a good cutting point for next chunk
        if len(chunk_words) > OVERLAP_WORDS:
            # Keep OVERLAP_WORDS at the end for next chunk alignment
            current_position_ms = int(chunk_words[-OVERLAP_WORDS]["start"] * 1000)
        else:
            current_position_ms += chunk_duration_ms - 10*1000

        # Write this chunk's words and text to the output file
        output_file = Path(audio_path).stem + "_transcription.jsonl"
        with jsonlines.open(output_file, mode='a') as writer:
            for word in chunk_words:
                writer.write(word)
            writer.write(chunk_text)

        print(f"Processed up to {current_position_ms/1000:.2f} seconds")

    # Return the output file path
    return output_file

def print_words(words_and_text):
    """Print words and text segments with their timestamps"""
    words, text = words_and_text if isinstance(words_and_text, tuple) else (words_and_text, None)

    # Print word-level timestamps
    for word in words:
        print(f"[{word['start']:.2f} - {word['end']:.2f}] {word['text']}")

    # Print full text segment if available
    if text:
        print("\nFull text segment:")
        print(f"[{text['start']:.2f} - {text['end']:.2f}]")
        print(text['text'])

def main():
    if len(sys.argv) != 2:
        print("Usage: python transcribe.py <audio_file.mp3>")
        sys.exit(1)

    audio_path = sys.argv[1]
    if not Path(audio_path).exists():
        print(f"Error: File {audio_path} not found")
        sys.exit(1)

    # Get file size in MB
    file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)

    # Clear any existing output file
    output_file = Path(audio_path).stem + "_transcription.jsonl"
    Path(output_file).unlink(missing_ok=True)

    # Choose transcription method based on file size
    if file_size_mb > 5:
        print(f"File size is {file_size_mb:.1f}MB. Processing in chunks...")
        output_file = transcribe_large_audio(audio_path)
    else:
        words, text_segment = transcribe_audio(audio_path)
        # Write single chunk to JSONL
        with jsonlines.open(output_file, mode='w') as writer:
            for word in words:
                writer.write(word)
            writer.write(text_segment)

    print(f"Transcription saved to {output_file}")

    # Print final output
    with jsonlines.open(output_file) as reader:
        for word in reader:
            print(f"[{word['start']:.2f} - {word['end']:.2f}] {word['text']}")


if __name__ == "__main__":
    main()

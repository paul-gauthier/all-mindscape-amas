#!/usr/bin/env python3

import os
import sys
import json
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

    # Extract words with timestamps from response
    words = []
    for word in response.words:
        words.append({
            "text": word.word,
            "start": round(word.start, 2),
            "end": round(word.end, 2)
        })

    return words

def transcribe_large_audio(audio_path):
    """
    Handle large audio files by processing chunks sequentially,
    using word timestamps to determine clean cut points.
    Includes overlap between chunks to ensure no words are lost.
    """
    # Number of words to overlap between chunks
    OVERLAP_WORDS = 10
    SPLICE_WORDS = 3

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
        chunk_words = transcribe_audio(temp_path)
        print_words(chunk_words)

        # Clean up temporary file
        os.remove(temp_path)

        if not chunk_words:
            break

        # Adjust timestamps with offset
        for word in chunk_words:
            word["start"] += current_position_ms / 1000  # Convert ms to seconds
            word["end"] += current_position_ms / 1000

        # Handle overlap with previous chunk
        if all_words:
            overlap_start = 0
            best_overlap = 0
            best_offset = 0

            # Try to align the overlapping words
            for i in range(SPLICE_WORDS):
                matches = sum(1 for j in range(min(SPLICE_WORDS - i, len(chunk_words)))
                            if chunk_words[j]["text"].lower() ==
                               all_words[-SPLICE_WORDS + i + j]["text"].lower())
                if matches > best_overlap:
                    best_overlap = matches
                    best_offset = i

            # Only trim if we found a good match
            if best_overlap >= 1:  # Require at least 1 matching word
                trim_point = best_offset
                chunk_words = chunk_words[trim_point:]
                print(f"\nTrimmed {trim_point} overlapping words")
            else:
                print("\nWARNING: Could not find good word alignment")

            # Print debug info about word alignment
            print("\nWord alignment details:")
            print("Last words from previous chunk:")
            for word in all_words[-OVERLAP_WORDS:]:
                print(f"  {word['text']}")
            print("\nFirst words of current chunk:")
            for word in chunk_words[:OVERLAP_WORDS]:
                print(f"  {word['text']}")

        # Find a good cutting point for next chunk
        if len(chunk_words) > OVERLAP_WORDS:
            # Keep OVERLAP_WORDS at the end for next chunk alignment
            current_position_ms = int(chunk_words[-OVERLAP_WORDS]["start"] * 1000)
        else:
            current_position_ms += chunk_duration_ms

        # Add words to the final list, keeping some overlap for next chunk
        if len(chunk_words) > SPLICE_WORDS:
            all_words.extend(chunk_words[:-SPLICE_WORDS])
        else:
            all_words.extend(chunk_words)

        print(f"Processed up to {current_position_ms/1000:.2f} seconds")

    return all_words

def print_words(words):
    """Print words with their timestamps"""
    for word in words:
        print(f"[{word['start']:.2f} - {word['end']:.2f}] {word['text']}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python transcribe.py <audio_file.mp3>")
        sys.exit(1)

    audio_path = sys.argv[1]
    if not Path(audio_path).exists():
        print(f"Error: File {audio_path} not found")
        sys.exit(1)

    try:
        # Get file size in MB
        file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)

        # Choose transcription method based on file size
        if file_size_mb > 5:
            print(f"File size is {file_size_mb:.1f}MB. Processing in chunks...")
            transcription = transcribe_large_audio(audio_path)
        else:
            transcription = transcribe_audio(audio_path)

        # Save to JSON file
        output_file = Path(audio_path).stem + "_transcription.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(transcription, f, indent=2, ensure_ascii=False)

        print(f"Transcription saved to {output_file}")
        print_words(transcription)

    except Exception as e:
        print(f"Error during transcription: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()

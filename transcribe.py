#!/usr/bin/env python3

import os
import sys
import json
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def transcribe_audio(audio_path):
    """
    Transcribe audio file using OpenAI Whisper API with word-level timestamps
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
    for segment in response.segments:
        for word in segment.words:
            words.append({
                "text": word.text,
                "start": round(word.start, 2),
                "end": round(word.end, 2)
            })
    
    return words

def main():
    if len(sys.argv) != 2:
        print("Usage: python transcribe.py <audio_file.mp3>")
        sys.exit(1)
        
    audio_path = sys.argv[1]
    if not Path(audio_path).exists():
        print(f"Error: File {audio_path} not found")
        sys.exit(1)
        
    try:
        # Perform transcription
        transcription = transcribe_audio(audio_path)
        
        # Save to JSON file
        output_file = Path(audio_path).stem + "_transcription.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(transcription, f, indent=2, ensure_ascii=False)
            
        print(f"Transcription saved to {output_file}")
        
        # Print formatted output to console
        for word in transcription:
            print(f"[{word['start']:.2f} - {word['end']:.2f}] {word['text']}")
            
    except Exception as e:
        print(f"Error during transcription: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()

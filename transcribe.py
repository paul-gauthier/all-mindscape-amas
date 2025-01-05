#!/usr/bin/env python3

import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"  # Force CPU usage

import whisper
import sys
import json
from pathlib import Path

def transcribe_audio(audio_path):
    """
    Transcribe audio file using Whisper model with word-level timestamps
    """
    # Load the Whisper model
    model = whisper.load_model("base")
    
    # Transcribe with word timestamps
    result = model.transcribe(
        audio_path,
        language="en",
        word_timestamps=True
    )
    
    # Extract words with timestamps
    words = []
    for segment in result["segments"]:
        for word in segment["words"]:
            words.append({
                "text": word["text"],
                "start": round(word["start"], 2),
                "end": round(word["end"], 2)
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

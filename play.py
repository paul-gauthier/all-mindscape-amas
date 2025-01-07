#!/usr/bin/env python3

import requests
import pygame
import io
import sys
import time

def stream_and_play(url):
    # Initialize pygame mixer
    pygame.mixer.init()
    
    # Stream the content in chunks
    response = requests.get(url, stream=True)
    
    # Create a byte buffer to hold the audio data
    buffer = io.BytesIO()
    
    # Download enough data to start playing
    chunk_size = 8192
    for i, chunk in enumerate(response.iter_content(chunk_size=chunk_size)):
        buffer.write(chunk)
        
        # After getting enough initial data, start playing
        if i == 10:  # Adjust this number based on needed buffer size
            buffer.seek(0)
            pygame.mixer.music.load(buffer)
            pygame.mixer.music.play()
        
        # Keep downloading while playing
        if i > 10:
            time.sleep(0.1)  # Prevent downloading too fast
    
    # Wait for playback to finish
    while pygame.mixer.music.get_busy():
        time.sleep(1)

def main():
    if len(sys.argv) != 2:
        print("Usage: ./play.py <mp3_url>")
        sys.exit(1)
        
    url = sys.argv[1]
    print(f"Streaming and playing: {url}")
    stream_and_play(url)

if __name__ == "__main__":
    main()

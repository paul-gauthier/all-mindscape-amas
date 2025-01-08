#!/usr/bin/env python3

import requests
import pygame
import sys
import time
import tempfile
import os

def stream_and_play(url):
    # Initialize pygame mixer
    pygame.mixer.init()
    
    # Create a temporary file
    temp_fd, temp_path = tempfile.mkstemp(suffix='.mp3')
    
    try:
        # Stream the content in chunks
        response = requests.get(url, stream=True)
        
        # Print request headers
        print("Request headers sent:")
        for header, value in response.request.headers.items():
            print(f"{header}: {value}")
            
        # Print redirect information
        if response.history:
            print("\nRedirects occurred:")
            for r in response.history:
                print(f"  {r.status_code}: {r.url}")
            print(f"\nFinal URL: {response.url}")
        else:
            print("\nNo redirects occurred")
        
        # Download enough data to start playing
        chunk_size = 32768  # Larger chunk size
        with os.fdopen(temp_fd, 'wb') as temp_file:
            for i, chunk in enumerate(response.iter_content(chunk_size=chunk_size)):
                temp_file.write(chunk)
                temp_file.flush()
                
                # After getting enough initial data, start playing
                if i == 10:
                    pygame.mixer.music.load(temp_path)
                    pygame.mixer.music.play()
                
                # Keep downloading while playing
                if i > 10:
                    time.sleep(0.1)
        
        # Wait for playback to finish
        while pygame.mixer.music.get_busy():
            time.sleep(1)
            
    finally:
        # Clean up temp file
        pygame.mixer.music.stop()
        if os.path.exists(temp_path):
            os.remove(temp_path)

def main():
    if len(sys.argv) != 2:
        print("Usage: ./play.py <mp3_url>")
        sys.exit(1)
        
    url = sys.argv[1]
    print(f"Streaming and playing: {url}")
    stream_and_play(url)

if __name__ == "__main__":
    main()

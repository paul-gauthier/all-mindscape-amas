#!/usr/bin/env python3
"""Print XING seek table from MP3 files."""

import sys
import eyed3
from mutagen.mp3 import MP3

def print_seek_table(filename):
    """Print the XING seek table for a given MP3 file."""
    try:
        # Try mutagen first
        audio = MP3(filename)
        info = audio.info
        print(f"\nFile: {filename}")
        
        xing_found = False
        
        # Try different ways to access Xing header info via mutagen
        xing_header = getattr(info, 'xing_header', None)
        if not xing_header:
            xing_header = getattr(info, 'xing', None)
            
        if xing_header and isinstance(xing_header, dict) and 'TOC' in xing_header:
            xing_found = True
            print("\nXING header found (via mutagen):")
            toc = xing_header['TOC']
            print("\nSeek table entries (position%, byte offset):")
            for i, offset in enumerate(toc):
                percentage = i * 100 // (len(toc) - 1)
                print(f"{percentage:3d}%: {offset}")
        
        # Try eyed3 approach
        audiofile = eyed3.load(filename)
        if audiofile and audiofile.tag and audiofile.tag.xing_header:
            xing_found = True
            xing = audiofile.tag.xing_header
            print("\nXING header details (via eyed3):")
            print(f"Frames: {xing.frames}")
            print(f"Bytes: {xing.bytes}")
            print(f"Quality: {xing.quality}")
            if hasattr(xing, 'bitrate'):
                print(f"Bitrate: {xing.bitrate}")
        
        if not xing_found:
            print("No XING header found")
            
    except Exception as e:
        print(f"Error processing {filename}: {e}", file=sys.stderr)

def main():
    if len(sys.argv) < 2:
        print("Usage: seek.py <mp3file> [mp3file2 ...]", file=sys.stderr)
        sys.exit(1)
        
    for filename in sys.argv[1:]:
        print_seek_table(filename)

if __name__ == '__main__':
    main()

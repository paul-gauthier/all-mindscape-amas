#!/usr/bin/env python3
"""Print XING seek table from MP3 files."""

import sys
import eyed3
from mutagen.mp3 import MP3

def print_seek_table(filename):
    """Print the XING seek table for a given MP3 file."""
    xing_found = False

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

def main():
    if len(sys.argv) < 2:
        print("Usage: seek.py <mp3file> [mp3file2 ...]", file=sys.stderr)
        sys.exit(1)

    for filename in sys.argv[1:]:
        print_seek_table(filename)

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Print XING seek table from MP3 files."""

import sys
from mutagen.mp3 import MP3

def print_seek_table(filename):
    """Print the XING seek table for a given MP3 file."""
    try:
        audio = MP3(filename)
        info = audio.info
        
        print(f"\nFile: {filename}")
        # Try different ways to access Xing header info
        xing_header = getattr(info, 'xing_header', None)
        if not xing_header:
            xing_header = getattr(info, 'xing', None)
            
        if xing_header and isinstance(xing_header, dict) and 'TOC' in xing_header:
            print("XING header found")
            toc = xing_header['TOC']
            print("\nSeek table entries (position%, byte offset):")
            for i, offset in enumerate(toc):
                percentage = i * 100 // (len(toc) - 1)
                print(f"{percentage:3d}%: {offset}")
        else:
            print("No XING seek table found")
            
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

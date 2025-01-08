#!/usr/bin/env python3

from pathlib import Path
import sys
import json
from mutagen.mp3 import MP3
from dump import dump


def format_time(seconds):
    minutes = int(seconds // 60)
    remaining_seconds = seconds % 60
    return f"{minutes:02d}:{remaining_seconds:05.2f}"


def main():
    orig_file = Path(sys.argv[1]).read_bytes()
    new_file = Path(sys.argv[2]).read_bytes()

    orig_len = len(orig_file)
    new_len = len(new_file)
    diff_len = new_len - orig_len

    print(f"Original length: {orig_len:,}")
    print(f"New length: {new_len:,}")
    print(f"Difference: {diff_len:,}")
    print()

    orig_audio = MP3(sys.argv[1])
    new_audio = MP3(sys.argv[2])
    print(f"Original duration: {format_time(orig_audio.info.length)}")
    print(f"New duration: {format_time(new_audio.info.length)}")
    print(f"Duration difference: {format_time(new_audio.info.length - orig_audio.info.length)}")
    print()

    orig_bytes_per_sec = orig_len / orig_audio.info.length
    new_bytes_per_sec = new_len / new_audio.info.length
    print(f"Original bytes/sec: {orig_bytes_per_sec:.2f}")
    print(f"New bytes/sec: {new_bytes_per_sec:.2f}")
    print(f"Bytes/sec difference: {(new_bytes_per_sec - orig_bytes_per_sec):.2f}")

    print()

    if len(sys.argv) != 4:
        print("Usage: seek.py ORIG_FILE NEW_FILE SEGMENTS_FILE")
        sys.exit(1)

    num_bytes = 128
    segments_file = sys.argv[3]

    # Read and process each segment
    with open(segments_file) as f:
        for line in f:
            segment = json.loads(line)
            start_sec = segment['start']
            
            # Calculate byte offset in original file
            orig_offset = int(start_sec * orig_bytes_per_sec)
            target_bytes = orig_file[orig_offset:orig_offset + num_bytes]

            # Search for these bytes in new file
            pos = 0
            print(f"\nMapping segment at {format_time(start_sec)}:")
            found = False
            while True:
                pos = new_file.find(target_bytes, pos)
                if pos == -1:
                    break
                # Convert position back to seconds
                found_sec = pos / new_bytes_per_sec
                print(f"  Found at {format_time(found_sec)} (offset {pos:,})")
                found = True
                pos += 1
            
            if not found:
                print("  No matches found")

if __name__ == '__main__':
    main()

#!/usr/bin/env python3

"""
fingerprint.py - Audio Segment Fingerprinting Tool

This script adds audio fingerprints to segment data by:
1. Reading segment timestamps from JSONL file
2. Calculating byte offsets in the corresponding MP3 file
3. Extracting 128-byte fingerprints at each segment start
4. Adding base64-encoded fingerprints to each segment record
5. Writing updated records to a new fingerprints.jsonl file
"""

import argparse
import base64
import json
from pathlib import Path

from mutagen.mp3 import MP3


def get_fingerprint(mp3_bytes, offset, length=128):
    """
    Extract a fingerprint from MP3 bytes at given offset.

    Args:
        mp3_bytes (bytes): The MP3 file content
        offset (int): Byte position to start fingerprint
        length (int): Number of bytes for fingerprint

    Returns:
        str: Base64-encoded fingerprint
    """
    fingerprint = mp3_bytes[offset : offset + length]
    return base64.b64encode(fingerprint).decode("utf-8")


def main():
    """
    Main entry point for the fingerprinting tool.
    """
    parser = argparse.ArgumentParser(
        description="Add audio fingerprints to segment data"
    )
    parser.add_argument("files", nargs="+", help="Files to process")
    args = parser.parse_args()

    for fname in args.files:
        print(f"\nProcessing {fname}...")
        process(fname)


def process(fname):
    """
    Process a single file to add fingerprints to its segments.

    Args:
        fname (str): Path to the file to process
    """
    base_path = Path(fname).with_suffix("")
    mp3_file = base_path.with_suffix(".mp3")
    segments_file = base_path.with_suffix(".summarized.jsonl")
    fingerprints_file = base_path.with_suffix(".fingerprints.jsonl")

    # Read the MP3 file
    mp3_bytes = Path(mp3_file).read_bytes()

    # Calculate bytes per second from MP3 duration
    total_bytes = len(mp3_bytes)
    audio = MP3(mp3_file)
    bytes_per_sec = total_bytes / audio.info.length

    # Load existing timestamps if file exists
    timestamps_file = base_path.with_suffix(".timestamps.json")
    timestamps = {}
    if timestamps_file.exists():
        with open(timestamps_file) as f:
            timestamps = json.load(f)

    # Process each segment
    with open(segments_file) as infile, open(fingerprints_file, "w") as outfile:
        for line in infile:
            segment = json.loads(line)
            start_sec = segment["start"]

            # Calculate byte offset
            offset = int(start_sec * bytes_per_sec)

            # Get fingerprint and add to segment
            fingerprint = get_fingerprint(mp3_bytes, offset)
            segment["fingerprint"] = fingerprint

            # Write updated segment
            outfile.write(json.dumps(segment) + "\n")

            # Add to timestamps dict
            key = f"{total_bytes},{fingerprint}"
            timestamps[key] = start_sec

    # Save updated timestamps
    with open(timestamps_file, "w") as f:
        json.dump(timestamps, f, indent=2)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3

import json
import shutil
import sys
import time
import re
import argparse
from io import BytesIO
from pathlib import Path

import requests
from mutagen.mp3 import MP3

from dump import dump


def get_file_size(url):
    # Try HEAD request first
    response = requests.head(url)
    if "Content-Length" in response.headers:
        return int(response.headers["Content-Length"])

    # If no Content-Length, try GET with range header
    response = requests.get(url, headers={"Range": "bytes=0-0"})
    if "Content-Range" in response.headers:
        content_range = response.headers["Content-Range"]
        return int(content_range.split("/")[-1])

    # If all else fails, we'll have to download the whole file
    response = requests.get(url)
    return len(response.content)


def get_byte_range(url, start, length):
    dump(start, length)
    headers = {"Range": f"bytes={start}-{start+length-1}"}
    response = requests.get(url, headers=headers)
    return response.content


def get_duration(url, bytes_per_sec):
    # Calculate duration using bytes per second from original file
    total_size = get_file_size(url)
    duration = total_size / bytes_per_sec
    return duration


def format_time(seconds):
    minutes = int(seconds // 60)
    remaining_seconds = seconds % 60
    return f"{minutes:02d}:{remaining_seconds:05.2f}"


def check_validation_timestamp(url):
    """Extract and check the validation timestamp from URL"""
    match = re.search(r'validation=(\d+)', url)
    if not match:
        return True  # No timestamp found, proceed

    timestamp = int(match.group(1))
    current_time = int(time.time())

    dump(url)
    dump(timestamp)
    dump(current_time)

    hours_remaining = (timestamp - current_time) / 3600.
    if hours_remaining > 0:
        print(f"Validation expires in {hours_remaining:.1f} hours")

    return current_time > timestamp

def main():
    parser = argparse.ArgumentParser(description='Sync audio segments with updated MP3 files')
    parser.add_argument('files', nargs='+', help='Files to process')
    parser.add_argument('--force', action='store_true', help='Force processing even if validation timestamp is in the future')
    args = parser.parse_args()

    for fname in args.files:
        print(f"\nProcessing {fname}...")
        process(fname, args.force)


def process(fname, force=False):
    base_path = Path(fname).with_suffix("")
    mp3_file = base_path.with_suffix(".mp3")
    metadata_file = base_path.with_suffix(".json")
    segments_file = base_path.with_suffix(".summarized.jsonl")
    synced_file = base_path.with_suffix(".synced.jsonl")

    # Read metadata file to get URL
    with open(metadata_file) as f:
        metadata = json.load(f)

    url = metadata["url"]

    # Follow redirects to get final URL using a small range request
    response = requests.get(url, headers={"Range": "bytes=0-1"}, allow_redirects=True)
    final_url = response.url
    metadata["final_url"] = final_url

    dump(final_url)

    # Check validation timestamp unless forced
    if not force and not check_validation_timestamp(final_url):
        print("Validation timestamp is in the future. Skipping processing.")
        print("Use --force to process anyway.")
        return

    # Save updated metadata with final URL
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2)

    url = final_url  # Use final URL for subsequent operations
    orig_file = Path(mp3_file).read_bytes()

    # Get new file metadata without downloading whole file
    new_len = get_file_size(url)
    orig_len = len(orig_file)
    diff_len = new_len - orig_len

    print(f"Original length: {orig_len:,}")
    print(f"New length: {new_len:,}")
    print(f"Difference: {diff_len:,}")
    print()

    # If files are identical, just copy segments to synced
    if diff_len == 0:
        print("New mp3 is identical, no sync needed.")
        shutil.copy2(segments_file, synced_file)
        return

    print(f"New length: {new_len:,}")
    print(f"Difference: {diff_len:,}")
    print()

    orig_audio = MP3(mp3_file)
    orig_bytes_per_sec = orig_len / orig_audio.info.length
    print(f"Original bytes/sec: {orig_bytes_per_sec:.2f}")

    new_duration = get_duration(url, orig_bytes_per_sec)
    print(f"Original duration: {format_time(orig_audio.info.length)}")
    print(f"New duration: {format_time(new_duration)}")
    print(f"Duration difference: {format_time(new_duration - orig_audio.info.length)}")
    print()

    print()

    num_bytes = 128

    # Read and process each segment
    last_match_pos = 0
    prev_duration = 0  # Track duration of previous segment

    # Process segments and write synced version with updated timestamps
    with open(segments_file) as f, open(synced_file, "w") as out_f:
        for line in f:
            segment = json.loads(line)
            start_sec = segment["start"]

            # Calculate byte offset in original file
            orig_offset = int(start_sec * orig_bytes_per_sec)
            target_bytes = orig_file[orig_offset : orig_offset + num_bytes]

            # Search for these bytes in new file starting after previous match
            # Calculate search start position based on previous segment duration
            search_start = last_match_pos
            if prev_duration > 0:
                # Start searching a bit before where we expect the segment to be
                expected_pos = last_match_pos + int(
                    (prev_duration - 5) * orig_bytes_per_sec
                )
                search_start = max(last_match_pos, expected_pos)

            pos = search_start

            found = False
            # Search in chunks to avoid downloading entire file
            found = False
            pos = search_start

            chunk_size = 128 * 1024  # Size of chunks to download and search
            while pos < new_len and not found:
                chunk = get_byte_range(url, pos, chunk_size)
                chunk_pos = chunk.find(target_bytes)

                if chunk_pos != -1:
                    actual_pos = pos + chunk_pos
                    found_sec = actual_pos / orig_bytes_per_sec
                    time_delta = found_sec - start_sec
                    print(
                        f"Segment at {format_time(start_sec)} found at {format_time(found_sec)} (offset {actual_pos:,}, delta {format_time(abs(time_delta))})"
                    )
                    found = True
                    last_match_pos = actual_pos + 1

                    # Update segment timestamps and write to synced file
                    duration = segment["end"] - segment["start"]
                    segment["start"] = found_sec
                    segment["end"] = found_sec + duration
                    json.dump(segment, out_f)
                    out_f.write("\n")

                    prev_duration = duration
                else:
                    # Move to next chunk, overlapping slightly to avoid missing matches
                    pos += chunk_size - num_bytes
                    chunk_size = min(chunk_size * 2, 1024 * 1024)

            if not found:
                print(f"Segment at {format_time(start_sec)} not found.")
                # Write original segment timing if match not found
                json.dump(segment, out_f)
                out_f.write("\n")


if __name__ == "__main__":
    main()

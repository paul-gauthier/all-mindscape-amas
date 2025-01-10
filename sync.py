#!/usr/bin/env python3

"""
sync.py - Audio Segment Synchronization Tool

This script synchronizes audio segment timestamps with updated MP3 files by:
1. Comparing original and new MP3 files from a URL
2. Calculating byte offsets and durations
3. Adjusting segment timestamps to match the new audio file
4. Creating a synchronized version of the segment data

The tool is particularly useful when the source audio file is updated but the
content structure remains similar, allowing for automatic realignment of
previously identified segments.
"""

import argparse
import json
import re
import shutil
import sys
import time
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path

import requests
from mutagen.mp3 import MP3

from dump import dump  # Debugging utility for printing values
from fingerprint import get_fingerprint


def get_file_size(url):
    """
    Get the size of a remote file in bytes using efficient HTTP requests.

    Args:
        url (str): The URL of the file to measure

    Returns:
        int: File size in bytes

    The method tries three approaches in order of efficiency:
    1. HEAD request for Content-Length header
    2. Range request for Content-Range header
    3. Full download as last resort
    """
    # Try HEAD request first (most efficient)
    response = requests.head(url)
    if "Content-Length" in response.headers:
        return int(response.headers["Content-Length"])

    # If no Content-Length, try GET with range header
    response = requests.get(url, headers={"Range": "bytes=0-0"})
    if "Content-Range" in response.headers:
        content_range = response.headers["Content-Range"]
        return int(content_range.split("/")[-1])

    # If all else fails, download the whole file (least efficient)
    response = requests.get(url)
    return len(response.content)


def get_byte_range(url, start, length):
    """
    Fetch a specific byte range from a remote file.

    Args:
        url (str): The URL of the file
        start (int): Starting byte position
        length (int): Number of bytes to fetch

    Returns:
        bytes: The requested byte range content
    """
    dump(start, length)  # Debugging output
    headers = {"Range": f"bytes={start}-{start+length-1}"}
    response = requests.get(url, headers=headers)
    return response.content


def get_duration(url, bytes_per_sec):
    """
    Calculate audio duration based on file size and encoding rate.

    Args:
        url (str): URL of the audio file
        bytes_per_sec (float): Encoding rate in bytes per second

    Returns:
        float: Calculated duration in seconds
    """
    total_size = get_file_size(url)
    duration = total_size / bytes_per_sec
    return duration


def get_validated_url(url):
    """
    Get a validated URL with a future timestamp.

    Args:
        url (str): The URL to validate

    Returns:
        str: Validated URL with timestamp at least 12 hours in the future

    Keeps trying until it gets a URL with a validation timestamp at least
    12 hours in the future, or falls back to the original URL if no timestamp
    is found.
    """
    while True:
        response = requests.get(
            url, headers={"Range": "bytes=0-1024"}, allow_redirects=True
        )
        final_url = response.url

        # Check validation timestamp
        match = re.search(r"validation=(\d+)", final_url)
        if match:
            timestamp = int(match.group(1))
            validation_time = datetime.fromtimestamp(timestamp)
            dump(validation_time)
            now = datetime.now()

            # If validation is more than 12 hours in the future, we're good
            if validation_time > now + timedelta(hours=12):
                return final_url

            # Otherwise wait a bit and try again
            time.sleep(5)
        else:
            # If no validation timestamp, just use this URL
            return final_url


def get_date_from_url(url):
    """
    Extract and format validation timestamp from URL if present.

    Args:
        url (str): URL to check for validation timestamp

    Returns:
        str: Formatted timestamp or "None" if not found
    """
    match = re.search(r"validation=(\d+)", url)
    if match:
        timestamp = int(match.group(1))
        from datetime import datetime

        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return "None"


def format_time(seconds):
    """
    Format a duration in seconds into a human-readable MM:SS.ss string.

    Args:
        seconds (float): Duration in seconds

    Returns:
        str: Formatted time string (MM:SS.ss)
    """
    minutes = int(seconds // 60)
    remaining_seconds = seconds % 60
    return f"{minutes:02d}:{remaining_seconds:05.2f}"


def check_valid(url):
    """
    Validate that a URL is accessible and supports range requests.

    Args:
        url (str): URL to validate

    Returns:
        bool: True if URL is valid and supports range requests
    """
    try:
        # Test with a small range request
        response = requests.get(url, headers={"Range": "bytes=0-0"})
        # Accept either partial content (206) or full content (200)
        if response.status_code != 206 and response.status_code != 200:
            print("Existing URL:", url)
            print(f"Validation timestamp: {get_date_from_url(url)}")
            print(f"URL validation failed with status code: {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"URL validation failed: {e}")
        return False

    return True


def main():
    """
    Main entry point for the synchronization tool.

    Processes one or more files, synchronizing their audio segments with updated
    MP3 versions from their source URLs.
    """
    parser = argparse.ArgumentParser(
        description="Sync audio segments with updated MP3 files"
    )
    parser.add_argument("files", nargs="+", help="Files to process")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force processing even if validation timestamp is in the future",
    )
    args = parser.parse_args()

    for fname in args.files:
        print(f"\nProcessing {fname}...")
        process(fname, args.force)


def process(fname, force=False):
    """
    Process a single file to synchronize its segments with updated audio.

    Args:
        fname (str): Path to the file to process
        force (bool): If True, process even if URL appears valid

    The processing workflow:
    1. Load metadata and check URL validity
    2. Compare original and new file sizes
    3. Check if we have cached timestamps for all fingerprints
    4. If cached timestamps exist, use them
    5. Otherwise, synchronize each segment by finding matching byte patterns
    6. Write updated segment data to synced output file
    """
    base_path = Path(fname).with_suffix("")
    mp3_file = base_path.with_suffix(".mp3")
    metadata_file = base_path.with_suffix(".json")
    segments_file = base_path.with_suffix(".fingerprints.jsonl")
    synced_file = base_path.with_suffix(".synced.jsonl")
    timestamps_file = base_path.with_suffix(".timestamps.json")

    # Read metadata file to get URL
    with open(metadata_file) as f:
        metadata = json.load(f)

    existing_final_url = metadata["final_url"]

    # Check validation timestamp unless forced
    if not force and check_valid(existing_final_url):
        print("Final URL is valid, skipping processing.")
        print(f"Validation timestamp: {get_date_from_url(existing_final_url)}")
        print("Use --force to process anyway.")
        return

    url = metadata["url"]

    # Get validated URL with future timestamp
    final_url = get_validated_url(url)
    metadata["final_url"] = final_url

    print(f"New URL date: {get_date_from_url(final_url)}")

    url = final_url  # Use final URL for subsequent operations

    # Get new file metadata without downloading whole file
    new_len = get_file_size(url)
    orig_len = metadata["file_size"]
    diff_len = new_len - orig_len

    print(f"Original length: {orig_len:,}")
    print(f"New length: {new_len:,}")
    print(f"Difference: {diff_len:,}")
    print()

    # Load timestamps if file exists
    timestamps = {}
    if timestamps_file.exists():
        with open(timestamps_file) as f:
            timestamps = json.load(f)

    # Check if we have cached timestamps for all fingerprints
    all_fingerprints_cached = True
    with open(segments_file) as f:
        for line in f:
            segment = json.loads(line)
            key = f"{new_len},{segment['fingerprint']}"
            if key not in timestamps:
                all_fingerprints_cached = False
                break

    # If files are identical or we have cached timestamps, just copy segments to synced
    if diff_len == 0 or all_fingerprints_cached:
        if diff_len == 0:
            print("New mp3 is identical, no sync needed.")
        else:
            print("Using cached timestamps from fingerprints")

        # Save updated metadata with final URL
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)

        # Update segments with cached timestamps if needed
        if all_fingerprints_cached:
            out_segments = []
            with open(segments_file) as infile:
                for line in infile:
                    segment = json.loads(line)
                    key = f"{new_len},{segment['fingerprint']}"
                    start_sec = timestamps[key]
                    duration = segment["end"] - segment["start"]
                    segment["start"] = start_sec
                    segment["end"] = start_sec + duration
                    out_segments.append(segment)

            # Write updated segments
            with open(synced_file, "w") as f:
                for segment in out_segments:
                    f.write(json.dumps(segment) + "\n")
        else:
            shutil.copy2(segments_file, synced_file)
        return

    # Get encoding rate and original length from metadata
    orig_bytes_per_sec = metadata["bytes_per_sec"]
    orig_len = metadata["file_size"]
    print(f"Original bytes/sec: {orig_bytes_per_sec:.2f}")

    # Calculate and display duration information
    orig_duration = orig_len / orig_bytes_per_sec
    new_duration = get_duration(url, orig_bytes_per_sec)
    print(f"Original duration: {format_time(orig_duration)}")
    print(f"New duration: {format_time(new_duration)}")
    print(f"Duration difference: {format_time(new_duration - orig_duration)}")
    print()

    # Number of bytes to use for pattern matching
    num_bytes = 128

    # Initialize search state
    last_match_pos = 0
    prev_duration = 0  # Track duration of previous segment

    prev_segment = None

    out_segments = []
    for line in Path(segments_file).read_text().splitlines():
        segment = json.loads(line)
        start_sec = segment["start"]

        # Calculate byte offset in original file using metadata values
        orig_offset = int(start_sec * orig_bytes_per_sec)
        # Get target bytes from new file using the calculated offset
        target_bytes = get_byte_range(url, orig_offset, num_bytes)

        # Search for these bytes in new file starting after previous match
        search_start = last_match_pos
        if prev_duration > 0:
            # Start searching a bit before where we expect the segment to be
            expected_pos = last_match_pos + int(
                (prev_duration - 5) * orig_bytes_per_sec
            )
            search_start = max(last_match_pos, expected_pos)

        pos = search_start
        found = False
        chunk_size = 128 * 1024  # Size of chunks to download and search

        # Search through the file in chunks
        while pos < new_len and not found:
            chunk = get_byte_range(url, pos, chunk_size)
            chunk_pos = chunk.find(target_bytes)

            if chunk_pos != -1:
                found = True
                break

            # Move to next chunk, overlapping slightly to avoid missing matches
            pos += chunk_size - num_bytes
            chunk_size = min(chunk_size * 2, 1024 * 1024)
            continue

        if not found:
            print(f"Segment at {format_time(start_sec)} not found.")
            assert False

        # Found matching bytes - calculate new timing
        actual_pos = pos + chunk_pos
        found_sec = actual_pos / orig_bytes_per_sec
        time_delta = found_sec - start_sec
        print(
            f"Segment at {format_time(start_sec)} found at {format_time(found_sec)} (offset {actual_pos:,}, delta {format_time(abs(time_delta))})"
        )
        found = True
        last_match_pos = actual_pos + 1

        # Add new timestamp to cache
        key = f"{new_len},{segment['fingerprint']}"
        timestamps[key] = found_sec

        # Update segment timestamps and write to synced file
        # Store current segment's start time before updating
        current_start = found_sec
        duration = segment["end"] - segment["start"]
        segment["start"] = current_start
        segment["end"] = current_start + duration

        # For the previous segment, update its end time to be this segment's start
        # This way we keep any ads which were inserted between this pair of segments.
        if out_segments:
            out_segments[-1]["end"] = current_start

        # Store current segment to update its end time when we process the next one
        out_segments.append(segment)
        prev_duration = duration

    # Save updated metadata with final URL
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2)

    # Save updated timestamps
    with open(timestamps_file, "w") as f:
        json.dump(timestamps, f, indent=2)

    # Save synchronized segments
    with open(synced_file, "w") as f:
        for segment in out_segments:
            f.write(json.dumps(segment) + "\n")


if __name__ == "__main__":
    main()

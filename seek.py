#!/usr/bin/env python3

from pathlib import Path
import sys
import json
import requests
from mutagen.mp3 import MP3
from dump import dump
from io import BytesIO


def get_file_size(url):
    # Try HEAD request first
    response = requests.head(url)
    if 'Content-Length' in response.headers:
        return int(response.headers['Content-Length'])
    
    # If no Content-Length, try GET with range header
    response = requests.get(url, headers={'Range': 'bytes=0-0'})
    if 'Content-Range' in response.headers:
        content_range = response.headers['Content-Range']
        return int(content_range.split('/')[-1])
    
    # If all else fails, we'll have to download the whole file
    response = requests.get(url)
    return len(response.content)


def get_byte_range(url, start, length):
    headers = {'Range': f'bytes={start}-{start+length-1}'}
    response = requests.get(url, headers=headers)
    return response.content


def get_duration(url):
    # Download first 1MB which should contain enough frames to calculate duration
    headers = {'Range': 'bytes=0-1048576'}
    response = requests.get(url, headers=headers)
    data = response.content
    
    # Skip ID3v2 tag if present
    offset = 0
    if data[:3] == b'ID3':
        tag_size = (data[6] << 21) | (data[7] << 14) | (data[8] << 7) | data[9]
        offset = tag_size + 10
    
    # Find first MP3 frame
    while offset < len(data) - 4:
        if data[offset:offset+2] == b'\xff\xfb':  # MPEG 1 Layer 3
            break
        offset += 1
    
    if offset >= len(data) - 4:
        raise Exception("Could not find MP3 frame")
    
    # Parse frame header
    header = int.from_bytes(data[offset:offset+4], 'big')
    version = (header >> 19) & 3
    layer = (header >> 17) & 3
    bitrate_index = (header >> 12) & 0xf
    sample_rate_index = (header >> 10) & 3
    padding = (header >> 9) & 1
    
    # Lookup tables
    bitrates = [
        [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 0],  # V1,L3
        [0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160, 0]  # V2,L3
    ]
    sample_rates = [44100, 48000, 32000, 0]  # MPEG1
    
    # Calculate values
    bitrate = bitrates[0 if version == 3 else 1][bitrate_index] * 1000
    sample_rate = sample_rates[sample_rate_index]
    
    if bitrate == 0 or sample_rate == 0:
        raise Exception("Invalid bitrate or sample rate")
        
    # Calculate duration from total file size
    total_size = get_file_size(url)
    duration = (total_size * 8) / bitrate
    
    return duration


def format_time(seconds):
    minutes = int(seconds // 60)
    remaining_seconds = seconds % 60
    return f"{minutes:02d}:{remaining_seconds:05.2f}"


def main():
    orig_file = Path(sys.argv[1]).read_bytes()
    url = sys.argv[2]
    
    # Get new file metadata without downloading whole file
    new_len = get_file_size(url)
    orig_len = len(orig_file)
    diff_len = new_len - orig_len

    print(f"Original length: {orig_len:,}")
    print(f"New length: {new_len:,}")
    print(f"Difference: {diff_len:,}")
    print()

    orig_audio = MP3(sys.argv[1])
    new_duration = get_duration(url)
    print(f"Original duration: {format_time(orig_audio.info.length)}")
    print(f"New duration: {format_time(new_duration)}")
    print(f"Duration difference: {format_time(new_duration - orig_audio.info.length)}")
    print()

    orig_bytes_per_sec = orig_len / orig_audio.info.length
    new_bytes_per_sec = new_len / new_duration
    print(f"Original bytes/sec: {orig_bytes_per_sec:.2f}")
    print(f"New bytes/sec: {new_bytes_per_sec:.2f}")
    print(f"Bytes/sec difference: {(new_bytes_per_sec - orig_bytes_per_sec):.2f}")

    print()

    if len(sys.argv) != 4:
        print("Usage: seek.py ORIG_FILE URL SEGMENTS_FILE")
        sys.exit(1)

    num_bytes = 128
    segments_file = sys.argv[3]

    # Read and process each segment
    last_match_pos = 0
    prev_duration = 0  # Track duration of previous segment
    with open(segments_file) as f:
        for line in f:
            segment = json.loads(line)
            start_sec = segment['start']

            # Calculate byte offset in original file
            orig_offset = int(start_sec * orig_bytes_per_sec)
            target_bytes = orig_file[orig_offset:orig_offset + num_bytes]

            # Search for these bytes in new file starting after previous match
            # Calculate search start position based on previous segment duration
            search_start = last_match_pos
            if prev_duration > 0:
                # Start searching a bit before where we expect the segment to be
                expected_pos = last_match_pos + int((prev_duration - 10) * new_bytes_per_sec)
                search_start = max(last_match_pos, expected_pos)

            pos = search_start

            found = False
            # Search in chunks to avoid downloading entire file
            chunk_size = 50000  # Size of chunks to download and search
            found = False
            pos = search_start
            
            while pos < new_len and not found:
                chunk = get_byte_range(url, pos, chunk_size)
                chunk_pos = chunk.find(target_bytes)
                
                if chunk_pos != -1:
                    actual_pos = pos + chunk_pos
                    found_sec = actual_pos / new_bytes_per_sec
                    time_delta = found_sec - start_sec
                    print(f"Segment at {format_time(start_sec)} found at {format_time(found_sec)} (offset {actual_pos:,}, delta {format_time(abs(time_delta))})")
                    found = True
                    last_match_pos = actual_pos + 1
                    prev_duration = segment['end'] - segment['start']
                else:
                    # Move to next chunk, overlapping slightly to avoid missing matches
                    pos += chunk_size - num_bytes

            if not found:
                print(f"Segment at {format_time(start_sec)} not found.")

if __name__ == '__main__':
    main()

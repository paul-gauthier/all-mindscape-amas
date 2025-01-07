#!/usr/bin/env python3

from jinja2 import Environment, FileSystemLoader
import jsonlines
import json
import sys
from pathlib import Path
from datetime import datetime
import numpy as np
from scipy.io import wavfile
from pydub import AudioSegment
from dump import dump

# Cache for loaded audio files
_audio_cache = {}

def generate_fingerprint(metadata, start_sec, end_sec):
    """Generate a simple audio fingerprint for a segment."""
    dump(start_sec)
    try:
        local_path = metadata['filename']
        
        # Use cached audio if available
        if local_path not in _audio_cache:
            _audio_cache[local_path] = AudioSegment.from_mp3(local_path)
        
        audio = _audio_cache[local_path]
        segment = audio[start_sec*1000:end_sec*1000]

        # Convert to mono wav for analysis
        segment = segment.set_channels(1)
        samples = np.array(segment.get_array_of_samples())

        # Simple FFT-based fingerprint
        window_size = 2048
        hop_size = 1024
        num_peaks = 20

        fingerprint = []
        for i in range(0, len(samples) - window_size, hop_size):
            window = samples[i:i + window_size]
            spectrum = np.abs(np.fft.rfft(window))
            peaks = np.argpartition(spectrum, -num_peaks)[-num_peaks:]
            fingerprint.extend(peaks.tolist())

        return fingerprint
    except Exception as e:
        print(f"Warning: Could not generate fingerprint: {e}")
        return []

def generate_html(input_files):
    # Set up Jinja2 environment
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('index.html')

    all_segments = []

    for input_file in input_files:
        base_path = Path(input_file).with_suffix("")
        input_path = base_path.with_suffix('.segments.jsonl')
        metadata_path = base_path.with_suffix('.json')

        with open(metadata_path) as f:
            metadata = json.load(f)

        with jsonlines.open(input_path) as reader:
            for segment in reader:
                start = int(segment['start'])
                end = int(segment['end'])
                duration = end - start
                duration_str = f"{duration // 60}m{duration % 60:02d}s" if duration >= 60 else f"{duration}s"

                full_text = segment['text'].replace("\n", " ")
                TRUNC = 200
                if len(full_text) > TRUNC:
                    trunc_at = full_text[:TRUNC].rfind(' ')
                    text = full_text[:trunc_at] + "..." if trunc_at > TRUNC - 50 else full_text[:TRUNC - 3] + "..."
                else:
                    text = full_text

                # Parse and format the date
                date_obj = datetime.strptime(metadata['date'], "%a, %d %b %Y %H:%M:%S %z")
                formatted_date = date_obj.strftime("%b<br>%Y")

                fingerprint = generate_fingerprint(metadata, start, end)

                all_segments.append({
                    'start': start,
                    'end': end,
                    'duration_str': duration_str,
                    'text': text,
                    'url': metadata['url'],
                    'title': metadata['title'],
                    'date': formatted_date,
                    'fingerprint': fingerprint
                })

    return template.render(segments=all_segments)

def main():
    if len(sys.argv) < 2:
        print("Usage: python render.py file1_segments.jsonl [file2_segments.jsonl ...]")
        sys.exit(1)

    input_files = sys.argv[1:]
    html = generate_html(input_files)

    output_file = Path("website") / "index.html"
    with open(output_file, 'w') as f:
        f.write(html)

    print(f"Saved to {output_file}")

if __name__ == "__main__":
    main()

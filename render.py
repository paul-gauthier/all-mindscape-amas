#!/usr/bin/env python3

from jinja2 import Environment, FileSystemLoader
import jsonlines
import json
import sys
from pathlib import Path

def generate_html(input_file, metadata_file):
    # Set up Jinja2 environment
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('segments.html')

    with open(metadata_file) as f:
        metadata = json.load(f)
    base_url = metadata['url']

    segments = []
    with jsonlines.open(input_file) as reader:
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

            segments.append({
                'start': start,
                'end': end,
                'duration_str': duration_str,
                'text': text
            })

    return template.render(segments=segments, base_url=base_url)

def main():
    if len(sys.argv) < 2:
        print("Usage: python render.py file1_segments.jsonl [file2_segments.jsonl ...]")
        sys.exit(1)

    for input_file in sys.argv[1:]:
        if not Path(input_file).exists():
            print(f"Error: File {input_file} not found")
            continue

        base_path = Path(input_file).with_suffix("")
        input_path = base_path.with_suffix('.segments.jsonl')
        metadata_path = base_path.with_suffix('.json')
        output_file = Path("website") / (base_path.stem + ".html")

        html = generate_html(input_path, metadata_path)

        with open(output_file, 'w') as f:
            f.write(html)

        print(f"Saved to {output_file}")

if __name__ == "__main__":
    main()

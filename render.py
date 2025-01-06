#!/usr/bin/env python3

import jsonlines
import json
import sys
from pathlib import Path

def generate_html(input_file, metadata_file):
    with open(metadata_file) as f:
        metadata = json.load(f)
    base_url = metadata['url']

    html = """<!DOCTYPE html>
<html>
<head>
    <title>Audio Segments</title>
</head>
<body>
    <h1>Audio Segments</h1>
    <ul>
"""

    with jsonlines.open(input_file) as reader:
        for segment in reader:
            start = int(segment['start'])
            end = int(segment['end'])
            duration = end - start
            url = f"{base_url}#t={start},{end}"
            text = segment['text'].replace("\n", " ")[:100] + "..."

            html += f'        <li><a href="{url}" target="_blank">[{duration}s] {text}</a></li>\n'

    html += """    </ul>
</body>
</html>"""

    return html

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
        output_file = base_path.with_suffix(".links.html")
        html = generate_html(input_path, metadata_path)

        with open(output_file, 'w') as f:
            f.write(html)

        print(f"Saved to {output_file}")

if __name__ == "__main__":
    main()

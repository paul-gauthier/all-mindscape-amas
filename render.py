#!/usr/bin/env python3

import jsonlines
import sys
from pathlib import Path

BASE_URL = "https://content.production.cdn.art19.com/validation=1736178977,3b923f91-5793-5eaa-82de-3bdc74aa5c29,1aDB2fPgm66XpRHYWfjutBUpsEE/episodes/fc3cf13a-51ac-472a-b070-de55023ed70a/912e4e62bbc513fa8caadfe2710a77198c1a8091b5eeee1fd8ff35730475f3dc028ff9e55e454f3d6ae046899cbfa3d5343f0eadc9e8467613a9706717201cd1/AMA-Dec-20.mp3"

def generate_html(input_file):
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
            url = f"{BASE_URL}#t={start},{end}"
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

        # update the filename logic to work like the other scripts. ai!
        output_file = Path(input_file).stem + "_links.html"
        html = generate_html(input_file)

        with open(output_file, 'w') as f:
            f.write(html)

        print(f"Saved to {output_file}")

if __name__ == "__main__":
    main()

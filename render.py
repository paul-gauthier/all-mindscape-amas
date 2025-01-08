#!/usr/bin/env python3

from jinja2 import Environment, FileSystemLoader
import jsonlines
import json
import sys
from pathlib import Path
from datetime import datetime
from dump import dump

def generate_html(input_files):
    # Set up Jinja2 environment
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('index.html')

    all_segments = []

    for input_file in input_files:
        base_path = Path(input_file).with_suffix("")
        input_path = base_path.with_suffix('.synced.jsonl')
        metadata_path = base_path.with_suffix('.json')

        with open(metadata_path) as f:
            metadata = json.load(f)

        print()
        dump(input_file)
        # Use final_url if it exists in metadata, otherwise use url
        chosen_url = metadata['url']  # Always use url as default
        if 'final_url' in metadata and metadata['final_url'] is not None:
            chosen_url = metadata['final_url']
        dump(chosen_url)

        with jsonlines.open(input_path) as reader:
            for segment in reader:
                start = int(segment['start'])
                end = int(segment['end'])
                duration = end - start
                duration_str = f"{duration // 60}m{duration % 60:02d}s" if duration >= 60 else f"{duration}s"

                full_text = segment['text'].replace("\n", " ")
                '''
                TRUNC = 200
                if len(full_text) > TRUNC:
                    trunc_at = full_text[:TRUNC].rfind(' ')
                    text = full_text[:trunc_at] + "..." if trunc_at > TRUNC - 50 else full_text[:TRUNC - 3] + "..."
                else:
                '''
                text = full_text

                # Parse and format the date
                date_obj = datetime.strptime(metadata['date'], "%a, %d %b %Y %H:%M:%S %z")
                formatted_date = date_obj.strftime("%b %Y")

                all_segments.append({
                    'start': start,
                    'end': end,
                    'duration_str': duration_str,
                    'text': text,
                    'url': chosen_url,
                    'title': metadata['title'],
                    'date': formatted_date
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

#!/usr/bin/env python3

import jsonlines
import json
import sys
from pathlib import Path

def generate_html(input_file, metadata_file):
    with open(metadata_file) as f:
        metadata = json.load(f)
    base_url = metadata['url']

    if 'audio_url' not in metadata:
        print(f"Error: Metadata file {metadata_file} is missing required 'audio_url' field")
        sys.exit(1)

    html = """<!DOCTYPE html>
<html>
<head>
    <title>Audio Segments</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        h1 {
            color: #333;
            text-align: center;
        }
        .segment-list {
            list-style: none;
            padding: 0;
        }
        .segment-item {
            padding: 10px;
            margin: 5px 0;
            background: #f5f5f5;
            border-radius: 4px;
            cursor: pointer;
            transition: background 0.2s;
        }
        .segment-item:hover {
            background: #e0e0e0;
        }
        .segment-item.playing {
            background: #d1e8ff;
        }
        .player-container {
            position: sticky;
            top: 0;
            background: white;
            padding: 20px 0;
            z-index: 100;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        audio {
            width: 100%;
        }
    </style>
</head>
<body>
    <h1>Audio Segments</h1>
    <div class="player-container">
        <audio id="audio-player" controls></audio>
    </div>
    <ul class="segment-list">
"""

    with jsonlines.open(input_file) as reader:
        for segment in reader:
            start = int(segment['start'])
            end = int(segment['end'])
            duration = end - start
            url = f"{base_url}#t={start},{end}"
            text = segment['text'].replace("\n", " ")[:100] + "..."

            html += f'        <li class="segment-item" data-start="{start}" data-end="{end}">[{duration}s] {text}</li>\n'

    html += """    </ul>
    <script>
        const player = document.getElementById('audio-player');
        const segments = document.querySelectorAll('.segment-item');
        const audioSrc = '""" + metadata['audio_url'] + """';
        let currentSegment = 0;

        player.src = audioSrc;

        function playSegment(start, end) {
            player.currentTime = start;
            player.play();
            
            // Stop at the end of the segment
            const stopAt = end;
            const checkTime = () => {
                if (player.currentTime >= stopAt) {
                    player.pause();
                    player.removeEventListener('timeupdate', checkTime);
                    
                    // Move to next segment if available
                    if (currentSegment < segments.length - 1) {
                        currentSegment++;
                        const nextSegment = segments[currentSegment];
                        nextSegment.click();
                    }
                }
            };
            player.addEventListener('timeupdate', checkTime);
        }

        segments.forEach((segment, index) => {
            segment.addEventListener('click', () => {
                // Remove playing class from all segments
                segments.forEach(s => s.classList.remove('playing'));
                
                // Add playing class to current segment
                segment.classList.add('playing');
                
                // Scroll segment into view
                segment.scrollIntoView({behavior: 'smooth', block: 'center'});
                
                // Play the segment
                currentSegment = index;
                const start = parseFloat(segment.dataset.start);
                const end = parseFloat(segment.dataset.end);
                playSegment(start, end);
            });
        });
    </script>
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

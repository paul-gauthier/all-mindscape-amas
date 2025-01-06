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
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .segment-item:hover {
            background: #e0e0e0;
        }
        .segment-item.playing {
            background: #d1e8ff;
        }
        .segment-duration {
            background: #e0e0e0;
            padding: 2px 6px;
            border-radius: 12px;
            font-size: 0.9em;
            color: #666;
        }
        .player-container {
            background: white;
            padding: 20px 0;
            margin-bottom: 20px;
            text-align: center;
        }
        audio {
            display: none;
        }
        .player-controls {
            display: inline-flex;
            gap: 10px;
        }
        .player-controls button {
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            background: #007bff;
            color: white;
            cursor: pointer;
            font-size: 14px;
        }
        .player-controls button:hover {
            background: #0056b3;
        }
    </style>
</head>
<body>
    <h1>Audio Segments</h1>
    <div class="player-container">
        <audio id="audio-player"></audio>
        <div class="player-controls">
            <button id="play-button">Play</button>
            <button id="pause-button">Pause</button>
        </div>
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

            html += f'        <li class="segment-item" data-start="{start}" data-end="{end}">\n'
            html += f'            <span class="segment-text">{text}</span>\n'
            html += f'            <span class="segment-duration">{duration}s</span>\n'
            html += f'        </li>\n'

    html += """    </ul>
    <script>
        const player = document.getElementById('audio-player');
        const playButton = document.getElementById('play-button');
        const pauseButton = document.getElementById('pause-button');
        const segments = document.querySelectorAll('.segment-item');
        const audioSrc = '""" + base_url + """';
        let currentSegment = 0;

        player.src = audioSrc;

        playButton.addEventListener('click', () => {
            player.play();
        });

        pauseButton.addEventListener('click', () => {
            player.pause();
        });

        let currentListener = null;

        function playSegment(start, end) {
            // Remove previous listener if it exists
            if (currentListener) {
                player.removeEventListener('timeupdate', currentListener);
                currentListener = null;
            }

            player.currentTime = start;
            player.play();

            // Stop at the end of the segment
            const stopAt = end;
            const checkTime = () => {
                if (player.currentTime >= stopAt) {
                    player.pause();
                    player.removeEventListener('timeupdate', checkTime);
                    currentListener = null;

                    // Move to next segment if available
                    if (currentSegment < segments.length - 1) {
                        currentSegment++;
                        const nextSegment = segments[currentSegment];
                        nextSegment.click();
                    }
                }
            };
            
            currentListener = checkTime;
            player.addEventListener('timeupdate', checkTime);
        }

        segments.forEach((segment, index) => {
            segment.addEventListener('click', () => {
                // Remove playing class from all segments
                segments.forEach(s => s.classList.remove('playing'));

                // Add playing class to current segment
                segment.classList.add('playing');

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

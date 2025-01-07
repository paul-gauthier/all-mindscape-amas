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
    <meta charset="UTF-8">
    <title>Audio Segments</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
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
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.9em;
            color: #666;
            margin-left: 10px;
            margin-right: 5px;
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
            margin-bottom: 10px;
        }
        .player-controls button {
            padding: 8px 12px;
            border: none;
            border-radius: 4px;
            background: #007bff;
            color: white;
            cursor: pointer;
            font-size: 16px;
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
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
            <button id="play-button"><i class="fas fa-play"></i></button>
            <button id="pause-button"><i class="fas fa-pause"></i></button>
            <button id="prev-button"><i class="fas fa-backward"></i></button>
            <button id="next-button"><i class="fas fa-forward"></i></button>
            <button id="shuffle-button"><i class="fas fa-random"></i></button>
        </div>
    </div>
    <ul class="segment-list">
"""

    with jsonlines.open(input_file) as reader:
        for segment in reader:
            start = int(segment['start'])
            end = int(segment['end'])
            duration = end - start
            minutes = duration // 60
            seconds = duration % 60
            duration_str = f"{minutes}m{seconds:02d}s"
            url = f"{base_url}#t={start},{end}"
            # Safely truncate text while preserving Unicode characters and word boundaries
            TRUNC = 200
            full_text = segment['text'].replace("\n", " ")
            if len(full_text) > TRUNC:
                # Find the last space within the first TRUNC characters to avoid breaking words
                trunc_at = full_text[:TRUNC].rfind(' ')
                if trunc_at > TRUNC - 50:  # Ensure we don't cut too much
                    text = full_text[:trunc_at] + "..."
                else:
                    text = full_text[:TRUNC - 3] + "..."
            else:
                text = full_text

            html += f'        <li class="segment-item" data-start="{start}" data-end="{end}">\n'
            html += f'            <span class="segment-text">{text}</span>\n'
            html += f'            <span class="segment-duration">{duration_str}</span>\n'
            html += f'        </li>\n'

    html += """    </ul>
    <script>
        const player = document.getElementById('audio-player');
        const playButton = document.getElementById('play-button');
        const pauseButton = document.getElementById('pause-button');
        const prevButton = document.getElementById('prev-button');
        const nextButton = document.getElementById('next-button');
        const shuffleButton = document.getElementById('shuffle-button');
        const segmentList = document.querySelector('.segment-list');
        let segments = document.querySelectorAll('.segment-item');
        const audioSrc = '""" + base_url + """';
        let currentSegment = 0;

        player.src = audioSrc;

        let firstPlay = true;

        playButton.addEventListener('click', () => {
            if (firstPlay) {
                // Highlight and play the first segment
                segments[0].classList.add('playing');
                const start = parseFloat(segments[0].dataset.start);
                const end = parseFloat(segments[0].dataset.end);
                playSegment(start, end);
                firstPlay = false;
            } else {
                player.play();
            }
        });

        pauseButton.addEventListener('click', () => {
            player.pause();
        });

        nextButton.addEventListener('click', () => {
            if (currentSegment < segments.length - 1) {
                currentSegment++;
                const nextSegment = segments[currentSegment];
                nextSegment.click();
            }
        });

        prevButton.addEventListener('click', () => {
            const currentStart = parseFloat(segments[currentSegment].dataset.start);
            if (player.currentTime - currentStart > 2) {
                // Restart current segment
                segments[currentSegment].click();
            } else if (currentSegment > 0) {
                // Move to previous segment
                currentSegment--;
                const prevSegment = segments[currentSegment];
                prevSegment.click();
            }
        });

        shuffleButton.addEventListener('click', () => {
            // Convert NodeList to array for shuffling
            const segmentsArray = Array.from(segments);

            // Shuffle the array using Fisher-Yates algorithm
            for (let i = segmentsArray.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                [segmentsArray[i], segmentsArray[j]] = [segmentsArray[j], segmentsArray[i]];
            }

            // Clear the current list
            segmentList.innerHTML = '';

            // Append shuffled segments
            segmentsArray.forEach(segment => {
                segmentList.appendChild(segment);
            });

            // Update segments reference to the new order
            segments = document.querySelectorAll('.segment-item');

            // Reset current segment
            currentSegment = 0;

            // Remove playing class from all segments
            segments.forEach(s => s.classList.remove('playing'));

            // Add playing class to new first segment
            segments[0].classList.add('playing');

            // Play the new first segment
            const start = parseFloat(segments[0].dataset.start);
            const end = parseFloat(segments[0].dataset.end);
            playSegment(start, end);
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

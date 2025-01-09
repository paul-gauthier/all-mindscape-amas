# Mindscape AMA Transcripts and Player

This project provides a web-based interface for browsing and playing "Ask Me Anything" (AMA) episodes from Sean Carroll's Mindscape podcast. It includes tools for:

- Downloading podcast episodes
- Transcribing audio with word-level timestamps
- Segmenting transcripts into individual questions/answers
- Generating searchable HTML pages with audio playback

## Features

- **Audio Player**: Play individual question segments with smooth transitions
- **Search & Filter**: Find questions by keyword or filter by episode
- **Transcripts**: Read full question/answer text with timestamps
- **Direct Links**: Share specific segments with timestamped URLs

## Components

The project consists of several Python scripts that handle different stages of processing:

1. **download.py**: Downloads AMA episodes from the podcast RSS feed
2. **transcribe.py**: Transcribes audio using OpenAI Whisper API
3. **segment.py**: Identifies and segments individual questions/answers
4. **summarize.py**: Generates concise summaries of each segment
5. **sync.py**: Synchronizes segments with updated audio files
6. **render.py**: Generates HTML pages from processed data

## Usage

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Download episodes:
```bash
python download.py
```

3. Transcribe audio:
```bash
python transcribe.py data/*.mp3
```

4. Segment transcripts:
```bash
python segment.py data/*.punct.jsonl
```

5. Generate HTML:
```bash
python render.py data/*.segments.jsonl
```

The final HTML output will be in the `website/` directory.

## Requirements

- Python 3.8+
- See requirements.txt for Python dependencies
- OpenAI API key for transcription
- FFmpeg for audio processing

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This project is not affiliated with Sean Carroll or the Mindscape podcast. All audio content is streamed directly from the official podcast feed.

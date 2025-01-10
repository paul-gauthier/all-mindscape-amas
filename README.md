
# All Mindscape AMAs

This project provides a web-based interface for browsing and playing 
individual questions from the
"Ask Me Anything" (AMA) episodes of Sean Carroll's Mindscape podcast. 

## Features

- **Audio Player**
  - Play individual questions directly from the official podcast mp3 feed
  - Includes all the original ads between questions
  - Shuffle to play questions in random order
- **Search & Filter**: Find questions by keyword or by episode
- **Direct Podcast Links**: Launch the podcast starting from any specific question

## Components

The project consists of several Python scripts that handle different stages of processing:

- **download.py**: Downloads AMA episodes from the podcast RSS feed
- **transcribe.py**: Transcribes audio using Whisper
- **segment.py**: Identifies and segments individual questions/answers using DeepSeek
- **summarize.py**: Generates concise summaries of each segment using DeepSeek
- **fingerprint.py**: Creates fingerprints for segment synchronization
- **sync.py**: Synchronizes segment timestamps with updated audio files
- **render.py**: Generates the HTML page from all the processed data

## Notes

Please consider supporting
<a href="https://www.patreon.com/seanmcarroll" target="_blank" rel="noopener noreferrer">
    Mindscape on Patreon</a>.

All audio streams directly from the
<a href="https://art19.com/shows/sean-carrolls-mindscape" target="_blank" rel="noopener noreferrer">
    official feed</a> of the
<a href="https://www.preposterousuniverse.com/podcast/" target="_blank" rel="noopener noreferrer">
    Mindscape podcast</a>,
and includes all the original ads between questions.

This project has no affiliation with Mindscape.

[Aider](https://aider.chat/) wrote more than half of the code for this project.

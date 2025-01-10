
# All Mindscape AMAs

This project provides a web-based interface for browsing and playing 
individual questions from the
"Ask Me Anything" (AMA) episodes of Sean Carroll's Mindscape podcast. 

### 🎧 Listen now: [All Mindscape AMAs](https://paul-gauthier.github.io/all-mindscape-amas/)

## Features

- **Audio Player**
  - Fast forward, rewind, shuffle through questions
  - Plays audio directly from the official podcast mp3 feed
  - Includes all the original ads between questions
- **Search & Filter**: Find questions by keyword or by episode
- **Direct Podcast Links**: Launch the podcast starting from any specific question

## How does it work?

- Download the XML podcast feed
- Download the MP3 files for episodes with titles that contain "AMA"
- Use Whisper to transcribe the MP3s to text with word granularity time stamps
  - Break the 2-3 hour long audio files into overlapping chunks small enough for Whisper to process
  - Stitch the timestamped transcript back together at the midpoints within the overlaps between chunks
- Use DeepSeek to read the transcript and find every question asked
  - DeepSeek returns the exact text of every "question" it finds in the transcript
- Find the MP3 timestamps for each question that DeepSeek found
  - Find the text of each question in the timestamped transcript
  - Use fuzzy matching if needed, to handle cases where DeepSeek returned a slightly incorrect copy of a question
- Create MP3 URLs for each question that deep link into the official podcast feed with `#t=start,end` timestamps
- Ask DeepSeek to generate a short summary of each question & answer.
- Combine the MP3 deep link URLs and summaries into a web page that allows search, browse, shuffle of all the AMA questions

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

All audio plays directly from the
<a href="https://art19.com/shows/sean-carrolls-mindscape" target="_blank" rel="noopener noreferrer">
    official feed</a> of the
<a href="https://www.preposterousuniverse.com/podcast/" target="_blank" rel="noopener noreferrer">
    Mindscape podcast</a>,
and includes all the original ads between questions.

This project has no affiliation with Mindscape.

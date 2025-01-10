#!/bin/bash

# Script to process podcast episode files through the full pipeline:
# 1. Transcription
# 2. Punctuation correction
# 3. Segmentation
# 4. Summarization
# 5. Synchronization
# 6. Final HTML rendering

# Exit immediately if any command fails
set -e

# Handle --force flag to force reprocessing of files
force_flag=""
if [ "$1" = "--force" ]; then
    force_flag="--force"
    shift
fi

# Validate input arguments
if [ -z "$1" ]; then
    echo "Usage: $0 [--force] <input_file> [input_file2 ...]"
    echo "Example: $0 data/2024-12-AMA.mp3 data/2024-11-AMA.mp3"
    echo "  --force   Force reprocessing even if intermediate files exist"
    exit 1
fi

# Process each input file through the pipeline
for input_file in "$@"; do
    # Verify input file exists
    if [ ! -f "$input_file" ]; then
        echo "Error: Input file $input_file does not exist"
        exit 1
    fi

    # Print processing header
    echo
    echo "Processing file: $input_file"
    echo "============================"

    # Run each processing step:
    ./transcribe.py $force_flag "$input_file"
    ./punct.py "$input_file"
    ./segment.py $force_flag "$input_file"
    ./summarize.py $force_flag "$input_file"
    ./sync.py $input_file
done

# Generate final HTML output for all processed files
./render.py "$@"


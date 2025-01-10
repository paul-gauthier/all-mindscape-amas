#!/bin/bash

# Script to synchronize and render audio files for AMA episodes
# Processes one or more audio files through sync.py and then renders them with render.py

# Exit immediately if any command fails
set -e

# Handle optional --force flag
force_flag=""
if [ "$1" = "--force" ]; then
    force_flag="--force"
    shift
fi

# Validate input arguments
if [ -z "$1" ]; then
    echo "Usage: $0 [--force] <input_file> [input_file2 ...]"
    echo "Example: $0 data/2024-12-AMA.mp3 data/2024-11-AMA.mp3"
    echo
    echo "Options:"
    echo "  --force   Force re-processing even if files already exist"
    echo
    echo "Processes audio files through sync.py and then renders them with render.py"
    exit 1
fi

# Process each input file
for input_file in "$@"; do
    # Verify input file exists
    if [ ! -f "$input_file" ]; then
        echo "Error: Input file $input_file does not exist"
        exit 1
    fi

    # Print separator and current file being processed
    echo
    echo
    echo "Processing file: $input_file"
    echo
    
    ./sync.py $force_flag $input_file
done

# After all files are processed, run render.py with all input files
./render.py "$@"


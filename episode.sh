#!/bin/bash

# exit when any command fails
set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <input_file> [input_file2 ...]"
    echo "Example: $0 data/2024-12-AMA.mp3 data/2024-11-AMA.mp3"
    exit 1
fi

for input_file in "$@"; do
    if [ ! -f "$input_file" ]; then
        echo "Error: Input file $input_file does not exist"
        exit 1
    fi

    echo
    echo
    echo $input_file
    echo
    
    ./transcribe.py "$input_file"
    ./punct.py "$input_file"
    ./segment.py "$input_file"
    ./render.py "$input_file"
done


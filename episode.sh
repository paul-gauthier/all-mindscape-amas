#!/bin/bash

# exit when any command fails
set -e

force_flag=""
if [ "$1" = "--force" ]; then
    force_flag="--force"
    shift
fi

if [ -z "$1" ]; then
    echo "Usage: $0 [--force] <input_file> [input_file2 ...]"
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
    
    ./transcribe.py $force_flag "$input_file"
    ./punct.py "$input_file"
    ./segment.py $force_flag "$input_file"
    ./summarize.py $force_flag "$input_file"
    ./sync.py $input_file
done

./render.py "$@"


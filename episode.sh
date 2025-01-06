#!/bin/bash

# exit when any command fails
set -e

# ai: take many filenames on the cmd line, process each one... ai!
if [ -z "$1" ]; then
    echo "Usage: $0 <input_file>"
    echo "Example: $0 data/2024-12-AMA.mp3"
    exit 1
fi

if [ ! -f "$1" ]; then
    echo "Error: Input file $1 does not exist"
    exit 1
fi

./transcribe.py $1
./punct.py $1
./segment.py $1
./render.py $1


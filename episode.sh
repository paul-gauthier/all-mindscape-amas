#!/bin/bash

# exit when any command fails
set -e

# check that $1 exists. ai!

./transcribe.py $1
./punct.py $1
./segement.py $1
./render.py $1


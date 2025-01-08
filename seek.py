#!/usr/bin/env python3

from pathlib import Path
import sys
from mutagen.mp3 import MP3
from dump import dump


def main():
    orig_file = Path(sys.argv[1]).read_bytes()
    new_file = Path(sys.argv[2]).read_bytes()

    orig_len = len(orig_file)
    new_len = len(new_file)
    diff_len = new_len - orig_len

    print(f"Original length: {orig_len:,}")
    print(f"New length: {new_len:,}")
    print(f"Difference: {diff_len:,}")

    orig_audio = MP3(sys.argv[1])
    new_audio = MP3(sys.argv[2])
    print(f"Original duration: {orig_audio.info.length:.3f} seconds")
    print(f"New duration: {new_audio.info.length:.3f} seconds")
    print(f"Duration difference: {(new_audio.info.length - orig_audio.info.length):.3f} seconds")

    # start = 334.505

if __name__ == '__main__':
    main()

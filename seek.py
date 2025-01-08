#!/usr/bin/env python3

from pathlib import Path
import sys
from dump import dump


def main():
    orig_file = Path(sys.argv[1]).read_bytes()
    new_file = Path(sys.argv[2]).read_bytes()

    orig_len = len(orig_file)
    new_len = len(new_file)
    diff_len = new_len - orig_len

    # print the lens with ,000 format. ai!


if __name__ == '__main__':
    main()

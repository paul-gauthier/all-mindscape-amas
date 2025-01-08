#!/usr/bin/env python3

from pathlib import Path
import sys


def main():
    orig_file = Path(sys.argv[1]).read()
    new_file = Path(sys.argv[2]).read()

    dump(len(orig_file))


if __name__ == '__main__':
    main()

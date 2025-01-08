#!/usr/bin/env python3

from pathlib import Path
import sys
from dump import dump


def main():
    orig_file = Path(sys.argv[1]).read_bytes()
    new_file = Path(sys.argv[2]).read_bytes()

    dump(len(orig_file))


if __name__ == '__main__':
    main()

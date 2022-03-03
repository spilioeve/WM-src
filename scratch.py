#!/usr/bin/env python3

from sys import argv
from os.path import isabs

if __name__ == '__main__':
    path = argv[1]
    print(isabs(path))

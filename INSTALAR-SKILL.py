#!/usr/bin/env python3
"""Portable installer. Execute from any working directory after extracting the ZIP."""
from pathlib import Path
import sys

if sys.version_info < (3, 12):
    raise SystemExit('Instale Python 3.12 ou superior: https://www.python.org/downloads/')
sys.path.insert(0, str(Path(__file__).resolve().parent / 'tools'))
from install_skill import main

if __name__ == '__main__':
    raise SystemExit(main())

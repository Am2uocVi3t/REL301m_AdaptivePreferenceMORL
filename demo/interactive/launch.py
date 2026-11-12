#!/usr/bin/env python3
"""Portable entry point: no installation or training side effects."""

import sys
from pathlib import Path

if sys.version_info[:2] != (3, 11):
    raise SystemExit("The demo requires Python 3.11. See README.md for environment setup.")

try:
    from src.demo.server import main
except ImportError as error:
    raise SystemExit("Missing dependency. Install requirements.txt in your Python 3.11 environment. " + str(error)) from error

main(Path(__file__).resolve().parent)

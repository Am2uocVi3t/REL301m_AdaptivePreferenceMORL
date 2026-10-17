#!/usr/bin/env python3
"""Portable entry point: no installation or training side effects."""

import sys
from pathlib import Path

if sys.version_info[:2] != (3, 11):
    raise SystemExit("Demo yêu cầu Python 3.11. Xem README_VI.md để tạo .venv bằng Python 3.11.")

try:
    from src.demo.server import main
except ImportError as error:
    raise SystemExit("Thiếu dependency. Cài requirements.txt trong .venv theo README_VI.md. " + str(error)) from error

main(Path(__file__).resolve().parent)

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.evaluation.course_matrix import build_course_manifest, load_course_study
from src.utils.provenance import write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a non-executing frozen course matrix manifest")
    parser.add_argument("--config", default="configs/experiments/course_paired_matrix_v1.json")
    parser.add_argument("--output", default="research/experiments/course_paired_matrix_v1_manifest.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(__file__).resolve().parents[1]
    config = load_course_study(root / args.config)
    manifest = build_course_manifest(config, root)
    write_json(root / args.output, manifest)
    print(json.dumps({"output": args.output, "jobs": manifest["job_count"], "execution_authorized": False}))


if __name__ == "__main__":
    main()

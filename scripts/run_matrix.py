#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.utils.provenance import collect_provenance, write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a reproducible paired-seed PCQN experiment matrix")
    parser.add_argument("--env", required=True)
    parser.add_argument("--protocol", required=True)
    parser.add_argument(
        "--methods",
        nargs="+",
        choices=("adaptive-pcqn", "uniform-pcqn", "random-curriculum-pcqn"),
        default=("adaptive-pcqn", "uniform-pcqn", "random-curriculum-pcqn"),
    )
    parser.add_argument("--seeds", nargs="+", type=int, default=(1, 2, 3, 4, 5))
    parser.add_argument(
        "--allocation-target",
        choices=("rollout_only", "update_only", "rollout_and_update"),
        default="rollout_and_update",
    )
    parser.add_argument("--total-timesteps", type=int, default=500_000)
    parser.add_argument("--output-dir", default="artifacts/matrix")
    parser.add_argument("--execute", action="store_true", help="Execute instead of printing the frozen matrix")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def make_command(args: argparse.Namespace, method: str, seed: int) -> list[str]:
    return [
        sys.executable,
        "scripts/train.py",
        "--env",
        args.env,
        "--protocol",
        args.protocol,
        "--algo",
        method,
        "--allocation-target",
        args.allocation_target,
        "--seed",
        str(seed),
        "--total-timesteps",
        str(args.total_timesteps),
        "--output-dir",
        args.output_dir,
    ]


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    jobs: list[dict[str, Any]] = []
    for method in args.methods:
        for seed in args.seeds:
            final_checkpoint = output_dir / f"{method}_{args.env}_seed{seed}" / "final.pt"
            jobs.append(
                {
                    "method": method,
                    "seed": seed,
                    "command": make_command(args, method, seed),
                    "final_checkpoint": str(final_checkpoint),
                    "status": "planned",
                }
            )

    manifest_path = output_dir / "matrix_manifest.json"
    manifest = {
        "schema_version": 1,
        "provenance": collect_provenance(vars(args)),
        "jobs": jobs,
    }
    write_json(manifest_path, manifest)

    if not args.execute:
        print(f"Wrote dry-run matrix with {len(jobs)} jobs to {manifest_path}")
        for job in jobs:
            print(" ".join(job["command"]))
        return

    for job in jobs:
        checkpoint = Path(job["final_checkpoint"])
        if checkpoint.exists() and not args.overwrite:
            raise FileExistsError(f"Refusing to overwrite completed run: {checkpoint}")
        started_at = time.time()
        job["status"] = "running"
        write_json(manifest_path, manifest)
        try:
            subprocess.run(job["command"], check=True)
        except subprocess.CalledProcessError:
            job["status"] = "failed"
            job["elapsed_seconds"] = time.time() - started_at
            write_json(manifest_path, manifest)
            raise
        job["status"] = "complete"
        job["elapsed_seconds"] = time.time() - started_at
        write_json(manifest_path, manifest)


if __name__ == "__main__":
    main()

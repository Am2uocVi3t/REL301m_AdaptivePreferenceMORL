#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import torch

from src.evaluation.calibration import load_calibration_plan
from src.evaluation.pilot import build_pilot_jobs, pilot_manifest
from src.utils.provenance import collect_provenance, write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate or execute the predeclared pilot calibration matrix")
    parser.add_argument("--plan", default="configs/pilots/calibration_v1.json")
    parser.add_argument("--output-dir", default="artifacts/pilot-calibration-v1")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--smoke", action="store_true", help="Use non-freezable smoke budgets and one seed")
    parser.add_argument("--execute", action="store_true", help="Execute jobs instead of only writing the manifest")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    plan = load_calibration_plan(args.plan)
    output_dir = Path(args.output_dir)
    jobs = build_pilot_jobs(
        plan,
        output_dir=output_dir,
        python_executable=sys.executable,
        device=args.device,
        smoke=args.smoke,
    )
    manifest = pilot_manifest(
        plan,
        jobs,
        plan_path=args.plan,
        smoke=args.smoke,
        provenance=collect_provenance(vars(args)),
    )
    manifest_path = output_dir / "pilot_manifest.json"
    write_json(manifest_path, manifest)

    if not args.execute:
        print(f"Wrote {'smoke' if args.smoke else 'pilot'} manifest with {len(jobs)} jobs to {manifest_path}")
        for job in jobs:
            print(" ".join(job["train_command"]))
            print(" ".join(job["evaluation_command"]))
        return

    for job in jobs:
        checkpoint = Path(job["checkpoint"])
        evaluation_output = Path(job["evaluation_output"])
        if not args.overwrite and (checkpoint.exists() or evaluation_output.exists()):
            raise FileExistsError(
                f"Refusing to overwrite pilot outputs for {job['env_id']} seed {job['training_seed']}"
            )

        started_at = time.time()
        job["status"] = "training"
        write_json(manifest_path, manifest)
        try:
            subprocess.run(job["train_command"], check=True)
            job["status"] = "evaluating"
            write_json(manifest_path, manifest)
            subprocess.run(job["evaluation_command"], check=True)
        except subprocess.CalledProcessError:
            job["status"] = "failed"
            job["elapsed_seconds"] = time.time() - started_at
            write_json(manifest_path, manifest)
            raise
        job["status"] = "complete"
        job["elapsed_seconds"] = time.time() - started_at
        write_json(manifest_path, manifest)

    manifest["eligible_for_freeze_evidence"] = not args.smoke
    write_json(manifest_path, manifest)
    print(f"Completed {len(jobs)} {'smoke' if args.smoke else 'pilot'} jobs; manifest: {manifest_path}")


if __name__ == "__main__":
    main()

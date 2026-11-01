#!/usr/bin/env python3
"""Run the fixed, presentation-only replacement jobs; never a course comparison."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.evaluation.protocol import load_protocol, protocol_hash

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "configs/demos/recovery_presentation_v1.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_status(path: Path, value: dict[str, Any]) -> None:
    pending = path.with_suffix(".pending")
    pending.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8", newline="\n")
    pending.replace(path)


def build_jobs(plan: dict[str, Any], root: Path = ROOT) -> list[dict[str, Any]]:
    if (
        plan.get("purpose") != "presentation_replacement_only"
        or plan.get("course_evidence") is not False
        or plan.get("final_test_permitted") is not False
        or plan.get("checkpoint_selection") != "final_at_fixed_budget_no_selection"
        or plan.get("algorithm") != "uniform-pcqn"
        or plan.get("budget", {}).get("training_interactions_per_job") != 100_000
        or len(plan.get("jobs", [])) != 2
    ):
        raise ValueError("Unexpected or expanded recovery-presentation scope")
    output = Path(plan["output_root"])
    if output.is_absolute() or ".." in output.parts or output.parts[:1] != ("artifacts",):
        raise ValueError("Presentation outputs must stay under workspace artifacts")
    jobs = []
    for spec in plan["jobs"]:
        protocol, _ = load_protocol(root / spec["protocol"], "validation")
        if protocol_hash(protocol) != spec["protocol_sha256"] or protocol["env_id"] != spec["environment"]:
            raise ValueError("Presentation protocol drift")
        command = [
            sys.executable,
            "scripts/train.py",
            "--env",
            spec["environment"],
            "--protocol",
            spec["protocol"],
            "--algo",
            "uniform-pcqn",
            "--seed",
            str(spec["training_seed"]),
            "--total-timesteps",
            "100000",
            "--learning-starts",
            "5000",
            "--train-freq",
            "4",
            "--batch-size",
            "64",
            "--curriculum-update-freq",
            "100001",
            "--eval-freq",
            "100001",
            "--save-freq",
            "100000",
            "--isolate-evaluation-rng",
            "--independent-rng-streams",
            "--device",
            "cpu",
            "--output-dir",
            output.as_posix(),
        ]
        folder = output / f"uniform-pcqn_{spec['environment']}_seed{spec['training_seed']}"
        jobs.append(spec | {"command": command, "checkpoint": (folder / "final.pt").as_posix()})
    return jobs


def execute(plan: dict[str, Any], jobs: list[dict[str, Any]]) -> None:
    if ROOT.drive.lower() != "d:":
        raise ValueError("Recovery training is restricted to the D: workspace")
    for variable in ("TEMP", "TMP", "UV_CACHE_DIR", "MPLCONFIGDIR", "TORCH_HOME"):
        if Path(os.environ.get(variable, "")).drive.lower() != "d:":
            raise ValueError(f"Dot-source scripts/use_d_runtime.ps1 first; {variable} is not on D:")
    if sys.version_info[:2] != (3, 11):
        raise ValueError("Python 3.11 is required")
    output = ROOT / plan["output_root"]
    output.mkdir(parents=True, exist_ok=True)
    status_path = output / "execution_status.json"
    plan_hash = digest(PLAN)
    status = (
        json.loads(status_path.read_text())
        if status_path.exists()
        else {"plan_sha256": plan_hash, "course_evidence": False, "final_test_accessed": False, "jobs": {}}
    )
    if status.get("plan_sha256") != plan_hash:
        raise ValueError("Existing presentation execution binds a different plan")
    for job in jobs:
        checkpoint = ROOT / job["checkpoint"]
        previous = status["jobs"].get(job["id"])
        if previous:
            if previous["status"] == "complete" and digest(checkpoint) == previous["checkpoint_sha256"]:
                print(f"SKIP verified {job['id']}", flush=True)
                continue
            raise ValueError("Existing partial/failed presentation job cannot be silently retried")
        if checkpoint.parent.exists():
            raise ValueError("Untracked presentation job directory exists; refusing overwrite")
        record = {"status": "running", "command": job["command"], "checkpoint": job["checkpoint"]}
        status["jobs"][job["id"]] = record
        write_status(status_path, status)
        print(f"START {job['id']} 100000 interactions, CPU, log={output / (job['id'] + '.log')}", flush=True)
        try:
            with (output / f"{job['id']}.log").open("w", encoding="utf-8") as log:
                subprocess.run(job["command"], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
            record.update(status="complete", checkpoint_sha256=digest(checkpoint))
            write_status(status_path, status)
            print(f"COMPLETE {job['id']}", flush=True)
        except Exception as error:
            record.update(status="failed", error=str(error))
            write_status(status_path, status)
            raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    plan = json.loads(PLAN.read_text())
    jobs = build_jobs(plan)
    if not args.execute:
        print(json.dumps({"execute": False, "course_evidence": False, "jobs": jobs}, indent=2))
        return
    execute(plan, jobs)


if __name__ == "__main__":
    main()

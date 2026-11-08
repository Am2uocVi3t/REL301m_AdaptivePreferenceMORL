"""Finite P1 preference-transfer diagnosis, launched independently by the Windows provider."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import TextIO

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.launch_credit_recovery import job_information
from src.utils.training_recovery import atomic_json, process_birth, process_lease

PLAN = Path("configs/experiments/preference_transfer_p1_v1.json")
ROOT = Path("artifacts/preference-transfer-p1-v1")


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    with process_lease(ROOT / "coordinator.lock"):
        if job_information()["member"]:
            raise RuntimeError("Diagnostic coordinator must be outside Windows Jobs")
        if subprocess.check_output(["git", "status", "--porcelain"], text=True).strip():
            raise ValueError("Commit the diagnostic plan and source before dispatch")
        plan = json.loads(PLAN.read_text())
        receipt = json.loads(Path("research/qualification/preference_transfer_p1_v1.json").read_text())
        if receipt["status"] != "pass" or receipt["plan_sha256"] != hashlib.sha256(PLAN.read_bytes()).hexdigest():
            raise ValueError("P1 qualification is absent or stale")
        for filename, expected in receipt["source_files"].items():
            if hashlib.sha256(Path(filename).read_bytes()).hexdigest() != expected:
                raise ValueError(f"P1 source changed since qualification: {filename}")
        jobs = [
            {"name": m["name"], "state": "pending"}
            for m in sorted(plan["models"], key=lambda m: (m["env_id"] != "minecart-v0", m["name"]))
        ]
        status = {
            "study_id": plan["study_id"],
            "pid": os.getpid(),
            "birth": process_birth(os.getpid()),
            "plan_sha256": hashlib.sha256(PLAN.read_bytes()).hexdigest(),
            "jobs": jobs,
            "state": "running",
            "training_interactions": 0,
            "gradient_updates": 0,
            "final_test_steps": 0,
        }
        path = ROOT / "execution_status.json"
        if path.exists():
            raise ValueError("Existing diagnosis must not be overwritten or automatically retried")
        atomic_json(path, status)
        running: dict[str, tuple[subprocess.Popen[bytes], TextIO]] = {}
        failed = False
        while True:
            for job in jobs:
                if len(running) >= 3 or failed:
                    break
                if job["state"] != "pending":
                    continue
                new_log = (ROOT / f"{job['name']}.log").open("w", encoding="utf-8")
                process = subprocess.Popen(
                    [sys.executable, "scripts/run_preference_transfer.py", "--job", job["name"]],
                    stdout=new_log,
                    stderr=subprocess.STDOUT,
                )
                running[job["name"]] = (process, new_log)
                job.update(state="running", pid=process.pid)
            for job in jobs:
                if job["name"] not in running:
                    continue
                process, log = running[job["name"]]
                if process.poll() is None:
                    continue
                log.close()
                job.update(state="complete" if process.returncode == 0 else "failed", returncode=process.returncode)
                failed |= process.returncode != 0
                running.pop(job["name"])
            status["updated_unix"] = time.time()
            atomic_json(path, status)
            if not running and (failed or all(j["state"] == "complete" for j in jobs)):
                break
            time.sleep(3)
        status["state"] = "failed" if failed else "complete"
        atomic_json(path, status)
        if failed:
            raise RuntimeError("A frozen diagnostic failed; preserve logs, no automatic retry")


if __name__ == "__main__":
    root = ROOT
    root.mkdir(parents=True, exist_ok=True)
    sys.stdout = (root / "coordinator.stdout.log").open("a", encoding="utf-8")
    sys.stderr = (root / "coordinator.stderr.log").open("a", encoding="utf-8")
    main()

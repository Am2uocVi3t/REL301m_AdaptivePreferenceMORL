"""Run only the frozen 12-job development cohort, with three local workers."""

from __future__ import annotations

import concurrent.futures
import hashlib
import itertools
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.run_credit_assignment import PLAN, ROOT, save_json


def main() -> None:
    qualification = Path("research/qualification/credit_assignment_v1.json")
    if not qualification.exists() or json.loads(qualification.read_text())["status"] != "pass":
        raise ValueError("Repeated CUDA learning witness must pass first")
    if subprocess.check_output(["git", "status", "--porcelain"], text=True).strip():
        raise ValueError("Commit and qualify the study source before main execution")
    plan = json.loads(PLAN.read_text())
    ROOT.mkdir(parents=True, exist_ok=True)
    source_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    jobs = []
    for protocol, seed, n in itertools.product(plan["protocols"], plan["seeds"], plan["arms"]):
        env_id = json.loads(Path(protocol).read_text())["env_id"]
        name = f"{env_id}_n{n}_seed{seed}"
        directory = ROOT / "runs" / name
        if directory.exists():
            raise ValueError(f"Existing main job must be audited, not overwritten: {directory}")
        jobs.append({"name": name, "protocol": protocol, "seed": seed, "n": n, "state": "pending"})
    status = {
        "study_id": plan["study_id"],
        "source_commit": source_commit,
        "plan_sha256": hashlib.sha256(PLAN.read_bytes()).hexdigest(),
        "max_workers": 3,
        "jobs": jobs,
        "final_test_steps": 0,
    }
    status_path = ROOT / "execution_status.json"
    if status_path.exists():
        raise ValueError("Existing execution status requires explicit audit before another dispatch")
    save_json(status_path, status)

    def execute(job: dict) -> int:
        with (
            (ROOT / f"{job['name']}.stdout.log").open("w", encoding="utf-8") as stdout,
            (ROOT / f"{job['name']}.stderr.log").open("w", encoding="utf-8") as stderr,
        ):
            process = subprocess.Popen(
                [
                    sys.executable,
                    "scripts/run_credit_assignment.py",
                    "--protocol",
                    job["protocol"],
                    "--seed",
                    str(job["seed"]),
                    "--n",
                    str(job["n"]),
                ],
                stdout=stdout,
                stderr=stderr,
            )
            # The coordinator alone writes the status file at submission/completion.
            return process.wait()

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(execute, job): job for job in jobs}
        for job in jobs:
            job["state"] = "queued_or_running"
        save_json(status_path, status)
        for future in concurrent.futures.as_completed(futures):
            job = futures[future]
            code = future.result()
            job["returncode"] = code
            job["state"] = "complete" if code == 0 else "technical_failure"
            save_json(status_path, status)
            print(f"{job['name']}: {job['state']}", flush=True)
    if any(job["state"] != "complete" for job in jobs):
        raise SystemExit("Cohort contains technical failures; preserve them for audit")
    print("All 12 jobs completed. Analyze actual retained evidence before making claims.", flush=True)


if __name__ == "__main__":
    main()

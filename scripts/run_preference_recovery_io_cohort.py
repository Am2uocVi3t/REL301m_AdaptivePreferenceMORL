"""Bounded P2 factorial dispatch; no automatic retries or scientific gate unlock."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.preference_recovery_io import AMENDMENT, verify_qualification
from scripts.preference_recovery_io import atomic_json_retry as atomic_json
from src.utils.training_recovery import process_birth, process_lease

ROOT = Path("artifacts/preference-recovery-p2-v1")
PLAN = Path("configs/experiments/preference_recovery_p2_v1.json")


def read(path: Path) -> Any:
    return json.loads(path.read_text())


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def preflight() -> None:
    from scripts.launch_credit_recovery import job_information

    if job_information()["member"]:
        raise RuntimeError("P2 coordinator must be outside Windows Jobs")
    verify_qualification()
    amendment = read(AMENDMENT)
    for filename, expected in amendment["retained_files"].items():
        if sha(Path(filename)) != expected:
            raise ValueError(f"Retained completed artifact changed: {filename}")
    receipt = read(Path("research/qualification/preference_recovery_p2_v1.json"))
    if receipt["status"] != "pass":
        raise ValueError("P2 qualification did not pass")
    for filename, expected in receipt["source_sha256"].items():
        if sha(Path(filename)) != expected:
            raise ValueError(f"Qualified source changed: {filename}")
    plan = read(PLAN)
    p1_path = Path(plan["p1_evidence"])
    if sha(p1_path) != plan["p1_evidence_sha256"]:
        raise ValueError("P1 evidence changed")
    p1 = read(p1_path)
    if p1["audit"] != "trace_numeric_and_source_pass" or any(
        g["pass"] for g in p1["gates"] if g["env_id"] == "minecart-v0"
    ):
        raise ValueError("P2 is conditional on audited P1 being insufficient for Minecart")
    if subprocess.check_output(["git", "status", "--porcelain"], text=True).strip():
        raise ValueError("Commit source and state before P2 dispatch")


def main(resume_existing: bool = False) -> None:
    with process_lease(ROOT / "coordinator.lock"):
        preflight()
        plan = read(PLAN)
        path = ROOT / "execution_status.json"
        if path.exists():
            if not resume_existing:
                raise ValueError("Existing execution requires explicit ResumeExisting")
            status = read(path)
            if status["plan_sha256"] != sha(PLAN):
                raise ValueError("Recovery amendment changed")
        else:
            jobs = []
            for seed in plan["seeds"]:
                for arm in plan["factorial_arms"]:
                    name = f"minecart-v0_{arm}_seed{seed}"
                    jobs.append(
                        {
                            "name": name,
                            "protocol": plan["protocols"][0],
                            "arm": arm,
                            "n": 1,
                            "seed": seed,
                            "directory": str(ROOT / "runs" / name),
                            "origin": "new_factorial",
                            "state": "pending",
                        }
                    )
            status = {
                "study_id": plan["study_id"],
                "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
                "plan_sha256": sha(PLAN),
                "jobs": jobs,
                "final_test_steps": 0,
                "segments": [],
            }
        status.update(
            coordinator_pid=os.getpid(), coordinator_birth=process_birth(os.getpid()), coordinator_state="running"
        )
        status["segments"].append({"pid": os.getpid(), "started_unix": time.time(), "explicit_resume": resume_existing})
        status["segments"][-1]["io_amendment_sha256"] = sha(AMENDMENT)
        status["segments"][-1]["source_commit"] = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip()
        status["io_recovery_amendment"] = str(AMENDMENT)
        running: dict[str, tuple[subprocess.Popen | None, Any, Any]] = {}
        stop_dispatch = False
        for job in status["jobs"]:
            if job["state"] == "complete":
                completion_path = Path(job["directory"]) / "complete.json"
                if not completion_path.exists() or (
                    "completion_sha256" in job and sha(completion_path) != job["completion_sha256"]
                ):
                    raise ValueError("A recorded completed artifact is missing or changed")
                continue
            directory = Path(job["directory"])
            complete = directory / "complete.json"
            if complete.exists():
                job["state"] = "complete"
                continue
            heartbeat = directory / "heartbeat.json"
            live = read(heartbeat) if heartbeat.exists() else None
            if live and live.get("process_birth") and process_birth(live["pid"]) == live["process_birth"]:
                job.update(state="running", pid=live["pid"], birth=live["process_birth"], adopted=True)
                running[job["name"]] = (None, None, None)
            elif directory.exists() and any(p.name != "worker.lock" for p in directory.iterdir()):
                if not (directory / "resume_latest.json").exists():
                    job["state"] = "interrupted_without_resume_checkpoint"
                    stop_dispatch = True
                else:
                    job.update(
                        state="pending_resume",
                        prior_progress=read(directory / "progress.json")
                        if (directory / "progress.json").exists()
                        else live,
                        prior_heartbeat=live,
                        resume_checkpoint=read(directory / "resume_latest.json"),
                    )
            else:
                job["state"] = "pending"
        atomic_json(path, status)
        while True:
            for job in status["jobs"]:
                if len(running) >= 3 or stop_dispatch:
                    break
                if job["state"] not in ("pending", "pending_resume"):
                    continue
                command = [
                    sys.executable,
                    "scripts/run_preference_recovery_io.py",
                    "--protocol",
                    job["protocol"],
                    "--n",
                    str(job["n"]),
                    "--seed",
                    str(job["seed"]),
                    "--arm",
                    job["arm"],
                ]
                if job["state"] == "pending_resume":
                    command.append("--resume")
                stdout = (ROOT / f"{job['name']}.stdout.log").open("a", encoding="utf-8")
                stderr = (ROOT / f"{job['name']}.stderr.log").open("a", encoding="utf-8")
                launched_process = subprocess.Popen(command, stdout=stdout, stderr=stderr)
                running[job["name"]] = (launched_process, stdout, stderr)
                job.update(
                    state="running",
                    pid=launched_process.pid,
                    birth=process_birth(launched_process.pid),
                    started_unix=time.time(),
                )
                atomic_json(path, status)
            for job in status["jobs"]:
                if job["name"] not in running:
                    continue
                process, stdout, stderr = running[job["name"]]
                directory = Path(job["directory"])
                heartbeat = directory / "heartbeat.json"
                if heartbeat.exists():
                    job["heartbeat"] = read(heartbeat)
                exited = (
                    process.poll() is not None if process is not None else process_birth(job["pid"]) != job["birth"]
                )
                if not exited:
                    continue
                if stdout is not None:
                    stdout.close()
                    stderr.close()
                complete = directory / "complete.json"
                if complete.exists() and (process is None or process.returncode == 0):
                    job["state"] = "complete"
                    job["completion"] = read(complete)
                    job["completion_sha256"] = sha(complete)
                else:
                    job.update(state="technical_failure", returncode=process.returncode if process else None)
                    stop_dispatch = True
                running.pop(job["name"])
            status["updated_unix"] = time.time()
            atomic_json(path, status)
            if not running and (stop_dispatch or all(j["state"] == "complete" for j in status["jobs"])):
                break
            time.sleep(5)
        status["coordinator_state"] = "blocked" if stop_dispatch else "training_complete"
        atomic_json(path, status)
        if stop_dispatch:
            raise RuntimeError("Technical interruption: no automatic retry; inspect status before explicit resume")
        with (ROOT / "postprocess.log").open("w", encoding="utf-8") as log:
            result = subprocess.run(
                [sys.executable, "scripts/analyze_preference_recovery_io.py"],
                stdout=log,
                stderr=subprocess.STDOUT,
            )
        status["postprocess_returncode"] = result.returncode
        status["coordinator_state"] = "complete_audited" if result.returncode == 0 else "audit_failed"
        atomic_json(path, status)
        if result.returncode:
            raise RuntimeError("Post-cohort numeric audit failed; no scientific gate unlock")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--resume-existing", action="store_true")
    args = parser.parse_args()
    ROOT.mkdir(parents=True, exist_ok=True)
    sys.stdout = (ROOT / "coordinator.stdout.log").open("a", encoding="utf-8")
    sys.stderr = (ROOT / "coordinator.stderr.log").open("a", encoding="utf-8")
    main(args.resume_existing)

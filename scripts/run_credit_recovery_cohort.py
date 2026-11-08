"""Bounded recovery dispatch with live identities, leases and explicit resume."""

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

from src.utils.training_recovery import atomic_json, process_birth, process_lease

ROOT = Path("artifacts/credit-assignment-recovery-v1")
AMENDMENT = Path("configs/experiments/credit_assignment_recovery_v1.json")
PLAN = Path("configs/experiments/credit_assignment_v1.json")


def read(path: Path) -> Any:
    return json.loads(path.read_text())


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def preflight() -> None:
    for name in (
        "credit_recovery_numerical_v1.json",
        "credit_recovery_durable_v1.json",
        "credit_recovery_tail_v1.json",
    ):
        receipt = read(Path("research/qualification") / name)
        if receipt["status"] != "pass":
            raise ValueError(f"Qualification did not pass: {name}")
        for filename, expected in receipt["source_sha256"].items():
            if sha(Path(filename)) != expected:
                raise ValueError(f"Qualified source changed: {filename}")
    retained = read(Path("research/qualification/credit_recovery_retained_jobs_v1.json"))
    for filename, expected in retained["files"].items():
        if sha(Path(filename)) != expected:
            raise ValueError(f"Original completed artifact changed: {filename}")
    if subprocess.check_output(["git", "status", "--porcelain"], text=True).strip():
        raise ValueError("Commit source and state before dispatch")


def main(resume_existing: bool = False) -> None:
    with process_lease(ROOT / "coordinator.lock"):
        preflight()
        amendment = read(AMENDMENT)
        plan = read(PLAN)
        path = ROOT / "execution_status.json"
        if path.exists():
            if not resume_existing:
                raise ValueError("Existing execution requires explicit ResumeExisting")
            status = read(path)
            if status["amendment_sha256"] != sha(AMENDMENT):
                raise ValueError("Recovery amendment changed")
        else:
            jobs = []
            for name in [*amendment["retained_original_jobs"], *amendment["new_jobs"]]:
                original = name in amendment["retained_original_jobs"]
                protocol = next(p for p in plan["protocols"] if name.startswith(read(Path(p))["env_id"] + "_"))
                n, seed = name.rsplit("_n", 1)[1].split("_seed")
                directory = Path("artifacts/credit-assignment-v1/runs") / name if original else ROOT / "runs" / name
                jobs.append(
                    {
                        "name": name,
                        "protocol": protocol,
                        "n": int(n),
                        "seed": int(seed),
                        "directory": str(directory),
                        "origin": "retained_original" if original else "recovery",
                        "state": "complete" if original else "pending",
                    }
                )
            status = {
                "study_id": amendment["study_id"],
                "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
                "original_source_commit": "71b96905c577e4fedeff920a148c620737700caf",
                "plan_sha256": sha(PLAN),
                "amendment_sha256": sha(AMENDMENT),
                "jobs": jobs,
                "final_test_steps": 0,
                "segments": [],
            }
        status.update(
            coordinator_pid=os.getpid(), coordinator_birth=process_birth(os.getpid()), coordinator_state="running"
        )
        status["segments"].append({"pid": os.getpid(), "started_unix": time.time(), "explicit_resume": resume_existing})
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
                    "scripts/run_credit_assignment_recoverable.py",
                    "--protocol",
                    job["protocol"],
                    "--n",
                    str(job["n"]),
                    "--seed",
                    str(job["seed"]),
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
                [sys.executable, "scripts/analyze_credit_assignment.py", "--recovery"],
                stdout=log,
                stderr=subprocess.STDOUT,
            )
        status["postprocess_returncode"] = result.returncode
        status["coordinator_state"] = "complete_audited" if result.returncode == 0 else "audit_failed"
        atomic_json(path, status)
        if result.returncode:
            raise RuntimeError("Post-cohort numeric audit failed; no scientific gate unlock")


if __name__ == "__main__":
    main()

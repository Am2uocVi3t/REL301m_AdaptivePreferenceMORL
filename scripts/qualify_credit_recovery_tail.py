"""Kill after unsaved learning steps and verify rewind/replay equals continuous training."""

from __future__ import annotations

import hashlib
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.qualify_credit_recovery import ROOT as CONTROLS
from scripts.qualify_credit_recovery import command, compare, read
from src.utils.training_recovery import atomic_json


def main() -> None:
    root = Path("artifacts/credit-recovery-tail-v1")
    root.mkdir(parents=True, exist_ok=False)
    plan = read(Path("configs/experiments/credit_assignment_v1.json"))
    records = []
    for protocol in plan["protocols"]:
        env_id = read(Path(protocol))["env_id"]
        for n in (1, 20):
            case = root / f"{env_id}_n{n}"
            case.mkdir()
            suffix = Path("smoke") / f"{env_id}_n{n}_seed20261511"
            directory = case / suffix
            with (case / "interrupted.log").open("w", encoding="utf-8") as log:
                process = subprocess.Popen(command(protocol, n, case, 12000), stdout=log, stderr=subprocess.STDOUT)
                try:
                    deadline = time.monotonic() + 180
                    while True:
                        heartbeat = directory / "heartbeat.json"
                        if heartbeat.exists() and read(heartbeat)["step"] >= 11000:
                            break
                        if process.poll() is not None or time.monotonic() >= deadline:
                            raise RuntimeError("Could not inject a mid-episode interruption")
                        time.sleep(0.02)
                    before = read(heartbeat)
                    checkpoint = read(directory / "resume_latest.json")
                    if checkpoint["step"] >= before["step"]:
                        raise AssertionError("Test must discard actual unsaved training work")
                    subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], check=True, capture_output=True)
                    process.wait(timeout=30)
                    if (directory / "complete.json").exists():
                        raise AssertionError("Interruption arrived after completion")
                finally:
                    if process.poll() is None:
                        subprocess.run(
                            ["taskkill", "/PID", str(process.pid), "/T", "/F"], check=True, capture_output=True
                        )
                        process.wait(timeout=30)
            with (case / "resumed.log").open("w", encoding="utf-8") as log:
                subprocess.run(
                    [*command(protocol, n, case, 12000), "--resume"],
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    check=True,
                    timeout=180,
                )
            compare(CONTROLS / f"{env_id}_n{n}" / "continuous" / suffix, directory, 12000)
            records.append(
                {
                    "env_id": env_id,
                    "n": n,
                    "resume_step": checkpoint["step"],
                    "last_observed_step": before["step"],
                    "discarded_training_lower_bound": before["step"] - checkpoint["step"],
                    "discarded_training_upper_bound": 12000 - checkpoint["step"],
                    "result": "exact_model_target_optimizer_episode_and_evaluation_match",
                }
            )
            print(records[-1], flush=True)
    paths = [
        Path("scripts/run_credit_assignment_recoverable.py"),
        Path("src/utils/training_recovery.py"),
        Path("configs/experiments/credit_assignment_recovery_v1.json"),
    ]
    atomic_json(
        Path("research/qualification/credit_recovery_tail_v1.json"),
        {
            "status": "pass",
            "records": records,
            "base_training_interactions": 48000,
            "additional_discarded_work_bounds": [
                sum(r["discarded_training_lower_bound"] for r in records),
                sum(r["discarded_training_upper_bound"] for r in records),
            ],
            "source_sha256": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        },
    )


if __name__ == "__main__":
    main()

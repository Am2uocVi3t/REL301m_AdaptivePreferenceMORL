"""Read live process identities instead of trusting stale running flags."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.utils.training_recovery import process_birth


def main() -> None:
    root = Path("artifacts/credit-assignment-recovery-v1")
    path = root / "execution_status.json"
    if not path.exists():
        print("Recovery cohort has not started")
        return
    status = json.loads(path.read_text())
    coordinator_alive = process_birth(status["coordinator_pid"]) == status["coordinator_birth"]
    print(f"Coordinator alive: {coordinator_alive}; recorded phase: {status['coordinator_state']}")
    for job in status["jobs"]:
        directory = Path(job["directory"])
        hb_path = directory / "heartbeat.json"
        hb = json.loads(hb_path.read_text()) if hb_path.exists() else job.get("heartbeat", {})
        state = job["state"]
        if state == "running":
            pid, birth = hb.get("pid", job["pid"]), hb.get("process_birth", job["birth"])
            if not birth or process_birth(pid) != birth:
                state = "interrupted_process_absent"
        progress = directory / "progress.json"
        saved = json.loads(progress.read_text()) if progress.exists() else {}
        step = hb.get("step", saved.get("step", 0))
        age = round(time.time() - hb["updated_unix"]) if "updated_unix" in hb else None
        print(f"{job['name']}: {state}; step={step}; heartbeat_age_s={age}; resume_step={hb.get('resume_step')}")


if __name__ == "__main__":
    main()

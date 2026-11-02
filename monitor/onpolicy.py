"""Passive native-terminal telemetry for the new Minecart specialist."""

from __future__ import annotations

import re
import shutil
import time
from pathlib import Path
from typing import Any

from monitor.server import Monitor, shared_read


class OnPolicyMonitor(Monitor):
    def __init__(self, repo: Path, stage: str = "S"):
        super().__init__(repo)
        if stage not in ("S", "C"):
            raise ValueError("Unknown on-policy stage")
        self.stage = stage
        self.kind = "specialist" if stage == "S" else "conditional"
        self.root = repo / f"artifacts/minecart-onpolicy-{self.kind}-v1"
        self.runs = self.root / "runs"

    def directory(self, name: str) -> Path:
        if name != f"minecart-v0_{self.stage}_seed20264111":
            raise ValueError("Unknown on-policy job")
        return self.runs / name

    def snapshot(self) -> dict[str, Any]:
        with self.lock:
            if time.monotonic() - self.sampled < 3:
                return self.last_snapshot
            warnings: list[str] = []
            plan = (
                self.read_json(self.repo / f"configs/experiments/minecart_onpolicy_{self.kind}_v1.json", warnings) or {}
            )
            name = f"minecart-v0_{self.stage}_seed20264111"
            directory = self.directory(name)
            processes = self.processes()
            workers = [
                p
                for p in processes or []
                if ("run_minecart_onpolicy.py" if self.stage == "S" else "run_minecart_conditional.py")
                in (p.get("command") or "")
                and "--engineering" not in (p.get("command") or "")
                and str(self.repo).lower() in (p.get("command") or "").lower()
            ]
            alive = bool(workers) if processes is not None else None
            complete = self.read_json(directory / "complete.json", warnings) or {}
            manifest = self.read_json(directory / "manifest.json", warnings) or {}
            progress, stdout = self.log_progress(name)
            try:
                stderr = shared_read(self.root / f"{name}.stderr.log", 8000, tail=True)
            except FileNotFoundError:
                stderr = ""
            state = (
                "complete"
                if complete
                else "running"
                if alive
                else "unknown"
                if alive is None
                else "failed"
                if "Traceback (most recent call last)" in stderr
                else "interrupted"
                if stdout
                else "pending"
            )
            snapshots = [int(p.stem.removeprefix("resume_step")) for p in directory.glob("resume_step*.pt")]
            task = []
            for mode, gate in complete.get("gates", {}).items():
                for profile in gate.get("profiles", [gate]):
                    task.append(
                        {
                            "mode": mode,
                            "profile": profile.get("profile", 0),
                            "successes": profile["deliveries"],
                            "episodes": profile["episodes"],
                            "utility": profile["mean_utility"],
                        }
                    )
            budget = plan.get("training_interactions", 4000000)
            job = {
                "name": name,
                "arm": self.stage,
                "seed": plan.get("seed", 20264111),
                "state": state,
                "step": complete.get("training_interactions", progress.get("step", 0)),
                "budget": budget,
                "updates": complete.get("actor_updates", progress.get("updates")),
                "resume_step": max(snapshots) if snapshots else None,
                "task": task,
                "rate": progress.get("rate"),
                "pid": workers[-1]["pid"] if workers else None,
                "alive": alive,
                "heartbeat_unix": progress.get("updated_unix"),
            }
            counts = {
                key: int(state == key)
                for key in ["complete", "running", "stale", "starting", "failed", "interrupted", "pending", "unknown"]
            }
            disk = round(shutil.disk_usage(self.repo).free / 1024**3, 1)
            entropy = re.findall(r"entropy=([\d.]+) target=([\d.]+)", stdout)
            self.last_snapshot = {
                "observed_unix": time.time(),
                "study_id": plan.get("study_id"),
                "study_label": "Minecart / PPO " + ("specialist" if self.stage == "S" else "conditional32"),
                "state": state,
                "coordinator_alive": alive,
                "jobs": [job],
                "counts": counts,
                "total_steps": job["step"],
                "budget": budget,
                "gpu": self.hardware(),
                "disks_gib": {"workspace": disk},
                "warnings": warnings,
                "source_commit": manifest.get("provenance", {}).get("git_commit"),
                "progress_source": "append-only stdout; latest completed optimizer round",
                "entropy": entropy[-1] if entropy else None,
                "analysis": None,
            }
            self.sampled = time.monotonic()
            return self.last_snapshot

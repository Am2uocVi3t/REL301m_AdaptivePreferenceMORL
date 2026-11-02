"""Passive aggregate telemetry for three independent G workers."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from monitor.onpolicy import OnPolicyMonitor
from monitor.server import Monitor


class ConfirmationMonitor(Monitor):
    def __init__(self, repo: Path):
        super().__init__(repo)
        self.root = repo / "artifacts/minecart-onpolicy-confirmation-v1"
        self.runs = self.root / "runs"
        self.seeds = [20264311, 20264312, 20264313]
        self.children = [OnPolicyMonitor(repo, stage="G", seed=seed) for seed in self.seeds]

    def directory(self, name: str) -> Path:
        if name not in {f"minecart-v0_G_seed{seed}" for seed in self.seeds}:
            raise ValueError("Unknown confirmation job")
        return self.runs / name

    def snapshot(self) -> dict[str, Any]:
        with self.lock:
            if time.monotonic() - self.sampled < 3:
                return self.last_snapshot
            states = [child.snapshot() for child in self.children]
            jobs = [state["jobs"][0] for state in states]
            counts = {key: sum(state["counts"][key] for state in states) for key in states[0]["counts"]}
            failures = counts["failed"] + counts["interrupted"]
            state = (
                "complete"
                if counts["complete"] == 3
                else "draining"
                if failures and counts["running"]
                else "blocked"
                if failures
                else "running"
                if counts["running"]
                else "unknown"
                if counts["unknown"]
                else "pending"
            )
            self.last_snapshot = {
                **states[0],
                "study_label": "Minecart / PPO confirmation (3 seeds)",
                "state": state,
                "jobs": jobs,
                "counts": counts,
                "total_steps": sum(j["step"] or 0 for j in jobs),
                "budget": 12000000,
                "warnings": [w for s in states for w in s["warnings"]],
                "entropy": None,
            }
            self.sampled = time.monotonic()
            return self.last_snapshot

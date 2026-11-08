"""Repeat complete short CUDA learning traces before the finite main cohort."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import scripts.run_credit_assignment as runner


def main() -> None:
    original_root = runner.ROOT
    plan = json.loads(runner.PLAN.read_text())
    records = []
    for protocol in plan["protocols"]:
        repetitions = []
        for repeat in range(2):
            runner.ROOT = original_root / "qualification" / f"repeat{repeat}"
            path = runner.run(protocol, 20, 20261402, "cuda", smoke=True)
            repetitions.append(path)
        first, second = repetitions
        for name in ("complete.json", "training_episodes.json", "evaluations.json", "losses.json"):
            a, b = [json.loads((path / name).read_text()) for path in repetitions]
            if name == "complete.json":
                a.pop("wall_seconds")
                b.pop("wall_seconds")
            if a != b:
                raise AssertionError(f"Repeated-seed trace differs: {protocol} {name}")
        records.append({"protocol": protocol, "runs": [str(first), str(second)], "match": True})
    runner.ROOT = original_root
    runner.save_json(
        Path("research/qualification/credit_assignment_v1.json"),
        {
            "status": "pass",
            "device": "cuda",
            "seed": 20261402,
            "n": 20,
            "training_interactions_per_repetition": 6000,
            "updates_per_repetition": 251,
            "records": records,
            "scope": (
                "Same runtime/device exact initial and final parameter hashes, full episode summaries, "
                "loss samples and validation returns; not a task-learning claim"
            ),
        },
    )


if __name__ == "__main__":
    main()

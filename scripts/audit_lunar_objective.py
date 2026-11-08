"""Recompute the development positive control from its retained native traces."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    if not __debug__:
        raise RuntimeError("Evidence assertions must be enabled")
    evidence = Path("research/evidence/lunar_objective_diagnosis_v1.json")
    data = json.loads(evidence.read_text())
    plan = data["plan"]
    assert sha(Path("configs/experiments/lunar_objective_diagnosis_v1.json")) == data["plan_sha256"]
    spec = json.loads((Path(plan["package"]) / "config.json").read_text())["environments"]["lunar"]
    assert sha(Path(plan["package"]) / spec["weights_file"]) == spec["weights_sha256"] == data["model_sha256"]
    assert data["training_interactions"] == data["final_test_steps"] == 0
    assert len(data["records"]) == plan["expected_environment_episodes"] == 30
    initials: dict[int, list[np.ndarray]] = {}
    for record in data["records"]:
        path = Path(record["trace"])
        assert sha(path) == record["trace_sha256"]
        trace = json.loads(path.read_text())
        rewards, states = np.asarray(trace["native_rewards"]), np.asarray(trace["states"])
        assert rewards.shape == (record["steps"], 4) and states.shape == (record["steps"] + 1, 8)
        assert len(trace["actions"]) == record["steps"] and np.isfinite(rewards).all()
        initials.setdefault(record["seed"], []).append(states[0])
        np.testing.assert_allclose(rewards.sum(axis=0), record["native_raw_return"])
        assert record["native_plus100"] == bool(rewards[-1, 0] == 100 and record["terminated"])
        for gamma in plan["counterfactual_rescoring_gammas"]:
            scores = record["scores"][str(gamma)]
            vector = (rewards * np.power(gamma, np.arange(len(rewards)))[:, None]).sum(axis=0)
            scaled = vector * np.asarray(spec["reward_scale"])
            np.testing.assert_allclose(vector, scores["native_discounted_return"], rtol=1e-12, atol=1e-12)
            np.testing.assert_allclose(scaled, scores["scaled_discounted_return"], rtol=1e-12, atol=1e-12)
            for label, supplied in plan["model_preferences"].items():
                contributions = scaled * np.asarray(supplied or spec["default_weights"])
                np.testing.assert_allclose(contributions, scores["utilities"][label]["per_objective_contributions"])
                np.testing.assert_allclose(contributions.sum(), scores["utilities"][label]["total"])
    assert sum(record["steps"] for record in data["records"]) == data["diagnostic_steps"]
    for seed in plan["environment_seeds"]:
        assert len(initials[seed]) == 3
        for initial in initials[seed][1:]:
            np.testing.assert_array_equal(initial, initials[seed][0])
    receipt = {
        "status": "numeric_trace_audit_pass",
        "review_independence": "executor_numeric_checks_only",
        "evidence_sha256": sha(evidence),
        "episodes": 30,
        "diagnostic_steps": data["diagnostic_steps"],
        "training_interactions": 0,
        "final_test_steps": 0,
        "scope": (
            "All native traces, hashes, vector sums, four gamma rescorings, utilities and paired initial observations"
        ),
    }
    output = Path("research/qualification/lunar_objective_diagnosis_v1.json")
    output.write_bytes((json.dumps(receipt, indent=2) + "\n").encode())
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()

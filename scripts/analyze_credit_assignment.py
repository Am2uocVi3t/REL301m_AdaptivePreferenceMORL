"""Post-cohort numerical and provenance audit of the finite n-step study."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.evaluation.metrics import compute_hypervolume
from src.evaluation.protocol import load_protocol, protocol_hash, resolve_reference_point

ROOT = Path("artifacts/credit-assignment-v1")
PLAN = Path("configs/experiments/credit_assignment_v1.json")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path) -> Any:
    return json.loads(path.read_text())


def verify_training_source(commit: str, frozen: str) -> None:
    """Documentation/analysis commits may advance while unchanged workers run."""
    for path in (
        "src",
        "requirements.txt",
        "scripts/run_credit_assignment.py",
        "configs/protocols",
        str(PLAN).replace("\\", "/"),
    ):
        versions = [
            subprocess.check_output(["git", "rev-parse", f"{revision}:{path}"], text=True).strip()
            for revision in (commit, frozen)
        ]
        if versions[0] != versions[1]:
            raise ValueError(f"Training source changed: {path} at {commit}")


def main() -> None:
    if not __debug__:
        raise RuntimeError("Run the evidence audit without Python optimization flags")
    plan, execution = read(PLAN), read(ROOT / "execution_status.json")
    assert execution["plan_sha256"] == digest(PLAN)
    assert len(execution["jobs"]) == 12
    assert all(job["state"] == "complete" for job in execution["jobs"]), "Cohort still running or failed"
    full_records, summaries = [], []
    totals = dict(
        training_interactions=0,
        gradient_updates=0,
        validation_evaluation_steps=0,
        task_diagnostic_steps=0,
        final_test_steps=0,
    )
    for job in execution["jobs"]:
        directory = ROOT / "runs" / job["name"]
        manifest, complete = [read(directory / filename) for filename in ("manifest.json", "complete.json")]
        assert manifest["plan_sha256"] == digest(PLAN) and manifest["plan"] == plan
        verify_training_source(manifest["provenance"]["git_commit"], execution["source_commit"])
        assert manifest["provenance"]["git_dirty"] is False
        assert manifest["n"] == job["n"] and manifest["seed"] == job["seed"]
        protocol, preferences = load_protocol(job["protocol"], "validation")
        assert manifest["protocol_sha256"] == protocol_hash(protocol)
        assert complete["training_interactions"] == 500000 and complete["gradient_updates"] == 123751
        assert complete["replay_size"] == 200000 and complete["pending_transitions"] == 0
        assert complete["curriculum_evaluation_steps"] == complete["final_test_steps"] == 0
        episodes = read(directory / "training_episodes.json")
        assert sum(episode["steps"] for episode in episodes) == 500000
        assert sum(episode["completed"] for episode in episodes) == complete["episodes"]
        for episode in episodes:
            assert episode["completed"] == (episode["terminated"] or episode["truncated"])
            assert np.isfinite(episode["native_raw_return"]).all()
            assert np.isfinite(episode["scaled_discounted_return"]).all()
        evaluations = read(directory / "evaluations.json")
        assert [evaluation["step"] for evaluation in evaluations] == plan["checkpoints"]
        counted_validation = counted_task = 0
        checkpoint_metrics = []
        files = [
            directory / name
            for name in ("manifest.json", "complete.json", "training_episodes.json", "evaluations.json", "losses.json")
        ]
        for evaluation in evaluations:
            np.testing.assert_array_equal(evaluation["preferences"], preferences)
            raw = np.asarray(evaluation["validation"]["raw_episode_returns"])
            discounted = np.asarray(evaluation["validation"]["episode_returns"])
            lengths = np.asarray(evaluation["validation"]["episode_lengths"])
            assert raw.shape == discounted.shape == (32, 3, protocol["reward_dim"])
            assert lengths.shape == (32, 3) and np.all((lengths > 0) & (lengths <= 1000))
            assert np.isfinite(raw).all() and np.isfinite(discounted).all()
            np.testing.assert_allclose(discounted.mean(axis=1), evaluation["validation"]["mean_returns"], atol=1e-7)
            assert int(lengths.sum()) == evaluation["validation"]["evaluation_steps"]
            counted_validation += int(lengths.sum())
            task = evaluation["task"]
            assert len(task["records"]) == 20
            for pref_index, pref in enumerate(plan["task_preferences"][protocol["env_id"]]):
                cases = task["records"][pref_index * 10 : (pref_index + 1) * 10]
                assert [case["seed"] for case in cases] == plan["task_environment_seeds"]
                for case in cases:
                    np.testing.assert_allclose(case["preference"], pref)
                    assert case["terminated"] or case["truncated"]
                    assert sum(case["action_counts"]) == case["steps"]
                    np.testing.assert_allclose(
                        np.asarray(case["native_discounted_return"]) * protocol["reward_scale"],
                        case["scaled_discounted_return"],
                        rtol=2e-7,
                        atol=1e-7,
                    )
            assert sum(case["steps"] for case in task["records"]) == task["evaluation_steps"]
            counted_task += task["evaluation_steps"]
            cases = task["records"][:10]
            if protocol["env_id"] == "minecart-v0":
                task_successes = sum(case["ore_delivered"] for case in cases)
                native_positives = task_successes
            else:
                task_successes = sum(case["native_plus100"] and case["inside_pad_x"] for case in cases)
                native_positives = sum(case["native_plus100"] for case in cases)
            mean_returns = discounted.mean(axis=1)
            reference = resolve_reference_point(protocol)
            if reference is None:
                raise ValueError("Frozen hypervolume reference point is required")
            metric = {
                "step": evaluation["step"],
                "expected_utility": float((mean_returns * preferences).sum(axis=1).mean()),
                "hypervolume": compute_hypervolume(mean_returns, reference),
                "task_successes_of_10": task_successes,
                "native_positives_of_10": native_positives,
            }
            checkpoint_metrics.append(metric)
            checkpoint = directory / f"step{evaluation['step']}.pt"
            assert checkpoint.is_file()
            files.append(checkpoint)
        assert complete["validation_evaluation_steps"] == counted_validation
        assert complete["task_diagnostic_steps"] == counted_task
        threshold = 5 if protocol["env_id"] == "minecart-v0" else 8
        summaries.append(
            {
                "env_id": protocol["env_id"],
                "n": job["n"],
                "seed": job["seed"],
                "metrics": checkpoint_metrics,
                "final_task_gate_pass": checkpoint_metrics[-1]["task_successes_of_10"] >= threshold,
            }
        )
        full_records.append(
            {
                "job": job,
                "manifest": manifest,
                "complete": complete,
                "evaluations": evaluations,
                "files": {str(path): digest(path) for path in files},
            }
        )
        for key in totals:
            totals[key] += complete[key]
    assert totals["training_interactions"] == 6000000 and totals["gradient_updates"] == 1485012
    effects = []
    for protocol_path in plan["protocols"]:
        env_id = read(Path(protocol_path))["env_id"]
        for seed in plan["seeds"]:
            paired = [
                record
                for record in full_records
                if record["manifest"]["protocol"]["env_id"] == env_id and record["job"]["seed"] == seed
            ]
            assert len(paired) == 2
            assert (
                paired[0]["manifest"]["initial_parameter_sha256"] == paired[1]["manifest"]["initial_parameter_sha256"]
            )
            one, twenty = [
                next(
                    summary
                    for summary in summaries
                    if summary["env_id"] == env_id and summary["seed"] == seed and summary["n"] == n
                )
                for n in (1, 20)
            ]
            effects.append(
                {
                    "env_id": env_id,
                    "seed": seed,
                    "expected_utility_delta_n20_minus_n1": twenty["metrics"][-1]["expected_utility"]
                    - one["metrics"][-1]["expected_utility"],
                    "task_success_delta_of_10": twenty["metrics"][-1]["task_successes_of_10"]
                    - one["metrics"][-1]["task_successes_of_10"],
                }
            )
    result = {
        "study_id": plan["study_id"],
        "audit": "numeric_and_provenance_pass",
        "review_independence": "executor_numeric_check_only",
        "source_commit": execution["source_commit"],
        "plan_sha256": digest(PLAN),
        "totals": totals,
        "summaries": summaries,
        "paired_effects": effects,
        "records": full_records,
        "limits": (
            "Validation-only development screen; no original scientific gate unlock, "
            "no best-checkpoint selection, no significance claim from three pairs"
        ),
    }
    destination = Path("research/evidence/credit_assignment_v1.json")
    destination.write_bytes((json.dumps(result, indent=2, allow_nan=False) + "\n").encode())
    print(json.dumps({"totals": totals, "summaries": summaries, "paired_effects": effects}, indent=2))


if __name__ == "__main__":
    main()

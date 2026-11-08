"""Audit the complete P2 factorial without selecting intermediate checkpoints."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import torch

from scripts.audit_preference_transfer import audit_traces
from scripts.diagnose_policy_extraction import read, sha
from scripts.run_credit_assignment_recoverable import parameter_hash
from src.evaluation.metrics import compute_hypervolume
from src.evaluation.protocol import load_protocol, resolve_reference_point, resolve_reward_scale
from src.models.q_network import VectorQNetwork
from src.utils.training_recovery import atomic_json

PLAN = Path("configs/experiments/preference_recovery_p2_v1.json")
ROOT = Path("artifacts/preference-recovery-p2-v1")


def main() -> None:
    plan = read(PLAN)
    execution = read(ROOT / "execution_status.json")
    assert execution["plan_sha256"] == sha(PLAN)
    expected_jobs = {(seed, arm) for seed in plan["seeds"] for arm in plan["factorial_arms"]}
    assert {(j["seed"], j["arm"]) for j in execution["jobs"]} == expected_jobs
    assert len(execution["jobs"]) == 12 and all(j["state"] == "complete" for j in execution["jobs"])
    receipt = read(Path("research/qualification/preference_recovery_p2_v1.json"))
    assert receipt["status"] == "pass" and receipt["plan_sha256"] == sha(PLAN)
    assert all(sha(Path(p)) == digest for p, digest in receipt["source_sha256"].items())
    summaries, records = [], []
    totals = dict(
        training_interactions=0,
        gradient_updates=0,
        validation_evaluation_steps=0,
        task_diagnostic_steps=0,
        final_test_steps=0,
    )
    for job in execution["jobs"]:
        directory = Path(job["directory"])
        manifest, complete = [read(directory / f) for f in ("manifest.json", "complete.json")]
        assert manifest["plan_sha256"] == complete["plan_sha256"] == sha(PLAN)
        assert manifest["plan"] == plan and manifest["arm"] == complete["arm"] == job["arm"]
        assert manifest["seed"] == job["seed"] and manifest["provenance"]["git_dirty"] is False
        binding = manifest["recovery_binding"]
        assert binding["runner_sha256"] == sha(Path("scripts/run_preference_recovery.py"))
        assert binding["core_sha256"] == sha(Path("scripts/preference_recovery_core.py"))
        assert all(sha(Path(p)) == digest for p, digest in binding["source_files"].items())
        assert complete["training_interactions"] == 500000 and complete["gradient_updates"] == 123751
        assert complete["replay_size"] == 200000 and complete["pending_transitions"] == 0
        assert complete["final_test_steps"] == complete["curriculum_evaluation_steps"] == 0
        protocol, preferences = load_protocol(job["protocol"], "validation")
        assert manifest["protocol"] == protocol
        scale = resolve_reward_scale(protocol)
        episodes = read(directory / "training_episodes.json")
        assert sum(r["steps"] for r in episodes) == 500000
        assert sum(r["completed"] for r in episodes) == complete["episodes"]
        assert all(np.isfinite(r["scaled_discounted_return"]).all() for r in episodes)
        evaluations = read(directory / "evaluations.json")
        assert [e["step"] for e in evaluations] == plan["checkpoints"]
        metrics = []
        validation_steps = task_steps = 0
        for evaluation in evaluations:
            np.testing.assert_array_equal(evaluation["preferences"], preferences)
            validation = evaluation["validation"]
            raw, discounted = [np.asarray(validation[k]) for k in ("raw_episode_returns", "episode_returns")]
            lengths = np.asarray(validation["episode_lengths"])
            assert raw.shape == discounted.shape == (32, 3, 3)
            assert lengths.shape == (32, 3) and ((lengths > 0) & (lengths <= 1000)).all()
            assert np.isfinite(raw).all() and np.isfinite(discounted).all()
            np.testing.assert_allclose(discounted.mean(1), validation["mean_returns"], atol=1e-7)
            np.testing.assert_allclose(raw / scale, validation["native_raw_episode_returns"], atol=1e-7)
            np.testing.assert_allclose(discounted / scale, validation["native_discounted_episode_returns"], atol=1e-7)
            assert lengths.sum() == validation["evaluation_steps"]
            validation_steps += int(lengths.sum())
            task = evaluation["task"]
            if evaluation["step"] != 500000:
                assert task["records"] == [] and task["evaluation_steps"] == 0
            else:
                assert len(task["records"]) == 20
                assert {(r["preference_index"], r["seed"]) for r in task["records"]} == {
                    (p, s) for p in range(2) for s in plan["task_environment_seeds"]
                }
                for r in task["records"]:
                    np.testing.assert_allclose(
                        r["preference"], plan["task_preferences"]["minecart-v0"][r["preference_index"]]
                    )
                audit_traces(
                    {
                        "model": {"reward_scale": scale, "env_id": "minecart-v0"},
                        "diagnostic_steps": task["evaluation_steps"],
                        "records": task["records"],
                    },
                    plan,
                )
            task_steps += task["evaluation_steps"]
            checkpoint_path = directory / f"step{evaluation['step']}.pt"
            saved = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
            model = VectorQNetwork(**saved["architecture"])
            model.load_state_dict(saved["model_state_dict"])
            assert parameter_hash(model) == evaluation["parameter_sha256"]
            assert saved["counters"]["training_interactions"] == evaluation["step"]
            reference = resolve_reference_point(protocol)
            assert reference is not None
            means = discounted.mean(1)
            metrics.append(
                {
                    "step": evaluation["step"],
                    "expected_utility": float((means * preferences).sum(1).mean()),
                    "hypervolume": compute_hypervolume(means, reference),
                    "checkpoint_sha256": sha(checkpoint_path),
                }
            )
        assert complete["validation_evaluation_steps"] == validation_steps
        assert complete["task_diagnostic_steps"] == task_steps
        task = evaluations[-1]["task"]["records"]
        profile = []
        for index in range(2):
            cases = sorted([r for r in task if r["preference_index"] == index], key=lambda r: r["seed"])
            profile.append(
                {
                    "successes_of_10": sum(r["ore_delivered"] for r in cases),
                    "utility": float(np.mean([r["utility"] for r in cases])),
                    "case_utilities": [r["utility"] for r in cases],
                }
            )
        summaries.append(
            {
                "seed": job["seed"],
                "arm": job["arm"],
                "metrics": metrics,
                "profiles": profile,
                "initial_hash": manifest["initial_parameter_sha256"],
            }
        )
        files = [
            directory / n
            for n in ("manifest.json", "complete.json", "training_episodes.json", "evaluations.json", "losses.json")
        ]
        records.append(
            {
                "job": job,
                "manifest": manifest,
                "complete": complete,
                "evaluations": evaluations,
                "file_sha256": {str(p): sha(p) for p in files},
            }
        )
        for key in totals:
            totals[key] += complete[key]
    assert totals["training_interactions"] == 6000000 and totals["gradient_updates"] == 1485012
    assert totals["validation_evaluation_steps"] <= plan["validation_max_steps"]
    assert totals["task_diagnostic_steps"] <= plan["task_max_steps"]
    effects: list[dict[str, Any]] = []
    passing = []
    for arm in ("B", "C", "D"):
        arm_rows = []
        for seed in plan["seeds"]:
            pair = {r["arm"]: r for r in summaries if r["seed"] == seed}
            assert len({r["initial_hash"] for r in pair.values()}) == 1
            differences = [pair[arm]["profiles"][i]["utility"] - pair["A"]["profiles"][i]["utility"] for i in range(2)]
            row = {
                "arm": arm,
                "seed": seed,
                "paired_profile_utility_differences_vs_A": differences,
                "successes_of_10": [p["successes_of_10"] for p in pair[arm]["profiles"]],
                "pass": all(p["successes_of_10"] >= 8 for p in pair[arm]["profiles"])
                and all(d > 0 for d in differences),
            }
            effects.append(row)
            arm_rows.append(row)
        if all(r["pass"] for r in arm_rows):
            passing.append(arm)
    factorial = []
    for seed in plan["seeds"]:
        values = {r["arm"]: r["metrics"][-1]["expected_utility"] for r in summaries if r["seed"] == seed}
        factorial.append(
            {
                "seed": seed,
                "relabel_main_effect": ((values["B"] - values["A"]) + (values["D"] - values["C"])) / 2,
                "auxiliary_main_effect": ((values["C"] - values["A"]) + (values["D"] - values["B"])) / 2,
                "interaction_difference": values["D"] - values["C"] - values["B"] + values["A"],
            }
        )
    atomic_json(
        ROOT / "analysis.json",
        {
            "study_id": plan["study_id"],
            "audit": "numeric_and_provenance_pass",
            "review_independence": "executor_only",
            "totals": totals,
            "plan_sha256": sha(PLAN),
            "source_commit": execution["source_commit"],
            "summaries": summaries,
            "paired_effects": effects,
            "factorial_effects": factorial,
            "passing_arms": passing,
            "records": records,
            "next": ("Freeze independent confirmation if a method passes; otherwise stop this finite study."),
            "original_gate_unlock": False,
        },
    )
    print({"totals": totals, "passing_arms": passing})


if __name__ == "__main__":
    if not __debug__:
        raise RuntimeError("Audit assertions must be enabled")
    main()

"""Verify every native trace and summarize the fixed policy-extraction matrix."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

from src.utils.training_recovery import atomic_json

ROOT = Path("artifacts/policy-extraction-diagnosis-v1")
PLAN = Path("configs/experiments/policy_extraction_diagnosis_v1.json")


def read(path: Path) -> Any:
    return json.loads(path.read_text())


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    if not __debug__:
        raise RuntimeError("Evidence checks must be enabled")
    plan = read(PLAN)
    status = read(ROOT / "execution_status.json")
    if status["state"] != "complete" or not all(j["state"] == "complete" for j in status["jobs"]):
        raise ValueError("Frozen diagnostic matrix is not complete")
    assert status["plan_sha256"] == sha(PLAN)
    models, tables, probes, conditioning = [], [], [], []
    provenance_exceptions = []
    episode_count = steps = 0
    for spec in plan["models"]:
        path = ROOT / "runs" / spec["name"] / "complete.json"
        data = read(path)
        assert data["plan_sha256"] == sha(PLAN) and data["replication_pass"]
        assert data["training_interactions"] == data["gradient_updates"] == data["final_test_steps"] == 0
        assert sha(Path(spec["checkpoint"])) == spec["checkpoint_sha256"]
        if data["provenance"]["git_dirty"]:
            context = read(Path("research/qualification/policy_extraction_source_context_v1.json"))
            if spec["name"] not in context["affected_completed_jobs"]:
                raise ValueError("An unaccounted dirty-source diagnostic requires audit")
            for filename, expected in context["frozen_actor_files"].items():
                assert sha(Path(filename)) == expected, filename
            provenance_exceptions.append(
                {
                    "model": spec["name"],
                    "git_dirty": True,
                    "context": "Non-executed postprocessing source/config edits; frozen actor dependencies verified",
                    "receipt": "research/qualification/policy_extraction_source_context_v1.json",
                }
            )
        # Analysis/docs may advance HEAD; actual actor/env/model code must be identical.
        for source in ("src", "scripts/diagnose_policy_extraction.py", str(PLAN).replace("\\", "/")):
            commits = [data["provenance"]["git_commit"], "b7ad03f"]
            blobs = [subprocess.check_output(["git", "rev-parse", f"{c}:{source}"], text=True).strip() for c in commits]
            assert blobs[0] == blobs[1], source
        groups: dict[tuple[int, str], list[dict[str, Any]]] = defaultdict(list)
        initials: dict[tuple[int, int], set[str]] = defaultdict(set)
        supported: dict[int, list[bool]] = defaultdict(list)
        calibrations: dict[tuple[int, str], list[dict[str, Any]]] = defaultdict(list)
        scale = np.asarray(data["model"]["reward_scale"])
        for record in data["records"]:
            trace_path = Path(record["trace"])
            assert sha(trace_path) == record["trace_sha256"]
            with np.load(trace_path, allow_pickle=False) as trace:
                rewards = trace["native_rewards"]
                actions = trace["actions"]
                assert rewards.shape == (record["steps"], len(scale))
                assert trace["states"].shape[0] == len(actions) + 1 == record["steps"] + 1
                assert np.isfinite(rewards).all() and np.isfinite(trace["probe_q"]).all()
                np.testing.assert_array_equal(
                    np.bincount(actions, minlength=len(record["action_counts"])), record["action_counts"]
                )
                raw = rewards.sum(0)
                discounted = (rewards * np.power(plan["gamma"], np.arange(len(actions)))[:, None]).sum(0)
                np.testing.assert_allclose(raw, record["native_raw_return"], atol=1e-9)
                np.testing.assert_allclose(discounted, record["native_discounted_return"], atol=1e-9)
                np.testing.assert_allclose(discounted * scale, record["scaled_discounted_return"], atol=1e-9)
                np.testing.assert_allclose(np.dot(discounted * scale, record["preference"]), record["utility"])
                assert record["terminated"] or record["truncated"]
                if spec["env_id"] == "minecart-v0":
                    assert record["ore_delivered"] == bool(np.any(raw[:2] > 0))
                else:
                    assert record["native_plus100"] == bool(raw[0] > 0 and record["terminated"])
                state_hash = hashlib.sha256(trace["states"][0].astype(np.float32).tobytes()).hexdigest()
                assert state_hash == record["initial_state_sha256"]
                if record["block"] == "paired_extraction":
                    pref_index = record["preference_index"]
                    key = (pref_index, record["policy"])
                    groups[key].append(record)
                    initials[(pref_index, record["seed"])].add(state_hash)
                    if record["policy"] == "mean_greedy":
                        has_support = (trace["probe_head_actions"] == trace["probe_mean_actions"][:, None]).any(1)
                        supported[pref_index].extend(has_support.tolist())
                    if record["policy"].startswith("head"):
                        head = int(record["policy"][4])
                        predicted = trace["probe_q"][0, head, actions[0]].astype(np.float64)
                        actual = np.asarray(record["scaled_discounted_return"])
                        calibrations[key].append(
                            {
                                "predicted_vector": predicted,
                                "observed_vector": actual,
                                "scalar_bias": float(np.dot(predicted - actual, record["preference"])),
                            }
                        )
            episode_count += 1
            steps += record["steps"]
        for values in initials.values():
            assert len(values) == 1
        expected_policies = [*plan["policies"]]
        if spec["env_id"] == "mo-lunar-lander-v3":
            expected_policies.append(plan["lunar_positive_control"])
        mean_vectors = {}
        for pref_index, preference in enumerate(plan["preferences"][spec["env_id"]]):
            for policy in expected_policies:
                cases = groups[(pref_index, policy)]
                assert len(cases) == 10 and [r["seed"] for r in cases] == plan["development_environment_seeds"]
                np.testing.assert_allclose([r["preference"] for r in cases], [preference] * 10)
                success = (
                    sum(r["ore_delivered"] for r in cases)
                    if spec["env_id"] == "minecart-v0"
                    else sum(r["native_plus100"] and r["inside_pad_x"] for r in cases)
                )
                entry = {
                    "model": spec["name"],
                    "env_id": spec["env_id"],
                    "n": spec["n"],
                    "training_seed": spec["training_seed"],
                    "preference_index": pref_index,
                    "preference": preference,
                    "policy": policy,
                    "successes_of_10": success,
                    "mean_utility": float(np.mean([r["utility"] for r in cases])),
                    "mean_steps": float(np.mean([r["steps"] for r in cases])),
                    "mean_native_raw_return": np.mean([r["native_raw_return"] for r in cases], axis=0),
                }
                if spec["env_id"] == "minecart-v0":
                    entry["cargo_positive_of_10"] = sum(r["cargo_peak"] > 0 for r in cases)
                else:
                    entry["native_plus100_of_10"] = sum(r["native_plus100"] for r in cases)
                if (pref_index, policy) in calibrations:
                    samples = calibrations[(pref_index, policy)]
                    entry["initial_head_mc_diagnostic"] = {
                        "mean_predicted_vector": np.mean([s["predicted_vector"] for s in samples], axis=0),
                        "mean_observed_vector": np.mean([s["observed_vector"] for s in samples], axis=0),
                        "mean_scalar_bias": float(np.mean([s["scalar_bias"] for s in samples])),
                    }
                tables.append(entry)
                if policy == "mean_greedy":
                    mean_vectors[pref_index] = np.mean([r["scaled_discounted_return"] for r in cases], axis=0)
            probes.append(
                {
                    "model": spec["name"],
                    "preference_index": pref_index,
                    "mean_trajectory_probe_count": len(supported[pref_index]),
                    "mean_action_not_any_head_argmax_fraction": 1 - float(np.mean(supported[pref_index])),
                }
            )
        for target_index, w in enumerate(plan["preferences"][spec["env_id"]]):
            scores = [float(np.dot(vector, w)) for vector in mean_vectors.values()]
            conditioning.append(
                {
                    "model": spec["name"],
                    "target_preference_index": target_index,
                    "own_mean_policy_utility": scores[target_index],
                    "all_fixed_source_preference_utilities": scores,
                    "empirical_conditioning_gap": max(scores) - scores[target_index],
                    "scope": (
                        "Best mean over ten cases among predeclared mean-policy preferences; "
                        "exploratory reference, not true regret or deployment selection"
                    ),
                }
            )
        models.append(
            {
                "model": spec,
                "worker_result_sha256": sha(path),
                "replay_audit": data["replay_audit"],
                "provenance": data["provenance"],
                "records": data["records"],
            }
        )
    assert episode_count == plan["expected_episodes"] and steps <= plan["maximum_environment_steps"]
    result = {
        "study_id": plan["study_id"],
        "audit": "trace_numeric_and_source_pass",
        "review_independence": "executor_only",
        "plan_sha256": sha(PLAN),
        "episodes": episode_count,
        "diagnostic_steps": steps,
        "training_interactions": 0,
        "gradient_updates": 0,
        "final_test_steps": 0,
        "tables": tables,
        "same_state_probes": probes,
        "exploratory_conditioning_rescoring": conditioning,
        "models": models,
        "provenance_exceptions": provenance_exceptions,
    }
    atomic_json(Path("research/evidence/policy_extraction_diagnosis_v1.json"), result)
    print(json.dumps({"episodes": episode_count, "diagnostic_steps": steps, "audit": result["audit"]}))


if __name__ == "__main__":
    main()

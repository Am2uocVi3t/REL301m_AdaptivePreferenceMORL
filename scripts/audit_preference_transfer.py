"""Audit P1 traces and predeclared gates; engineering qualification is separate."""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import torch

from scripts.diagnose_policy_extraction import read, rollout, sha
from scripts.run_preference_transfer import PLAN, ROOT, GPIMeanQ
from src.models.q_network import VectorQNetwork
from src.utils.training_recovery import atomic_json

RECEIPT = Path("research/qualification/preference_transfer_p1_v1.json")
EVIDENCE = Path("research/evidence/preference_transfer_p1_v1.json")


def actor_hashes() -> dict[str, str]:
    paths = [
        *Path("src").rglob("*.py"),
        Path("scripts/diagnose_policy_extraction.py"),
        Path("scripts/run_preference_transfer.py"),
        Path("scripts/run_preference_transfer_cohort.py"),
        Path("scripts/start_preference_transfer.ps1"),
        Path(__file__),
        PLAN,
    ]
    return {p.as_posix(): sha(p) for p in paths}


def audit_traces(data: dict[str, Any], plan: dict[str, Any]) -> None:
    scale = np.asarray(data["model"]["reward_scale"])
    initials: dict[tuple[int, int], set[str]] = defaultdict(set)
    for r in data["records"]:
        assert sha(Path(r["trace"])) == r["trace_sha256"]
        with np.load(r["trace"], allow_pickle=False) as t:
            rewards = t["native_rewards"]
            assert rewards.shape == (r["steps"], len(scale))
            assert len(t["states"]) == r["steps"] + 1
            assert np.isfinite(rewards).all() and np.isfinite(t["probe_q"]).all()
            raw = rewards.sum(0)
            discounted = (rewards * np.power(plan["gamma"], np.arange(len(rewards)))[:, None]).sum(0)
            np.testing.assert_allclose(raw, r["native_raw_return"], atol=1e-9)
            np.testing.assert_allclose(discounted, r["native_discounted_return"], atol=1e-9)
            np.testing.assert_allclose(discounted * scale, r["scaled_discounted_return"], atol=1e-9)
            np.testing.assert_allclose(np.dot(discounted * scale, r["preference"]), r["utility"])
            np.testing.assert_array_equal(
                np.bincount(t["actions"], minlength=len(r["action_counts"])), r["action_counts"]
            )
            assert r["terminated"] or r["truncated"]
            if data["model"]["env_id"] == "minecart-v0":
                assert r["ore_delivered"] == bool(np.any(raw[:2] > 0))
            else:
                assert r["native_plus100"] == bool(raw[0] > 0 and r["terminated"])
            import hashlib

            initial = hashlib.sha256(t["states"][0].astype(np.float32).tobytes()).hexdigest()
            assert initial == r["initial_state_sha256"]
            initials[(r["preference_index"], r["seed"])].add(initial)
    assert all(len(v) == 1 for v in initials.values())
    assert data["diagnostic_steps"] == sum(r["steps"] for r in data["records"])


def qualify() -> None:
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    plan = read(PLAN)
    models, episodes, steps, probe_count = [], 0, 0, 0
    for name in ("minecart-v0_n20_seed20261211", "mo-lunar-lander-v3_n1_seed20261211"):
        data = read(ROOT / "qualification" / name / "complete.json")
        assert data["qualify"] and data["plan_sha256"] == sha(PLAN)
        audit_traces(data, plan)
        spec = data["model"]
        assert sha(Path(spec["checkpoint"])) == spec["checkpoint_sha256"]
        checkpoint = torch.load(spec["checkpoint"], map_location="cpu", weights_only=True)
        model = VectorQNetwork(**checkpoint["architecture"]).to("cuda")
        model.load_state_dict(checkpoint["model_state_dict"])
        model.eval().requires_grad_(False)
        bank = torch.tensor(data["source_bank"], device="cuda")
        gpi = GPIMeanQ(model, bank).eval()
        replication_dir = ROOT / "qualification_replication" / name
        replication_dir.mkdir(parents=True, exist_ok=True)
        with torch.inference_mode():
            for r in data["records"]:
                if r["policy"] == "mean_greedy":
                    replica = rollout(
                        model,
                        spec,
                        plan,
                        "mean_greedy",
                        r["preference"],
                        r["seed"],
                        replication_dir / f"pref{r['preference_index']}.npz",
                        "cuda",
                    )
                    for k in ("steps", "action_counts", "native_raw_return", "native_discounted_return"):
                        np.testing.assert_array_equal(replica[k], r[k])
                    episodes += 1
                    steps += replica["steps"]
                with np.load(r["trace"], allow_pickle=False) as trace:
                    for probe_index, step in enumerate(trace["probe_steps"]):
                        state = torch.tensor(trace["states"][step], device="cuda")[None]
                        target = torch.tensor(r["preference"], dtype=torch.float32, device="cuda")
                        if r["policy"].startswith("gpi_"):
                            # Independent source-by-source calls, not the adapter's batched path.
                            qs = torch.stack([model(state, w[None])[:, 0] for w in bank], 1)
                            expected = torch.matmul(qs.mean(0), target).max(0).values
                            observed = torch.matmul(gpi(state, target[None])[:, 0].mean(0), target)
                            torch.testing.assert_close(observed, expected, rtol=1e-5, atol=1e-6)
                        else:
                            observed = torch.matmul(model(state, target[None])[:, 0].mean(0), target)
                        retained = torch.tensor(trace["probe_q"][probe_index], device="cuda")
                        torch.testing.assert_close(torch.matmul(retained.mean(0), target), observed, rtol=0, atol=0)
                        assert int(observed.argmax()) == int(trace["probe_mean_actions"][probe_index])
                        probe_count += 1
        episodes += len(data["records"])
        steps += data["diagnostic_steps"]
        models.append(name)
    atomic_json(
        RECEIPT,
        {
            "study_id": plan["study_id"],
            "status": "pass",
            "plan_sha256": sha(PLAN),
            "source_files": actor_hashes(),
            "models": models,
            "engineering_episodes": episodes,
            "engineering_steps": steps,
            "independent_probe_equations_checked": probe_count,
            "checks": [
                "trace numeric audit",
                "exact baseline replication",
                "literal source-bank GPI",
                "checkpoint immutable",
            ],
            "review_independence": "executor_only",
            "training_interactions": 0,
            "final_test_steps": 0,
        },
    )


def main() -> None:
    plan = read(PLAN)
    status = read(ROOT / "execution_status.json")
    assert status["state"] == "complete" and all(j["state"] == "complete" for j in status["jobs"])
    receipt = read(RECEIPT)
    assert receipt["status"] == "pass" and receipt["plan_sha256"] == sha(PLAN)
    assert receipt["source_files"] == actor_hashes()
    tables, models = [], []
    episodes = steps = 0
    for spec in plan["models"]:
        data = read(ROOT / "runs" / spec["name"] / "complete.json")
        assert not data["qualify"] and data["plan_sha256"] == sha(PLAN)
        assert sha(Path(spec["checkpoint"])) == spec["checkpoint_sha256"]
        assert data["training_interactions"] == data["gradient_updates"] == data["final_test_steps"] == 0
        assert not data["provenance"]["git_dirty"] and not data["end_provenance"]["git_dirty"]
        assert data["provenance"]["git_commit"] == data["end_provenance"]["git_commit"]
        audit_traces(data, plan)
        expected = {
            (p, s, policy)
            for p in range(2)
            for s in plan["development_environment_seeds"]
            for policy in plan["policies"]
        }
        actual = {(r["preference_index"], r["seed"], r["policy"]) for r in data["records"]}
        assert expected == actual and len(data["records"]) == len(expected)
        records = {(r["preference_index"], r["seed"], r["policy"]): r for r in data["records"]}
        for index in range(2):
            for policy in plan["policies"]:
                rows = [records[index, s, policy] for s in plan["development_environment_seeds"]]
                success = [
                    bool(r["ore_delivered"])
                    if spec["env_id"] == "minecart-v0"
                    else bool(r["native_plus100"] and r["inside_pad_x"])
                    for r in rows
                ]
                differences = {
                    ref: [r["utility"] - records[index, r["seed"], ref]["utility"] for r in rows]
                    for ref in ("mean_greedy", "mean_eps005")
                }
                tables.append(
                    {
                        "model": spec["name"],
                        "env_id": spec["env_id"],
                        "n": spec["n"],
                        "training_seed": spec["training_seed"],
                        "preference_index": index,
                        "policy": policy,
                        "successes_of_10": sum(success),
                        "utility": float(np.mean([r["utility"] for r in rows])),
                        "native_raw_return_mean": np.mean([r["native_raw_return"] for r in rows], 0),
                        "scaled_discounted_return_mean": np.mean([r["scaled_discounted_return"] for r in rows], 0),
                        "paired_utility_differences": differences,
                        "paired_utility_mean": {k: float(np.mean(v)) for k, v in differences.items()},
                    }
                )
        episodes += len(data["records"])
        steps += data["diagnostic_steps"]
        models.append(data)
    assert episodes == plan["expected_episodes"] and steps <= plan["maximum_environment_steps"]
    gates = []
    for env_id in plan["preferences"]:
        for n in (1, 20):
            for policy in plan["policies"][1:]:
                task_profiles = (0, 1) if env_id == "minecart-v0" else (0,)
                rows = [
                    r
                    for r in tables
                    if r["env_id"] == env_id
                    and r["n"] == n
                    and r["policy"] == policy
                    and r["preference_index"] in task_profiles
                ]
                passed = len(rows) == 3 * len(task_profiles) and all(
                    r["successes_of_10"] >= 8 and r["paired_utility_mean"]["mean_greedy"] > 0 for r in rows
                )
                gates.append({"env_id": env_id, "n": n, "policy": policy, "pass": passed})
    atomic_json(
        EVIDENCE,
        {
            "study_id": plan["study_id"],
            "audit": "trace_numeric_and_source_pass",
            "review_independence": "executor_only",
            "plan_sha256": sha(PLAN),
            "episodes": episodes,
            "diagnostic_steps": steps,
            "training_interactions": 0,
            "gradient_updates": 0,
            "final_test_steps": 0,
            "gates": gates,
            "tables": tables,
            "models": models,
        },
    )
    print({"episodes": episodes, "steps": steps, "gates": gates})


if __name__ == "__main__":
    if not __debug__:
        raise RuntimeError("Audit assertions must be enabled")
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--qualify", action="store_true")
    args = parser.parse_args()
    qualify() if args.qualify else main()

"""Fail-closed numerical/source audit of the completed, fixed Envelope cohort."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import torch

from src.evaluation.metrics import compute_expected_utility, compute_hypervolume
from src.evaluation.protocol import load_protocol, protocol_hash
from src.utils.provenance import write_json


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(root: Path, plan_path: Path) -> dict[str, Any]:
    plan = json.loads(plan_path.read_text())
    protocol, weights = load_protocol(plan["protocol"], "validation")
    rows = []
    manifests = []
    for seed in plan["seeds"]:
        directory = root / f"seed{seed}"
        manifest_path = directory / "run_manifest.json"
        manifest = json.loads(manifest_path.read_text())
        expected_updates = (plan["training_interactions"] - plan["agent"]["learning_starts"] + 1) * plan["agent"][
            "gradient_updates"
        ]
        if not (
            manifest["status"] == "complete"
            and manifest["smoke"] is False
            and manifest["seed"] == seed
            and manifest["plan_sha256"] == sha(plan_path)
            and manifest["plan"] == plan
            and manifest["protocol"] == protocol
            and manifest["protocol_sha256"] == protocol_hash(protocol)
            and manifest["training_interactions"] == plan["training_interactions"]
            and manifest["gradient_updates"] == expected_updates
            and manifest["curriculum_steps"] == manifest["final_test_steps"] == 0
        ):
            raise ValueError(f"Incomplete or identity/budget mismatch: {manifest_path}")
        checkpoints = plan["validation_checkpoints"]
        if len(manifest["validation_artifacts"]) != len(checkpoints):
            raise ValueError("Missing/extra checkpoint evaluations")
        steps = 0
        for step, identity in zip(checkpoints, manifest["validation_artifacts"], strict=True):
            path = directory / f"validation_step{step}.json"
            result = json.loads(path.read_text())
            model_path = directory / f"step{step}.tar"
            if sha(path) != identity["sha256"] or sha(model_path) != result["checkpoint_sha256"]:
                raise ValueError("Changed validation or model file")
            checkpoint = torch.load(model_path, map_location="cpu", weights_only=True)
            if not all(torch.isfinite(value).all() for value in checkpoint["q_net_state_dict"].values()):
                raise ValueError("Non-finite learned parameters")
            raw = np.asarray(result["raw_episode_returns"])
            returns = np.asarray(result["episode_returns"])
            lengths = np.asarray(result["episode_lengths"])
            expected_shape = (len(weights), plan["episodes_per_preference"], protocol["reward_dim"])
            if raw.shape != expected_shape or returns.shape != expected_shape or lengths.shape != expected_shape[:2]:
                raise ValueError("Episode shape mismatch")
            if not (np.isfinite(raw).all() and np.isfinite(returns).all() and (lengths > 0).all()):
                raise ValueError("Invalid episode vectors/lengths")
            np.testing.assert_array_equal(result["preferences"], weights)
            if result["split"] != "validation" or result["evaluation_seed"] != plan["evaluation_seed"]:
                raise ValueError("Evaluation split/seed mismatch")
            ended = np.asarray(result["terminated"], dtype=bool) | np.asarray(result["truncated"], dtype=bool)
            if ended.shape != lengths.shape or not ended.all():
                raise ValueError("Episode end flags missing")
            if result["training_interactions"] != step or result["evaluation_steps"] != int(lengths.sum()):
                raise ValueError("Evaluation counter mismatch")
            expected_at_step = (step - plan["agent"]["learning_starts"] + 1) * plan["agent"]["gradient_updates"]
            if result["gradient_updates"] != expected_at_step:
                raise ValueError("Checkpoint update budget mismatch")
            optimizer_states = checkpoint["q_net_optimizer_state_dict"]["state"].values()
            if not optimizer_states or not all(int(state["step"]) == expected_at_step for state in optimizer_states):
                raise ValueError("Saved optimizer disagrees with declared update count")
            hv = compute_hypervolume(returns.mean(axis=1), np.asarray(protocol["reference_point"]))
            eu = compute_expected_utility(returns.mean(axis=1), weights)
            np.testing.assert_allclose(
                [hv, eu], [result["hypervolume"], result["expected_utility"]], rtol=1e-6, atol=1e-8
            )
            ore = (raw[:, :, :2] > 0).sum(axis=(0, 1)).tolist()
            if ore != result["ore_positive_episodes"]:
                raise ValueError("Ore-positive count mismatch")
            steps += result["evaluation_steps"]
            rows.append(
                {
                    "seed": seed,
                    "step": step,
                    "ore_positive_episodes": ore,
                    "hypervolume": hv,
                    "expected_utility": eu,
                    "evaluation_steps": result["evaluation_steps"],
                    "checkpoint_sha256": sha(model_path),
                    "validation_sha256": sha(path),
                    "episodes": int(lengths.size),
                    "episode_data": result,
                }
            )
        if steps != manifest["validation_steps"]:
            raise ValueError("Aggregate validation budget mismatch")
        manifests.append({"seed": seed, "sha256": sha(manifest_path), "manifest": manifest})
    return {
        "schema_version": 1,
        "study_id": plan["study_id"],
        "audit": "passed",
        "scope": "validation-only backbone feasibility; no allocation comparison or gate unlock",
        "plan_sha256": sha(plan_path),
        "protocol_sha256": protocol_hash(protocol),
        "runs": manifests,
        "training_interactions": sum(x["manifest"]["training_interactions"] for x in manifests),
        "gradient_updates": sum(x["manifest"]["gradient_updates"] for x in manifests),
        "validation_steps": sum(x["evaluation_steps"] for x in rows),
        "episodes": sum(x["episodes"] for x in rows),
        "final_test_steps": 0,
        "records": rows,
    }


def write_tex(payload: dict[str, Any], path: Path) -> None:
    text = r"""The predeclared screen used MORL-Baselines 1.3.0 Envelope and the pinned
upstream Minecart example, with the repository's frozen $\gamma=0.99$ and reward
scales. Each of three seed labels ran exactly 100,000 training interactions and
99,901 gradient updates. Gaussian behavior/update preferences were retained;
this is not a fixed-pool or compute-matched allocation comparator. Validation
used all 32 course preferences, three episodes each, at fixed steps 50,000 and
100,000. Validation preserved training RNG states, but the runner did not seed
Torch initialization or global NumPy/SciPy training draws. These are partially
seeded feasibility runs, not fully reproducible paired replications. The
original CUDA smoke exposed a replay-index transport bug; a tested host-index
bridge preserved the sampled indices/priorities and allowed the pinned learner
to run. No learning rule or hyperparameter was tuned on these validation results.

\begin{table}[htbp]
\centering\small
\caption{Envelope feasibility: positive ore episodes out of 96 fixed cases at each checkpoint.}
\begin{tabular}{rrrrrr}
\toprule
Seed & Steps & Ore 1 & Ore 2 & HV & Expected utility\\
\midrule
"""
    for row in payload["records"]:
        text += (
            f"{row['seed']} & {row['step']:,} & {row['ore_positive_episodes'][0]} & "
            f"{row['ore_positive_episodes'][1]} & {row['hypervolume']:.6f} & {row['expected_utility']:.4f}"
            + r"\\"
            + "\n"
        )
    text += r"\bottomrule\end{tabular}\end{table}" + "\n\n"
    text += (
        f"The completed cohort used {payload['training_interactions']:,} training interactions, "
        f"{payload['gradient_updates']:,} updates and {payload['validation_steps']:,} separate validation "
        f"environment steps across {payload['episodes']:,} episodes. Final-test steps were zero. "
    )
    finals = [row for row in payload["records"] if row["step"] == 100000]
    if all(row["ore_positive_episodes"] == [0, 0] for row in finals):
        text += (
            "All three fixed final checkpoints had zero positive ore episodes in both objectives. "
            "This screen did not demonstrate the Minecart ore task under its declared setting; "
            "it does not show that Envelope cannot solve Minecart under other protocols. "
        )
    else:
        text += (
            "At least one final checkpoint expressed positive ore in some validation cases. "
            "The per-seed counts above delimit that observation; they do not establish robust "
            "task coverage or an adaptive-allocation benefit. "
        )
    text += (
        "All model files and validation tensors passed hash, shape, finite-value, budget and "
        "metric checks. This numerical audit is not an independent semantic review. "
        "Neither outcome unlocks the failed matrix-v1/F1 or final-test workflow.\n"
    )
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("artifacts/envelope-feasibility-v1"))
    parser.add_argument("--plan", type=Path, default=Path("configs/experiments/envelope_feasibility_v1.json"))
    parser.add_argument(
        "--preserve-evidence", action="store_true", help="Audit and regenerate TeX without rewriting historical JSON"
    )
    arguments = parser.parse_args()
    result = audit(arguments.root, arguments.plan)
    if not arguments.preserve_evidence:
        write_json("research/evidence/envelope_feasibility_v1.json", result)
    write_tex(result, Path("paper/REL301m/Chapters/EnvelopeResults.tex"))
    print(f"Verified {len(result['runs'])} jobs, {result['episodes']} episodes, zero test steps")

"""Reproduce bounded P2 findings from the completed audit and retained traces."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.utils.training_recovery import atomic_json

SOURCE = Path("artifacts/preference-recovery-p2-v1/analysis.json")
OUTPUT = Path("outputs/p2-findings-20261102")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    source = json.loads(SOURCE.read_text())
    assert source["audit"] == "numeric_and_provenance_pass"
    assert source["totals"]["training_interactions"] == 6000000
    assert source["totals"]["final_test_steps"] == 0 and source["passing_arms"] == []
    assert len(source["runtime_io_segments"]) == 3
    baseline_case = source["records"][0]["evaluations"][-1]["task"]["records"][0]
    assert baseline_case["action_counts"][5] == baseline_case["steps"] == 1000
    idle_vector = np.asarray(baseline_case["scaled_discounted_return"])
    target_weights = [np.array([0.45, 0.45, 0.1]), np.array([0.8, 0.1, 0.1])]
    rows, trace_cases = [], []
    actions: dict[str, np.ndarray] = {}
    all_validation_positive = final_validation_positive = 0
    for record in source["records"]:
        job = record["job"]
        arm, seed = job["arm"], job["seed"]
        episodes = json.loads((Path(job["directory"]) / "training_episodes.json").read_text())
        completed = [e for e in episodes if e["completed"]]
        positive = [e for e in completed if np.any(np.asarray(e["native_raw_return"])[:2] > 0)]
        successful_vectors = np.asarray([e["scaled_discounted_return"] for e in positive])
        final = record["evaluations"][-1]
        raw = np.asarray(final["validation"]["native_raw_episode_returns"])
        final_positive = int(np.any(raw[:, :, :2] > 0, axis=2).sum())
        final_validation_positive += final_positive
        for evaluation in record["evaluations"]:
            native = np.asarray(evaluation["validation"]["native_raw_episode_returns"])
            all_validation_positive += int(np.any(native[:, :, :2] > 0, axis=2).sum())
        counterfactual = []
        for weight in target_weights:
            utility = successful_vectors @ weight
            baseline = float(idle_vector @ weight)
            counterfactual.append(
                {
                    "target": weight.tolist(),
                    "idle_baseline_utility": baseline,
                    "success_episode_utility_median": float(np.median(utility)),
                    "success_episode_utility_p90": float(np.quantile(utility, 0.9)),
                    "success_episode_utility_max": float(utility.max()),
                    "success_episode_above_idle": int((utility > baseline).sum()),
                    "positive_training_episodes": len(positive),
                }
            )
        summary = next(r for r in source["summaries"] if r["arm"] == arm and r["seed"] == seed)
        row = {
            "arm": arm,
            "seed": seed,
            "validation_eu": summary["metrics"][-1]["expected_utility"],
            "validation_hv": summary["metrics"][-1]["hypervolume"],
            "final_validation_positive_ore": final_positive,
            "completed_training_episodes": len(completed),
            "positive_training_episodes": len(positive),
            "positive_training_fraction": len(positive) / len(completed),
            "positive_training_median_length": float(np.median([e["steps"] for e in positive])),
            "counterfactual_training_rescoring": counterfactual,
        }
        rows.append(row)
        for case in final["task"]["records"]:
            trace = Path(case["trace"])
            assert sha(trace) == case["trace_sha256"]
            with np.load(trace, allow_pickle=False) as data:
                native = data["native_rewards"]
                np.testing.assert_allclose(native.sum(0), case["native_raw_return"], atol=1e-9)
                counts = np.bincount(data["actions"], minlength=6)
                np.testing.assert_array_equal(counts, case["action_counts"])
                # Minecart.get_state() puts cart.pos in the first two coordinates.
                distance = float(np.linalg.norm(data["states"][:, :2] - data["states"][0, :2], axis=1).max())
                assert case["steps"] == 1000 and case["truncated"] and not case["ore_delivered"]
                trace_cases.append(
                    {
                        "arm": arm,
                        "seed": seed,
                        "profile": case["preference_index"],
                        "env_seed": case["seed"],
                        "actions": counts.tolist(),
                        "max_distance_from_initial_cart_position": distance,
                        "cargo_peak": case["cargo_peak"],
                    }
                )
                actions[arm] = actions.get(arm, np.zeros(6, dtype=np.int64)) + counts
    arm_summaries = []
    for arm in "ABCD":
        group = [r for r in rows if r["arm"] == arm]
        values = np.array([r["validation_eu"] for r in group])
        paired = [
            r["validation_eu"] - next(a["validation_eu"] for a in rows if a["arm"] == "A" and a["seed"] == r["seed"])
            for r in group
        ]
        arm_summaries.append(
            {
                "arm": arm,
                "seed_eu": values.tolist(),
                "mean_eu": float(values.mean()),
                "sample_sd_eu": float(values.std(ddof=1)),
                "paired_seed_eu_delta_vs_A": paired,
                "mean_paired_eu_delta_vs_A": float(np.mean(paired)),
                "positive_seed_deltas": sum(v > 0 for v in paired),
                "training_positive_episodes": sum(r["positive_training_episodes"] for r in group),
                "training_completed_episodes": sum(r["completed_training_episodes"] for r in group),
                "final_task_successes": 0,
                "final_task_episodes": 60,
                "final_task_actions": actions[arm].tolist(),
            }
        )
    assert len(trace_cases) == 240 and all_validation_positive == final_validation_positive == 0
    assert sum(r["actions"][0] for r in trace_cases) == 0
    findings = {
        "study_id": source["study_id"],
        "source": str(SOURCE),
        "source_sha256": sha(SOURCE),
        "analysis_script_sha256": sha(Path(__file__)),
        "totals": source["totals"],
        "validation_episodes": 3456,
        "final_validation_episodes": 1152,
        "final_task_episodes": 240,
        "all_checkpoint_positive_validation_ore_episodes": all_validation_positive,
        "final_positive_validation_ore_episodes": final_validation_positive,
        "final_task_mining_actions": 0,
        "review_independence": "executor_only",
        "rows": rows,
        "arm_summaries": arm_summaries,
        "task_trace_diagnostics": trace_cases,
        "factorial_effects": source["factorial_effects"],
        "statistical_limits": (
            "Three paired training seeds; report each seed and sample SD. No episode-pooled CI or significance claim."
        ),
        "counterfactual_limits": (
            "Rescored behavior episodes are observed stochastic trajectories, "
            "not trained deterministic policies or a test split."
        ),
    }
    atomic_json(Path("research/evidence/preference_recovery_p2_findings_v1.json"), findings)
    # Preserve the exact complete audit with full vectors and I/O provenance.
    Path("research/evidence/preference_recovery_p2_v1.json").write_bytes(SOURCE.read_bytes())
    OUTPUT.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    figure, axes = plt.subplots(1, 3, figsize=(13.5, 4.2), layout="constrained")
    colors = ["#2c7a7b", "#d18f23", "#865baf"]
    seeds = sorted({r["seed"] for r in rows})
    for index, seed in enumerate(seeds):
        seed_values = [next(r["validation_eu"] for r in rows if r["arm"] == a and r["seed"] == seed) for a in "ABCD"]
        axes[0].plot(list("ABCD"), seed_values, "o-", color=colors[index], label=str(seed))
        fraction = [
            next(r["positive_training_fraction"] for r in rows if r["arm"] == a and r["seed"] == seed) for a in "ABCD"
        ]
        axes[1].plot(list("ABCD"), np.asarray(fraction) * 100, "o-", color=colors[index])
    axes[0].set(title="Final validation utility", ylabel="Expected utility (frozen scale)")
    axes[0].legend(fontsize=8)
    axes[1].set(title="Training did encounter ore", ylabel="Ore-positive completed episodes (%)")
    bottom = np.zeros(4)
    labels = ["Mine", "Left", "Right", "Accelerate", "Brake", "None"]
    matrix = np.array([actions[a] for a in "ABCD"]) / 60000 * 100
    for index, label in enumerate(labels):
        axes[2].bar(list("ABCD"), matrix[:, index], bottom=bottom, label=label)
        bottom += matrix[:, index]
    axes[2].set(title="Final task behavior: 0/240 deliveries", ylabel="Actions (%)")
    axes[2].legend(fontsize=7, ncol=2)
    figure.suptitle("P2: relabeling / auxiliary loss did not qualify greedy Minecart behavior", fontsize=12)
    figure.savefig(OUTPUT / "p2_findings.png", dpi=180)
    figure.savefig(OUTPUT / "p2_findings.pdf")
    plt.close(figure)
    print(
        json.dumps(
            {
                "arm_summaries": arm_summaries,
                "max_task_displacement": max(r["max_distance_from_initial_cart_position"] for r in trace_cases),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    if not __debug__:
        raise RuntimeError("Evidence assertions must be enabled")
    main()

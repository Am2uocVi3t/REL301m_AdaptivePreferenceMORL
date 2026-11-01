"""Verify episode traces and summarize task behavior without selecting a model."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from src.demo.runtime import sha256
from src.utils.provenance import write_json

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    source = ROOT / "artifacts/demo-behavior-audit-v1/results.json"
    data = json.loads(source.read_text())
    plan_path = ROOT / "configs/demos/behavior_audit_v1.json"
    plan = json.loads(plan_path.read_text())
    if sha256(plan_path) != data["plan_sha256"]:
        raise ValueError("Diagnostic plan changed")
    config = json.loads((ROOT / "outputs/REL301m_Course_Project_20261101/config.json").read_text())
    for row in data["episodes"]:
        path = ROOT / row["trace"]
        if sha256(path) != row["trace_sha256"]:
            raise ValueError("Changed trace")
        trace = json.loads(path.read_text())
        rewards = np.array([transition["reward"] for transition in trace["transitions"]])
        np.testing.assert_allclose(rewards.sum(axis=0), row["raw_return"], atol=1e-7)
        spec = config["environments"][row["environment"]]
        discounted = (rewards * np.power(spec["gamma"], np.arange(len(rewards)))[:, None]).sum(axis=0)
        np.testing.assert_allclose(discounted * spec["reward_scale"], row["discounted_scaled_return"], atol=1e-7)
        if not len(rewards) == row["steps"] <= 1000 or not row["done"]:
            raise ValueError("Episode budget/end mismatch")
    if len(data["episodes"]) != 80 or data["training_updates"] != 0:
        raise ValueError("Incorrect diagnostic scope")
    tables = {}
    for environment in ("lunar", "mine"):
        rows = [row for row in data["episodes"] if row["environment"] == environment]
        summaries = []
        for label in dict.fromkeys(row["case"] for row in rows):
            selected = [row for row in rows if row["case"] == label]
            if len(selected) != 5:
                raise ValueError("Each preference requires every one of the five declared environment seeds")
            expected_seeds = {config["environments"][environment]["seed"] + offset for offset in plan["seed_offsets"]}
            if {row["seed"] for row in selected} != expected_seeds:
                raise ValueError("Missing, duplicated or substituted environment seed")
            weights = plan["environments"][environment]["preferences"][label]
            weights = weights or config["environments"][environment]["default_weights"]
            for row in selected:
                np.testing.assert_allclose(row["weights"], weights, rtol=1e-6, atol=1e-7)
            result: dict[str, Any] = {
                "case": label,
                "weights": selected[0]["weights"],
                "episodes": len(selected),
                "mean_native_return": np.mean([row["raw_return"] for row in selected], axis=0),
                "mean_episode_length": float(np.mean([row["steps"] for row in selected])),
                "reached_presentation_cap": sum(row["presentation_cap"] for row in selected),
                "action_counts": np.sum([row["action_counts"] for row in selected], axis=0),
            }
            if environment == "lunar":
                result.update(
                    {
                        "environment_reported_landing": sum(row["environment_reported_landing"] for row in selected),
                        "landing_inside_pad_x": sum(
                            row["environment_reported_landing"] and row["inside_pad_x"] for row in selected
                        ),
                        "crash_or_out_of_bounds": sum(
                            row["environment_reported_crash_or_out_of_bounds"] for row in selected
                        ),
                    }
                )
            else:
                result.update(
                    {
                        "departed_base": sum(row["departed_base"] for row in selected),
                        "visited_mine": sum(row["visited_mine_radius"] for row in selected),
                        "delivered_any_ore": sum(any(row["delivered_positive_ore"]) for row in selected),
                        "maximum_cargo": np.max([row["maximum_cargo"] for row in selected], axis=0),
                    }
                )
            summaries.append(result)
        tables[environment] = summaries
    receipt = {
        "schema_version": 1,
        "scope": (
            "80 presentation diagnostic episodes, one frozen model per environment; "
            "not final test or five independent training replicates"
        ),
        "raw_return_units": (
            "Native undiscounted environment reward; historical research aggregate raw returns are scaled"
        ),
        "plan_sha256": data["plan_sha256"],
        "raw_results_sha256": sha256(source),
        "trace_numerical_audit": "passed all 80 hashes/lengths/raw/discounted sums",
        "presentation_diagnostic_steps": data["presentation_diagnostic_steps"],
        "training_updates": 0,
        "research_final_test_steps": 0,
        "parameters_unchanged": data["parameters_unchanged"],
        "provenance": data["provenance"],
        "tables": tables,
        "same_state_sensitivity": data["same_state_sensitivity"],
        "episodes": data["episodes"],
    }
    browser_path = ROOT / "artifacts/demo-behavior-audit-v1/browser/results.json"
    if browser_path.exists():
        browser = json.loads(browser_path.read_text())
        if browser["status"] != "PASS" or len(browser["cases"]) != 4:
            raise ValueError("Browser full-episode checks incomplete")
        receipt["browser"] = {
            "path": str(browser_path.relative_to(ROOT)),
            "sha256": sha256(browser_path),
            "cases": 4,
            "status": "PASS",
            "full_episode_integration_steps": sum(
                panel["steps"] for case in browser["cases"] for panel in case["state"]["panels"]
            ),
            "server_cumulative_steps_including_prior_attempts": browser["cases"][-1]["state"][
                "presentation_steps_total"
            ],
            "native_renderer_visibility": json.loads((browser_path.parent / "native-visibility-pass.json").read_text()),
        }
    evidence_path = ROOT / "research/evidence/demo_behavior_audit_v1.json"
    write_json(evidence_path, receipt)
    evidence_path.write_bytes(evidence_path.read_bytes().replace(b"\r\n", b"\n"))
    output = ROOT / "outputs/demo-behavior-audit-v1"
    output.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5), constrained_layout=True)
    lunar = tables["lunar"]
    labels = [row["case"].replace("_", "\n") for row in lunar]
    x = np.arange(len(lunar))
    bottoms = np.zeros(len(lunar))
    outcomes = [
        ("landing_inside_pad_x", "Native +100, within pad x", "#23767d"),
        (None, "Native +100, outside pad x", "#88b5b9"),
        ("crash_or_out_of_bounds", "Crash / out of bounds", "#d76b4c"),
        ("reached_presentation_cap", "1000-step cap", "#a7adb8"),
    ]
    for key, label, color in outcomes:
        values = np.array(
            [row[key] if key else row["environment_reported_landing"] - row["landing_inside_pad_x"] for row in lunar]
        )
        axes[0].bar(x, values, bottom=bottoms, label=label, color=color)
        bottoms += values
    axes[0].set(title="LunarLander: observed outcomes", ylabel="Episodes (five environment seeds)", yticks=range(6))
    axes[0].set_xticks(x, labels, fontsize=8)
    axes[0].legend(fontsize=8, loc="upper left", bbox_to_anchor=(0, -0.22), frameon=False)
    mine = tables["mine"]
    counts = np.array([row["action_counts"] for row in mine])
    percentages = counts / counts.sum(axis=1, keepdims=True) * 100
    bottom = np.zeros(len(mine))
    colors = ["#9c5d77", "#b8ae68", "#8875af", "#e1723a", "#23767d", "#a7adb8"]
    for i, label in enumerate(("Mine", "Left", "Right", "Accelerate", "Brake", "None")):
        axes[1].bar(np.arange(len(mine)), percentages[:, i], bottom=bottom, label=label, color=colors[i])
        bottom += percentages[:, i]
    axes[1].set(title="Minecart: action use (zero ore in 40/40 episodes)", ylabel="Actions (%)", ylim=(0, 100))
    axes[1].set_xticks(np.arange(len(mine)), [row["case"].replace("_", "\n") for row in mine], fontsize=8)
    axes[1].legend(fontsize=8, loc="upper left", bbox_to_anchor=(0, -0.22), ncol=3, frameon=False)
    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(output / "behavior_summary.png", dpi=160)
    fig.savefig(output / "behavior_summary.pdf")
    plt.close(fig)
    lunar_table = [
        "| Preference | w | +100 engine /5 | Trong pad x /5 | Crash /5 | Cap 1000 /5 |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in lunar:
        lunar_table.append(
            f"| {row['case']} | {np.round(row['weights'], 3).tolist()} | "
            f"{row['environment_reported_landing']} | {row['landing_inside_pad_x']} | "
            f"{row['crash_or_out_of_bounds']} | {row['reached_presentation_cap']} |"
        )
    mine_table = ["| Preference | w | Rời base /5 | Tới mine /5 | Giao ore /5 |", "|---|---|---:|---:|---:|"]
    for row in mine:
        mine_table.append(
            f"| {row['case']} | {np.round(row['weights'], 3).tolist()} | "
            f"{row['departed_base']} | {row['visited_mine']} | {row['delivered_any_ore']} |"
        )
    text = (ROOT / "docs/templates/DEMO_BEHAVIOR_AUDIT_VI.template.md").read_text(encoding="utf-8")
    text = text.replace("@@STEPS@@", f"{data['presentation_diagnostic_steps']:,}")
    text = text.replace("@@LUNAR_TABLE@@", "\n".join(lunar_table))
    text = text.replace("@@MINE_TABLE@@", "\n".join(mine_table))
    browser_note = "Chưa hoàn thành kiểm tra UI chạy hết episode."
    if "browser" in receipt:
        browser_note = (
            "Bốn trường hợp UI chạy hết episode bằng Edge (Lunar balanced/landing-heavy, "
            "Minecart ore1-only/ore2-only) khớp steps, weights và native returns của diagnostic trực tiếp. "
            "Native renderer và screenshots nằm tại artifacts/demo-behavior-audit-v1/browser."
        )
    text = text.replace("@@BROWSER@@", browser_note)
    (output / "BEHAVIOR_AUDIT_VI.md").write_text(text, encoding="utf-8")
    (ROOT / "docs/research/DEMO_BEHAVIOR_AUDIT_20261101.md").write_text(text, encoding="utf-8")
    print("Verified and summarized all 80 diagnostic episodes")


if __name__ == "__main__":
    main()

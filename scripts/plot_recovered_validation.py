#!/usr/bin/env python3
"""Plot every saved primary validation checkpoint; descriptive seed mean +/- SD."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    source = json.loads((ROOT / "research/evidence/course_primary_validation_v1.json").read_text())
    target = ROOT / "outputs/course-report/figures"
    target.mkdir(parents=True, exist_ok=True)
    for environment, short in (("mo-lunar-lander-v3", "lunar"), ("minecart-v0", "minecart")):
        figure, axes = plt.subplots(1, 2, figsize=(8.0, 3.0), layout="constrained")
        for arm, label, color in (
            ("uniform", "Uniform", "#245e8b"),
            ("matched-random", "Matched random", "#b46b18"),
            ("full", "Full adaptive", "#8154a5"),
        ):
            runs = sorted(
                (r for r in source["runs"] if r["environment"] == environment and r["arm"] == arm),
                key=lambda r: r["training_seed"],
            )
            checkpoints = [sorted(r["candidates"], key=lambda c: c["checkpoint"]["step"]) for r in runs]
            steps = np.asarray([c["checkpoint"]["step"] for c in checkpoints[0]]) / 1000
            for axis, metric, title in zip(
                axes,
                ("expected_utility", "hypervolume"),
                ("Expected utility", "Protocol-scaled hypervolume"),
                strict=True,
            ):
                values = np.asarray([[c["metrics"][metric] for c in row] for row in checkpoints])
                mean, deviation = values.mean(axis=0), values.std(axis=0, ddof=1)
                axis.plot(steps, mean, color=color, label=label, linewidth=1.6)
                axis.fill_between(steps, mean - deviation, mean + deviation, color=color, alpha=0.12)
                axis.set(title=title, xlabel="Training interactions (thousands)")
                axis.grid(alpha=0.18)
                axis.spines[["top", "right"]].set_visible(False)
        axes[0].legend(frameon=False, fontsize=7)
        figure.suptitle(f"{environment} | validation only | five seeds | bands: sample SD", fontsize=10)
        figure.savefig(target / f"{short}_validation.png", dpi=220)
        plt.close(figure)


if __name__ == "__main__":
    main()

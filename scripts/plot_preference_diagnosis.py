"""Plot every recorded preference diagnosis, including failures."""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle


def main():
    evidence = json.loads(Path("research/evidence/ppo_demo_preference_diagnosis_v1.json").read_text())
    plt.rcParams.update({"font.family": "serif", "font.size": 10})
    fig, axes = plt.subplots(2, 1, figsize=(8, 3.3))
    fig.subplots_adjust(bottom=0.18, left=0.18, right=0.98, top=0.96, hspace=1.15)
    for ax, env, labels, metric in [
        (
            axes[0],
            "lunar",
            ["Default", "Uniform", "Landing\nonly", "Shaping\nonly", "Main fuel\nonly", "Side fuel\nonly"],
            "Lunar\npad landings",
        ),
        (axes[1], "mine", ["Default", "Uniform", "Ore1\nonly", "Ore2\nonly", "Fuel\nonly*"], "Minecart\nore delivery"),
    ]:
        profiles = list(dict.fromkeys(r["profile"] for r in evidence["records"] if r["environment"] == env))
        rows = [[r for r in evidence["records"] if r["environment"] == env and r["profile"] == p] for p in profiles]
        assert all(len(r) == 5 for r in rows)
        counts = [sum(r["task_success"] for r in group) for group in rows]
        ax.imshow(np.asarray([counts]), cmap="Blues", vmin=0, vmax=5, aspect="auto")
        for index, count in enumerate(counts):
            ax.text(
                index, 0, f"{count}/5", ha="center", va="center", color="white" if count >= 3 else "black", fontsize=11
            )
        if env == "mine":
            ax.add_patch(Rectangle((len(counts) - 1.5, -0.5), 1, 1, fill=False, hatch="///", edgecolor="#777777"))
        ax.set(xticks=range(len(labels)), xticklabels=labels, yticks=[0], yticklabels=[metric])
        ax.tick_params(axis="both", length=0, pad=8)
        for spine in ax.spines.values():
            spine.set_visible(False)
    output = Path("outputs/course-report-latex")
    output.mkdir(exist_ok=True, parents=True)
    fig.savefig(output / "preference_diagnosis.pdf")
    fig.savefig(output / "preference_diagnosis.png", dpi=220)
    plt.close(fig)


if __name__ == "__main__":
    main()

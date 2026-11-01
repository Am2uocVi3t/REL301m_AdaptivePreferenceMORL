"""Plot all retained primary checkpoint trajectories, without checkpoint selection."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main() -> None:
    source = Path("research/evidence/course_primary_validation_v1.json")
    evidence = json.loads(source.read_text())
    colors = {"uniform": "#e1723a", "matched-random": "#23767d", "full": "#6c5b9c"}
    labels = {"uniform": "Uniform", "matched-random": "Matched-random", "full": "Full adaptive"}
    fig, axes = plt.subplots(2, 2, figsize=(9, 6.3), constrained_layout=True)
    for i, (environment, title) in enumerate((("mo-lunar-lander-v3", "LunarLander"), ("minecart-v0", "Minecart"))):
        for j, (metric, ylabel) in enumerate(
            (("hypervolume", "Hypervolume"), ("expected_utility", "Expected utility"))
        ):
            ax = axes[i, j]
            for arm, color in colors.items():
                runs = [run for run in evidence["runs"] if run["environment"] == environment and run["arm"] == arm]
                if len(runs) != 5:
                    raise ValueError("Plot requires exactly five original paired seeds per arm/environment")
                ordered = [sorted(run["candidates"], key=lambda item: item["checkpoint"]["step"]) for run in runs]
                steps = np.array([candidate["checkpoint"]["step"] for candidate in ordered[0]]) / 1000
                if any(
                    [candidate["checkpoint"]["step"] / 1000 for candidate in run] != steps.tolist() for run in ordered
                ):
                    raise ValueError("Inconsistent saved checkpoint schedule")
                values = np.array([[candidate["metrics"][metric] for candidate in run] for run in ordered])
                mean, sd = values.mean(axis=0), values.std(axis=0, ddof=1)
                ax.plot(steps, mean, color=color, label=labels[arm], linewidth=1.6)
                ax.fill_between(steps, mean - sd, mean + sd, color=color, alpha=0.12, linewidth=0)
            ax.set(title=title, xlabel="Training interactions (thousands)", ylabel=ylabel)
            ax.spines[["top", "right"]].set_visible(False)
            ax.grid(alpha=0.2)
    handles, legend_labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, legend_labels, loc="outside lower center", ncol=3, frameon=False)
    directory = Path("outputs/course-report-latex")
    directory.mkdir(parents=True, exist_ok=True)
    fig.savefig(directory / "recovered_learning_curves.pdf")
    fig.savefig(directory / "recovered_learning_curves.png", dpi=180)
    plt.close(fig)
    table = r"""\begin{table}[htbp]
\centering\small
\caption{Recovered primary validation at 500,000 interactions; mean $\pm$ sample SD, five seeds.}
\label{tab:primary}
\begin{tabular}{llrr}
\toprule
Environment & Arm & Hypervolume & Expected utility\\
\midrule
"""
    for environment, title in (("mo-lunar-lander-v3", "LunarLander"), ("minecart-v0", "Minecart")):
        for arm in colors:
            runs = [run for run in evidence["runs"] if run["environment"] == environment and run["arm"] == arm]
            finals = [
                [candidate for candidate in run["candidates"] if candidate["checkpoint"]["step"] == 500000]
                for run in runs
            ]
            if len(runs) != 5 or any(len(values) != 1 for values in finals):
                raise ValueError("Missing/extra fixed-final primary records")
            hv = np.array([values[0]["metrics"]["hypervolume"] for values in finals])
            utility = np.array([values[0]["metrics"]["expected_utility"] for values in finals])
            places = 6 if environment == "minecart-v0" else 4
            table += (
                f"{title} & {labels[arm]} & ${hv.mean():.{places}f}"
                + r"\pm"
                + f"{hv.std(ddof=1):.{places}f}$ & ${utility.mean():.4f}"
                + r"\pm"
                + f"{utility.std(ddof=1):.4f}$"
                + r"\\"
                + "\n"
            )
    table += r"\bottomrule\end{tabular}\end{table}" + "\n"
    Path("paper/REL301m/Chapters/PrimaryTable.tex").write_text(table, encoding="utf-8")
    print("Saved all-checkpoint means and sample SD bands; validation diagnostics only")


if __name__ == "__main__":
    main()

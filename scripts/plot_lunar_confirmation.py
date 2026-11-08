"""Plot prospective Lunar seed/mode curves; exclude the observed pilot."""

import json
from pathlib import Path

import matplotlib.pyplot as plt


def main():
    evidence = json.loads(Path("research/evidence/lunar_onpolicy_confirmation_v1.json").read_text())
    if not evidence["all_seed_both_mode_primary_gate_pass"] or evidence["pilot_included"]:
        raise ValueError("Expected audited confirmation with pilot separate")
    plt.rcParams.update({"font.family": "serif", "font.size": 10})
    fig, axes = plt.subplots(1, 2, figsize=(8, 4.2))
    fig.subplots_adjust(bottom=0.28, wspace=0.32, top=0.96)
    for job, color in zip(evidence["jobs"], ["#0072b2", "#d55e00"], strict=True):
        for mode, marker, style in [("sampled", "o", "-"), ("argmax", "x", "--")]:
            cells = [next(c for c in m["task"] if c["mode"] == mode and c["profile"] == 0) for m in job["milestones"]]
            steps = [m["step"] / 1e6 for m in job["milestones"]]
            for ax, key in zip(axes, ["pad_successes", "mean_utility"], strict=True):
                ax.plot(
                    steps,
                    [c[key] for c in cells],
                    color=color,
                    marker=marker,
                    linestyle=style,
                    label=f"{job['seed']} / {mode}",
                    linewidth=1.5,
                    markersize=5,
                )
    axes[0].axhline(8, linestyle=":", color="#555555", linewidth=1)
    axes[0].set(ylabel="Pad landings /10 (trained preference)", ylim=(-0.3, 10.5), yticks=[0, 2, 4, 6, 8, 10])
    axes[1].axhline(0, color="#888888", linewidth=0.7)
    axes[1].set_ylabel("Mean frozen utility (trained preference)")
    for ax in axes:
        ax.set(xlabel="Training interactions (millions)", xticks=[0.5, 1, 2, 4])
        ax.grid(alpha=0.18)
        ax.spines[["top", "right"]].set_visible(False)
    fig.legend(*axes[0].get_legend_handles_labels(), loc="lower center", ncol=2, frameon=False)
    output = Path("outputs/course-report-latex")
    output.mkdir(exist_ok=True, parents=True)
    fig.savefig(output / "lunar_confirmation.pdf")
    fig.savefig(output / "lunar_confirmation.png", dpi=220)
    plt.close(fig)


if __name__ == "__main__":
    main()

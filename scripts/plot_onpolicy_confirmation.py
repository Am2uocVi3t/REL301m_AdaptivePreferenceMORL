"""Draw the completed three-seed confirmation using retained audited results."""

import json
from pathlib import Path

import matplotlib.pyplot as plt


def main():
    evidence = json.loads(Path("research/evidence/minecart_onpolicy_confirmation_v1.json").read_text())
    if not evidence["all_seed_both_mode_both_profile_gate_pass"]:
        raise ValueError("Expected completed confirmation evidence")
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6), layout="constrained")
    colors = {"sampled": "#267d87", "argmax": "#ca6b3e"}
    for j, job in enumerate(evidence["jobs"]):
        for mode in ["sampled", "argmax"]:
            steps = [m["step"] / 1e6 for m in job["milestones"]]
            successes = [min(p["deliveries"] for p in m["gates"][mode]["profiles"]) for m in job["milestones"]]
            eu = [
                next(r["expected_utility"] for r in m["coverage"] if r["kind"] == "validation" and r["mode"] == mode)
                for m in job["milestones"]
            ]
            for ax, values in zip(axes, [successes, eu], strict=True):
                ax.plot(
                    steps,
                    values,
                    marker=["o", "s", "^"][j],
                    color=colors[mode],
                    alpha=0.7,
                    label=mode if j == 0 else None,
                )
    axes[0].axhline(8, color="#75818a", linestyle="--", linewidth=1)
    axes[0].set(ylabel="Minimum deliveries across task profiles /10", ylim=(-0.4, 10.5))
    axes[1].set(ylabel="Expected utility: 32 new preferences")
    for ax in axes:
        ax.set_xlabel("Training interactions (millions)")
        ax.grid(alpha=0.2)
        ax.legend(frameon=False)
    output = Path("outputs/course-report-latex")
    output.mkdir(parents=True, exist_ok=True)
    fig.savefig(output / "minecart_confirmation.pdf")
    fig.savefig(output / "minecart_confirmation.png", dpi=180)
    plt.close(fig)


if __name__ == "__main__":
    main()

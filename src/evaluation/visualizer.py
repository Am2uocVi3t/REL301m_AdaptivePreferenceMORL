import matplotlib.pyplot as plt
import numpy as np


def plot_pareto_front_2d(
    methods_points: dict[str, np.ndarray],
    dim_x: int = 0,
    dim_y: int = 1,
    labels: list[str] | None = None,
    title: str = "Pareto Frontier Comparison",
    save_path: str | None = None,
):
    """
    Plots 2D projection of Pareto Frontiers for LaTeX paper report.
    """
    plt.figure(figsize=(8, 6))
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]

    for idx, (method_name, pts) in enumerate(methods_points.items()):
        if len(pts) == 0:
            continue
        c = colors[idx % len(colors)]
        plt.scatter(pts[:, dim_x], pts[:, dim_y], label=method_name, color=c, alpha=0.8, s=40)

    lbl_x = labels[dim_x] if labels else f"Objective {dim_x + 1}"
    lbl_y = labels[dim_y] if labels else f"Objective {dim_y + 1}"
    plt.xlabel(lbl_x, fontsize=12)
    plt.ylabel(lbl_y, fontsize=12)
    plt.title(title, fontsize=14, fontweight="bold")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend(fontsize=11)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300)
    plt.close()

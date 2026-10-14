from __future__ import annotations

from itertools import product

import numpy as np


def bootstrap_ci(
    data: np.ndarray,
    n_boot: int = 5000,
    ci: float = 0.95,
    seed: int = 42,
) -> tuple[float, float, float]:
    values = np.asarray(data, dtype=np.float64)
    if values.ndim != 1 or len(values) == 0:
        raise ValueError("data must be a non-empty one-dimensional array")
    rng = np.random.default_rng(seed)
    samples = rng.choice(values, size=(n_boot, len(values)), replace=True)
    means = samples.mean(axis=1)
    alpha = 1.0 - ci
    return (
        float(values.mean()),
        float(np.quantile(means, alpha / 2.0)),
        float(np.quantile(means, 1.0 - alpha / 2.0)),
    )


def paired_effect_size(scores_a: np.ndarray, scores_b: np.ndarray) -> float:
    differences = np.asarray(scores_a, dtype=np.float64) - np.asarray(scores_b, dtype=np.float64)
    standard_deviation = differences.std(ddof=1)
    if standard_deviation == 0.0:
        return float("inf") if differences.mean() != 0.0 else 0.0
    return float(differences.mean() / standard_deviation)


def paired_permutation_test(
    scores_a: np.ndarray,
    scores_b: np.ndarray,
    max_exact_pairs: int = 20,
    monte_carlo_samples: int = 100_000,
    seed: int = 42,
) -> dict[str, float | int | str]:
    a = np.asarray(scores_a, dtype=np.float64)
    b = np.asarray(scores_b, dtype=np.float64)
    if a.shape != b.shape or a.ndim != 1 or len(a) < 2:
        raise ValueError("Paired scores must be one-dimensional, equal-length arrays with at least two pairs")

    differences = a - b
    observed = abs(float(differences.mean()))
    if len(differences) <= max_exact_pairs:
        statistics = [abs(float(np.mean(differences * signs))) for signs in product((-1.0, 1.0), repeat=len(a))]
        exceedances = sum(statistic >= observed - 1e-15 for statistic in statistics)
        p_value = exceedances / len(statistics)
        mode = "exact"
        permutations = len(statistics)
    else:
        rng = np.random.default_rng(seed)
        signs = rng.choice((-1.0, 1.0), size=(monte_carlo_samples, len(a)))
        statistics = np.abs((signs * differences).mean(axis=1))
        exceedances = int(np.sum(statistics >= observed - 1e-15))
        p_value = (exceedances + 1) / (monte_carlo_samples + 1)
        mode = "monte_carlo"
        permutations = monte_carlo_samples

    return {
        "mean_difference": float(differences.mean()),
        "effect_size_dz": paired_effect_size(a, b),
        "p_value": float(p_value),
        "mode": mode,
        "permutations": permutations,
    }


def holm_adjust(p_values: np.ndarray) -> np.ndarray:
    values = np.asarray(p_values, dtype=np.float64)
    if values.ndim != 1 or np.any((values < 0.0) | (values > 1.0)):
        raise ValueError("p_values must be a one-dimensional array in [0, 1]")

    order = np.argsort(values)
    adjusted_sorted = np.empty_like(values)
    running_max = 0.0
    count = len(values)
    for rank, index in enumerate(order):
        adjusted = min(1.0, (count - rank) * values[index])
        running_max = max(running_max, adjusted)
        adjusted_sorted[rank] = running_max

    adjusted = np.empty_like(values)
    adjusted[order] = adjusted_sorted
    return adjusted

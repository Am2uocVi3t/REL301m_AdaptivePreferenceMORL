from __future__ import annotations

import numpy as np


def pareto_prune(points: np.ndarray) -> np.ndarray:
    values = np.asarray(points, dtype=np.float32)
    if values.size == 0:
        width = values.shape[1] if values.ndim == 2 else 0
        return np.empty((0, width), dtype=np.float32)
    if values.ndim != 2:
        raise ValueError("points must have shape [N, objectives]")

    values = np.unique(values, axis=0)
    keep = np.ones(len(values), dtype=bool)
    for index, candidate in enumerate(values):
        if not keep[index]:
            continue
        dominates_candidate = np.all(values >= candidate, axis=1) & np.any(values > candidate, axis=1)
        keep[index] = not np.any(dominates_candidate)
    return values[keep]


def compute_hypervolume(points: np.ndarray, ref_point: np.ndarray) -> float:
    """Compute deterministic maximization hypervolume."""
    frontier = pareto_prune(points)
    reference = np.asarray(ref_point, dtype=np.float32)
    if frontier.size == 0:
        return 0.0
    if frontier.shape[1] != len(reference):
        raise ValueError("Reference point dimension does not match the points")

    valid = frontier[np.all(frontier >= reference, axis=1)]
    if valid.size == 0:
        return 0.0
    if valid.shape[1] == 2:
        return _hypervolume_2d(valid, reference)

    try:
        from pymoo.indicators.hv import HV

        indicator = HV(ref_point=-reference)
        return float(indicator(-valid))
    except ImportError as error:
        raise RuntimeError("Deterministic hypervolume for three or more objectives requires pymoo") from error


def _hypervolume_2d(points: np.ndarray, reference: np.ndarray) -> float:
    frontier = pareto_prune(points)
    frontier = frontier[np.argsort(frontier[:, 0])]
    area = 0.0
    previous_x = float(reference[0])
    for point in frontier:
        width = float(point[0] - previous_x)
        height = float(point[1] - reference[1])
        if width > 0.0 and height > 0.0:
            area += width * height
        previous_x = max(previous_x, float(point[0]))
    return area


def normalize_returns(
    returns: np.ndarray,
    lower_bounds: np.ndarray,
    upper_bounds: np.ndarray,
) -> np.ndarray:
    values = np.asarray(returns, dtype=np.float32)
    lower = np.asarray(lower_bounds, dtype=np.float32)
    upper = np.asarray(upper_bounds, dtype=np.float32)
    scale = upper - lower
    if np.any(scale <= 0.0):
        raise ValueError("Every normalization upper bound must exceed its lower bound")
    return (values - lower) / scale


def compute_expected_utility(agent_returns: np.ndarray, preferences: np.ndarray) -> float:
    returns = np.asarray(agent_returns, dtype=np.float32)
    weights = np.asarray(preferences, dtype=np.float32)
    if returns.shape != weights.shape:
        raise ValueError("agent_returns and preferences must have the same shape")
    return float(np.mean(np.sum(returns * weights, axis=1)))


def compute_scalarized_regret(
    agent_returns: np.ndarray,
    reference_front: np.ndarray,
    preferences: np.ndarray,
) -> dict[str, float]:
    returns = np.asarray(agent_returns, dtype=np.float32)
    reference = np.asarray(reference_front, dtype=np.float32)
    weights = np.asarray(preferences, dtype=np.float32)
    if reference.size == 0:
        raise ValueError("reference_front cannot be empty")
    if returns.shape != weights.shape:
        raise ValueError("agent_returns and preferences must have the same shape")

    optimal = np.max(weights @ reference.T, axis=1)
    actual = np.sum(weights * returns, axis=1)
    regrets = np.maximum(0.0, optimal - actual)
    tail_start = max(1, int(np.ceil(0.1 * len(regrets))))
    worst_tail = np.sort(regrets)[-tail_start:]
    return {
        "mean_regret": float(regrets.mean()),
        "worst_decile_regret": float(np.quantile(regrets, 0.9)),
        "cvar_10_regret": float(worst_tail.mean()),
        "max_regret": float(regrets.max()),
    }


def compute_igd(points: np.ndarray, reference_front: np.ndarray) -> float:
    frontier = pareto_prune(points)
    reference = pareto_prune(reference_front)
    if frontier.size == 0 or reference.size == 0:
        raise ValueError("Both fronts must contain at least one point")
    distances = np.linalg.norm(reference[:, None, :] - frontier[None, :, :], axis=-1)
    return float(np.mean(np.min(distances, axis=1)))


def compute_sparsity(points: np.ndarray) -> float:
    frontier = pareto_prune(points)
    if len(frontier) < 2:
        return 0.0
    pairwise = np.linalg.norm(frontier[:, None, :] - frontier[None, :, :], axis=-1)
    np.fill_diagonal(pairwise, np.inf)
    return float(np.mean(np.min(pairwise, axis=1)))

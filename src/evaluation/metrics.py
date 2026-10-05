import numpy as np
from typing import Dict, Union, List
from src.core.pareto_archive import dominates

def pareto_prune(points: np.ndarray) -> np.ndarray:
    """
    Filters a set of multidimensional points to retain only the non-dominated Pareto frontier.
    Args:
        points: Array of shape [N, d]
    Returns:
        non_dominated_points: Array of shape [M, d] where M <= N
    """
    if len(points) == 0:
        return np.empty((0, points.shape[1] if points.ndim > 1 else 0), dtype=np.float32)

    pts = np.asarray(points, dtype=np.float32)
    is_efficient = np.ones(pts.shape[0], dtype=bool)

    for i, c in enumerate(pts):
        if is_efficient[i]:
            # Keep any point with a component strictly greater, or equal in all components
            is_efficient[is_efficient] = ~np.array([
                dominates(c, other) for other in pts[is_efficient]
            ])
            is_efficient[i] = True  # Keep self

    return pts[is_efficient]

def compute_hypervolume(points: np.ndarray, ref_point: np.ndarray) -> float:
    """
    Computes Hypervolume dominated by points with respect to ref_point.
    """
    points = pareto_prune(points)
    if len(points) == 0:
        return 0.0

    ref = np.asarray(ref_point, dtype=np.float32)
    # Filter points that dominate or are at least equal to ref_point
    valid_points = points[np.all(points >= ref, axis=1)]
    if len(valid_points) == 0:
        return 0.0

    try:
        from morl_baselines.common.evaluation import hypervolume
        return float(hypervolume(ref, valid_points))
    except (ImportError, Exception):
        # Fallback 2D calculation if morl_baselines is not installed
        if valid_points.shape[1] == 2:
            sorted_pts = valid_points[np.argsort(valid_points[:, 0])]
            hv = 0.0
            last_y = ref[1]
            for pt in reversed(sorted_pts):
                if pt[1] > last_y:
                    hv += (pt[0] - ref[0]) * (pt[1] - last_y)
                    last_y = pt[1]
            return float(hv)
        # Approximate Monte Carlo hypervolume for d >= 3
        mins = ref
        maxs = np.max(valid_points, axis=0)
        n_samples = 10000
        samples = np.random.uniform(mins, maxs, size=(n_samples, len(ref)))
        dominated_count = np.sum([np.any(np.all(valid_points >= s, axis=1)) for s in samples])
        box_vol = np.prod(maxs - mins)
        return float((dominated_count / n_samples) * box_vol)

def compute_scalarized_regret(
    agent_returns: np.ndarray,
    reference_front: np.ndarray,
    preferences: np.ndarray
) -> Dict[str, float]:
    """
    Computes Scalarized Regret across a test set of preferences (Eq. in Section 6.3):
    Regret(w) = max_{v in A*} w^T v - w^T v_{pi(w)}
    
    Args:
        agent_returns: [N_pref, d] returns achieved by policy on each preference
        reference_front: [M, d] empirical Pareto reference front
        preferences: [N_pref, d] test preference vectors
    Returns:
        dict containing 'mean_regret', 'worst_decile_regret' (90th percentile), and 'max_regret'
    """
    regrets = []
    for w, ret in zip(preferences, agent_returns):
        optimal_val = np.max(np.dot(reference_front, w))
        actual_val = np.dot(ret, w)
        regrets.append(max(0.0, float(optimal_val - actual_val)))

    regrets = np.array(regrets, dtype=np.float32)
    return {
        "mean_regret": float(np.mean(regrets)),
        "worst_decile_regret": float(np.percentile(regrets, 90)),
        "max_regret": float(np.max(regrets)),
    }

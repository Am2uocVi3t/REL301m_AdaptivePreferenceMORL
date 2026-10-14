import numpy as np

from src.core.pareto_archive import ParetoArchive


def compute_conditioning_gap(
    preference: np.ndarray,
    pareto_archive: ParetoArchive,
    current_policy_return: np.ndarray,
) -> float:
    """
    Computes Conditioning Gap g(w) as defined in Eq. (11) of the proposal:
    g(w) = [ max_{v in A} w^T v - w^T v_hat ]_+

    Args:
        preference: 1D array of shape [reward_dim]
        pareto_archive: Instance of ParetoArchive
        current_policy_return: Empirical return vector achieved by current policy on preference w
    Returns:
        gap: Non-negative float score
    """
    w = np.asarray(preference, dtype=np.float32)
    if len(pareto_archive) == 0:
        return 0.0
    max_archive_val = pareto_archive.max_scalarized(w)

    v_hat = np.asarray(current_policy_return, dtype=np.float32)
    if v_hat.shape != w.shape:
        raise ValueError(f"Expected current return shape {w.shape}, got {v_hat.shape}")
    current_val = float(np.dot(w, v_hat))

    return max(0.0, max_archive_val - current_val)

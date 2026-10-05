import numpy as np
from src.core.pareto_archive import ParetoArchive
from typing import Optional

def compute_conditioning_gap(
    preference: np.ndarray,
    pareto_archive: ParetoArchive,
    current_policy_return: Optional[np.ndarray] = None
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
    max_archive_val = pareto_archive.max_scalarized(w)

    if current_policy_return is None:
        # If no recent evaluation, assume policy has not yet covered this preference
        return max(0.0, float(max_archive_val))

    v_hat = np.asarray(current_policy_return, dtype=np.float32)
    current_val = float(np.dot(w, v_hat))

    return max(0.0, max_archive_val - current_val)

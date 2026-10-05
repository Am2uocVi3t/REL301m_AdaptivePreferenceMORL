import numpy as np
from scipy import stats
from typing import Tuple, Dict

def bootstrap_ci(
    data: np.ndarray,
    n_boot: int = 2000,
    ci: float = 0.95,
    seed: int = 42
) -> Tuple[float, float, float]:
    """
    Computes 95% Bootstrap Confidence Interval on independent training seeds.
    Args:
        data: 1D array of metric values (one per seed)
        n_boot: Number of bootstrap resamples
        ci: Confidence level (e.g. 0.95)
    Returns:
        (mean, lower_bound, upper_bound)
    """
    data = np.asarray(data, dtype=np.float32)
    if len(data) == 0:
        return 0.0, 0.0, 0.0

    rng = np.random.default_rng(seed)
    boot_means = []
    for _ in range(n_boot):
        sample = rng.choice(data, size=len(data), replace=True)
        boot_means.append(np.mean(sample))

    alpha = 1.0 - ci
    lower = float(np.percentile(boot_means, 100 * (alpha / 2.0)))
    upper = float(np.percentile(boot_means, 100 * (1.0 - alpha / 2.0)))
    mean_val = float(np.mean(data))

    return mean_val, lower, upper

def paired_statistical_test(
    scores_a: np.ndarray,
    scores_b: np.ndarray
) -> Dict[str, float]:
    """
    Conducts paired comparison across identical training seeds.
    Uses Wilcoxon signed-rank test (or paired t-test if sample is small).
    """
    a = np.asarray(scores_a, dtype=np.float32)
    b = np.asarray(scores_b, dtype=np.float32)
    diff = a - b

    try:
        stat, p_val = stats.wilcoxon(a, b)
    except Exception:
        # Fallback to paired t-test
        stat, p_val = stats.ttest_rel(a, b)

    return {
        "mean_diff": float(np.mean(diff)),
        "std_diff": float(np.std(diff)),
        "statistic": float(stat),
        "p_value": float(p_val),
        "is_significant_005": bool(p_val < 0.05),
    }

import numpy as np
from typing import List, Optional, Tuple

def dominates(u: np.ndarray, v: np.ndarray) -> bool:
    """
    Returns True if vector u Pareto-dominates vector v (assuming maximization).
    u dominates v iff u >= v elementwise and u_i > v_i for at least one dimension.
    """
    return np.all(u >= v) and np.any(u > v)

class ParetoArchive:
    """
    Stores non-dominated return vectors v in R^d discovered during training.
    Used for:
    1. Tracking Pareto coverage evolution.
    2. Computing conditioning gap for candidate preferences: max_{v in A} w^T v.
    3. Generating the empirical reference front.
    """
    def __init__(self, reward_dim: int):
        self.reward_dim = reward_dim
        self.points: List[np.ndarray] = []
        self.metadata: List[dict] = []

    def add(self, candidate: np.ndarray, meta: Optional[dict] = None) -> bool:
        """
        Add a candidate vector to archive if it is non-dominated.
        Removes any existing points dominated by candidate.
        Returns True if candidate was added, False otherwise.
        """
        candidate = np.asarray(candidate, dtype=np.float32)
        if len(candidate) != self.reward_dim:
            raise ValueError(f"Expected vector of dimension {self.reward_dim}, got {len(candidate)}")

        # Check if dominated by any current point
        for pt in self.points:
            if dominates(pt, candidate) or np.array_equal(pt, candidate):
                return False

        # Filter out existing points that are dominated by the new candidate
        surviving_points = []
        surviving_meta = []
        for pt, m in zip(self.points, self.metadata):
            if not dominates(candidate, pt):
                surviving_points.append(pt)
                surviving_meta.append(m)

        surviving_points.append(candidate)
        surviving_meta.append(meta or {})
        self.points = surviving_points
        self.metadata = surviving_meta
        return True

    def max_scalarized(self, preference: np.ndarray) -> float:
        """
        Computes max_{v in A} w^T v.
        Returns 0.0 if archive is empty.
        """
        if not self.points:
            return 0.0
        w = np.asarray(preference, dtype=np.float32)
        pts = np.array(self.points)  # [N, d]
        scalarized_values = np.dot(pts, w)
        return float(np.max(scalarized_values))

    def get_points(self) -> np.ndarray:
        """Return non-dominated points as a NumPy array of shape [N, d]."""
        if not self.points:
            return np.empty((0, self.reward_dim), dtype=np.float32)
        return np.array(self.points, dtype=np.float32)

    def __len__(self) -> int:
        return len(self.points)

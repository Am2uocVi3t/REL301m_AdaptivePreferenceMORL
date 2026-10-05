import numpy as np
from typing import List, Optional
from src.core.pareto_archive import ParetoArchive

class AdaptivePreferenceSampler:
    """
    Adaptive Preference Curriculum Sampler as described in Section 5.3 of the proposal.
    Maintains a candidate pool W and updates sampling probabilities based on:
    - Conditioning Gap g(w)
    - Bootstrap Uncertainty u(w)
    - Coverage / Recency c(w)
    """
    def __init__(
        self,
        reward_dim: int,
        pool_size: int = 100,
        alpha: float = 0.25,
        beta: float = 0.25,
        eta: float = 0.25,
        temperature: float = 0.1,
        eps_c: float = 0.2,
        seed: int = 42
    ):
        self.reward_dim = reward_dim
        self.pool_size = pool_size
        self.alpha = alpha
        self.beta = beta
        self.eta = eta
        self.temperature = temperature
        self.eps_c = eps_c
        self.rng = np.random.default_rng(seed)

        self.pool = self._init_preference_pool()
        self.visit_counts = np.zeros(len(self.pool), dtype=np.int32)
        
        # Raw signal vectors
        self.gap_scores = np.zeros(len(self.pool), dtype=np.float32)
        self.uncertainty_scores = np.zeros(len(self.pool), dtype=np.float32)
        
        # Probability distribution over candidates
        self.probabilities = np.ones(len(self.pool), dtype=np.float32) / len(self.pool)

    def _init_preference_pool(self) -> np.ndarray:
        """Initialize candidate pool with corners, edges, and Dirichlet random samples."""
        candidates = []
        d = self.reward_dim

        # 1. Simplex corners (pure single-objective preferences)
        for i in range(d):
            corner = np.zeros(d, dtype=np.float32)
            corner[i] = 1.0
            candidates.append(corner)

        # 2. Pairwise edge midpoints (50-50 trade-offs)
        for i in range(d):
            for j in range(i + 1, d):
                edge = np.zeros(d, dtype=np.float32)
                edge[i] = 0.5
                edge[j] = 0.5
                candidates.append(edge)

        # 3. Center point (equal trade-off across all objectives)
        center = np.ones(d, dtype=np.float32) / d
        candidates.append(center)

        # 4. Dirichlet random samples to fill remaining pool size
        remaining = max(0, self.pool_size - len(candidates))
        if remaining > 0:
            dirichlet_samples = self.rng.dirichlet(np.ones(d), size=remaining).astype(np.float32)
            candidates.extend(list(dirichlet_samples))

        return np.array(candidates, dtype=np.float32)

    def sample(self) -> np.ndarray:
        """Sample a preference vector w according to current probability distribution."""
        idx = self.rng.choice(len(self.pool), p=self.probabilities)
        self.visit_counts[idx] += 1
        return self.pool[idx].copy()

    def update_distribution(
        self,
        gap_scores: np.ndarray,
        uncertainty_scores: np.ndarray
    ):
        """
        Recompute distribution p(w) using Eq. (13) and Eq. (14).
        """
        self.gap_scores = np.asarray(gap_scores, dtype=np.float32)
        self.uncertainty_scores = np.asarray(uncertainty_scores, dtype=np.float32)

        # Coverage score: inverse of visit count
        coverage_scores = 1.0 / (1.0 + self.visit_counts.astype(np.float32))

        # Normalize signals to [0, 1]
        def _normalize(arr: np.ndarray) -> np.ndarray:
            denom = arr.max() - arr.min()
            if denom < 1e-8:
                return np.zeros_like(arr)
            return (arr - arr.min()) / denom

        g_norm = _normalize(self.gap_scores)
        u_norm = _normalize(self.uncertainty_scores)
        c_norm = _normalize(coverage_scores)

        # Combined composite score: z(w) = alpha * g + beta * u + eta * c
        z = self.alpha * g_norm + self.beta * u_norm + self.eta * c_norm

        # Softmax over z(w) / tau
        z_scaled = z / max(self.temperature, 1e-4)
        z_scaled -= np.max(z_scaled)  # Numerical stability
        exp_z = np.exp(z_scaled)
        softmax_p = exp_z / np.sum(exp_z)

        # Mix with uniform exploration floor: p(w) = (1 - eps_c) * softmax + eps_c / |W|
        W_len = len(self.pool)
        self.probabilities = (1.0 - self.eps_c) * softmax_p + (self.eps_c / W_len)
        self.probabilities /= np.sum(self.probabilities)  # Ensure exact sum to 1.0

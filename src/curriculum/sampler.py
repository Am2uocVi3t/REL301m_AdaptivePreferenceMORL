from __future__ import annotations

import numpy as np


def _normalize(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=np.float32)
    span = float(values.max() - values.min())
    if span < 1e-8:
        return np.zeros_like(values)
    return (values - values.min()) / span


class AdaptivePreferenceSampler:
    """Finite-pool curriculum with explicit difficulty, uncertainty and sampling history."""

    def __init__(
        self,
        reward_dim: int,
        pool_size: int = 100,
        gap_weight: float = 0.25,
        uncertainty_weight: float = 0.25,
        coverage_weight: float = 0.25,
        progress_weight: float = 0.25,
        temperature: float = 0.1,
        uniform_floor: float = 0.2,
        locality_bandwidth: float = 0.2,
        seed: int = 42,
        pool_seed: int | None = None,
    ) -> None:
        if reward_dim < 2:
            raise ValueError("reward_dim must be at least two")
        if pool_size < reward_dim + 1:
            raise ValueError("pool_size must fit all simplex corners and the center")
        if temperature <= 0.0 or locality_bandwidth <= 0.0:
            raise ValueError("temperature and locality_bandwidth must be positive")
        if not 0.0 <= uniform_floor <= 1.0:
            raise ValueError("uniform_floor must be in [0, 1]")

        self.reward_dim = reward_dim
        self.pool_size = pool_size
        self.gap_weight = gap_weight
        self.uncertainty_weight = uncertainty_weight
        self.coverage_weight = coverage_weight
        self.progress_weight = progress_weight
        self.temperature = temperature
        self.uniform_floor = uniform_floor
        self.locality_bandwidth = locality_bandwidth
        self.rng = np.random.default_rng(seed)
        self.pool_rng = np.random.default_rng(seed if pool_seed is None else pool_seed)

        self.pool = self._init_preference_pool()
        self.visit_counts = np.zeros(pool_size, dtype=np.int64)
        self.last_visit = np.full(pool_size, -1, dtype=np.int64)
        self.clock = 0

        self.gap_scores = np.zeros(pool_size, dtype=np.float32)
        self.uncertainty_scores = np.zeros(pool_size, dtype=np.float32)
        self.progress_scores = np.zeros(pool_size, dtype=np.float32)
        self.coverage_scores = np.ones(pool_size, dtype=np.float32)
        self.probabilities = np.full(pool_size, 1.0 / pool_size, dtype=np.float32)

        distances = np.linalg.norm(self.pool[:, None, :] - self.pool[None, :, :], axis=-1)
        self.locality_kernel = np.exp(-0.5 * (distances / locality_bandwidth) ** 2).astype(np.float32)

    def _init_preference_pool(self) -> np.ndarray:
        candidates: list[np.ndarray] = []
        for index in range(self.reward_dim):
            corner = np.zeros(self.reward_dim, dtype=np.float32)
            corner[index] = 1.0
            candidates.append(corner)

        candidates.append(np.full(self.reward_dim, 1.0 / self.reward_dim, dtype=np.float32))
        for first in range(self.reward_dim):
            for second in range(first + 1, self.reward_dim):
                if len(candidates) >= self.pool_size:
                    break
                midpoint = np.zeros(self.reward_dim, dtype=np.float32)
                midpoint[first] = midpoint[second] = 0.5
                candidates.append(midpoint)

        remaining = self.pool_size - len(candidates)
        if remaining:
            random_preferences = self.pool_rng.dirichlet(np.ones(self.reward_dim), size=remaining)
            candidates.extend(random_preferences.astype(np.float32))
        return np.asarray(candidates, dtype=np.float32)

    def sample_index(self) -> int:
        index = int(self.rng.choice(self.pool_size, p=self.probabilities))
        self.visit_counts[index] += 1
        self.last_visit[index] = self.clock
        self.clock += 1
        return index

    def sample(self) -> np.ndarray:
        return self.pool[self.sample_index()].copy()

    def sample_batch(self, batch_size: int) -> np.ndarray:
        indices = [self.sample_index() for _ in range(batch_size)]
        return self.pool[indices].copy()

    def _compute_coverage_recency(self) -> np.ndarray:
        local_density = self.locality_kernel @ self.visit_counts.astype(np.float32)
        coverage = 1.0 / (1.0 + local_density)
        ages = np.where(self.last_visit < 0, self.clock + 1, self.clock - self.last_visit)
        recency = _normalize(ages.astype(np.float32))
        return 0.5 * _normalize(coverage) + 0.5 * recency

    def update_distribution(
        self,
        gap_scores: np.ndarray,
        uncertainty_scores: np.ndarray,
        progress_scores: np.ndarray | None = None,
        random_scores: np.ndarray | None = None,
    ) -> None:
        expected_shape = (self.pool_size,)
        arrays = [
            np.asarray(gap_scores, dtype=np.float32),
            np.asarray(uncertainty_scores, dtype=np.float32),
        ]
        if any(values.shape != expected_shape for values in arrays):
            raise ValueError(f"All score vectors must have shape {expected_shape}")

        self.gap_scores, self.uncertainty_scores = arrays
        self.progress_scores = (
            np.zeros(self.pool_size, dtype=np.float32)
            if progress_scores is None
            else np.asarray(progress_scores, dtype=np.float32)
        )
        if self.progress_scores.shape != expected_shape:
            raise ValueError(f"progress_scores must have shape {expected_shape}")

        self.coverage_scores = self._compute_coverage_recency()
        if random_scores is None:
            combined = (
                self.gap_weight * _normalize(self.gap_scores)
                + self.uncertainty_weight * _normalize(self.uncertainty_scores)
                + self.coverage_weight * _normalize(self.coverage_scores)
                + self.progress_weight * _normalize(self.progress_scores)
            )
        else:
            combined = _normalize(np.asarray(random_scores, dtype=np.float32))

        logits = combined / self.temperature
        logits -= float(np.max(logits))
        adaptive = np.exp(logits)
        adaptive /= adaptive.sum()
        uniform = np.full(self.pool_size, 1.0 / self.pool_size)
        self.probabilities = ((1.0 - self.uniform_floor) * adaptive + self.uniform_floor * uniform).astype(np.float32)
        self.probabilities /= self.probabilities.sum()

    def update_scores(
        self,
        gap_scores: np.ndarray,
        uncertainty_scores: np.ndarray,
        progress_scores: np.ndarray | None = None,
    ) -> None:
        self.update_distribution(gap_scores, uncertainty_scores, progress_scores)

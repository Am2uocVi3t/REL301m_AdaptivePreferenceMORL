"""Uniform episode-fixed preferences with independent and resumable RNG."""

from __future__ import annotations

import copy
from typing import Any

import numpy as np

from src.evaluation.protocol import validate_preferences


class EpisodePreferences:
    def __init__(self, pool: np.ndarray, streams: int, seed: int):
        self.pool = validate_preferences(pool, 3).copy()
        if len(self.pool) != 32:
            raise ValueError("Conditional pilot requires the frozen32-weight pool")
        self.rng = np.random.default_rng(np.random.SeedSequence([seed, 20]))
        self.indices = np.zeros(streams, dtype=np.int64)
        self.draw_counts = np.zeros(32, dtype=np.int64)
        self.interaction_counts = np.zeros(32, dtype=np.int64)
        for stream in range(streams):
            self.reset(stream)

    def reset(self, stream: int) -> None:
        index = int(self.rng.integers(32))
        self.indices[stream] = index
        self.draw_counts[index] += 1

    def values(self) -> np.ndarray:
        # Advanced indexing makes a copy: stored transitions cannot be rewritten
        # when another episode starts later in the same rollout fragment.
        return self.pool[self.indices].copy()

    def record_tick(self) -> None:
        np.add.at(self.interaction_counts, self.indices, 1)

    def state_dict(self) -> dict[str, Any]:
        return {
            "pool": self.pool.copy(),
            "indices": self.indices.copy(),
            "draw_counts": self.draw_counts.copy(),
            "interaction_counts": self.interaction_counts.copy(),
            "rng": copy.deepcopy(self.rng.bit_generator.state),
        }

    def load_state_dict(self, state: dict[str, Any]) -> None:
        np.testing.assert_array_equal(state["pool"], self.pool)
        if state["indices"].shape != self.indices.shape:
            raise ValueError("Stream count differs from checkpoint")
        for key in ["indices", "draw_counts", "interaction_counts"]:
            setattr(self, key, state[key].copy())
        self.rng.bit_generator.state = copy.deepcopy(state["rng"])

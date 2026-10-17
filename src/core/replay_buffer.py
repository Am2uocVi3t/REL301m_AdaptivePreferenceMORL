from __future__ import annotations

from collections.abc import Sequence
from typing import Literal, NamedTuple

import numpy as np
import torch


class ReplayBatch(NamedTuple):
    states: torch.Tensor
    actions: torch.Tensor
    rewards: torch.Tensor
    next_states: torch.Tensor
    terminated: torch.Tensor
    truncated: torch.Tensor
    behavior_preferences: torch.Tensor
    bootstrap_masks: torch.Tensor
    indices: np.ndarray
    importance_weights: torch.Tensor
    effective_preferences: torch.Tensor
    sample_origins: torch.Tensor
    trajectory_ids: torch.Tensor


class ReplayHandle(NamedTuple):
    buffer_index: int
    generation: int


class VectorReplayBuffer:
    """Replay buffer for vector rewards and preference-conditioned updates."""

    def __init__(
        self,
        capacity: int,
        state_dim: int,
        action_dim: int,
        reward_dim: int,
        num_heads: int = 3,
        bootstrap_probability: float = 0.8,
        device: str = "cpu",
        seed: int = 42,
        sampling: Literal["uniform", "prioritized"] = "uniform",
        priority_alpha: float = 0.6,
        priority_epsilon: float = 1e-6,
    ) -> None:
        if capacity <= 0 or num_heads <= 0:
            raise ValueError("capacity and num_heads must be positive")
        if not 0.0 < bootstrap_probability <= 1.0:
            raise ValueError("bootstrap_probability must be in (0, 1]")
        if sampling not in {"uniform", "prioritized"}:
            raise ValueError("sampling must be 'uniform' or 'prioritized'")
        if not np.isfinite(priority_alpha) or priority_alpha < 0.0:
            raise ValueError("priority_alpha must be finite and non-negative")
        if not np.isfinite(priority_epsilon) or priority_epsilon <= 0.0:
            raise ValueError("priority_epsilon must be finite and positive")

        self.capacity = capacity
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.reward_dim = reward_dim
        self.num_heads = num_heads
        self.bootstrap_probability = bootstrap_probability
        self.device = device
        self.rng = np.random.default_rng(seed)
        self.bootstrap_rng = np.random.default_rng(np.random.SeedSequence([seed, 1]))
        self.success_rng = np.random.default_rng(np.random.SeedSequence([seed, 2]))
        self.diagnostic_rng = np.random.default_rng(np.random.SeedSequence([seed, 3]))
        self.sampling = sampling
        self.priority_alpha = priority_alpha
        self.priority_epsilon = priority_epsilon

        self.states = np.zeros((capacity, state_dim), dtype=np.float32)
        self.actions = np.zeros(capacity, dtype=np.int64)
        self.rewards = np.zeros((capacity, reward_dim), dtype=np.float32)
        self.next_states = np.zeros((capacity, state_dim), dtype=np.float32)
        self.terminated = np.zeros(capacity, dtype=np.float32)
        self.truncated = np.zeros(capacity, dtype=np.float32)
        self.behavior_preferences = np.zeros((capacity, reward_dim), dtype=np.float32)
        self.bootstrap_masks = np.zeros((capacity, num_heads), dtype=np.float32)
        self.priorities = np.zeros(capacity, dtype=np.float64)
        self.trajectory_ids = np.full(capacity, -1, dtype=np.int64)
        self.generations = np.zeros(capacity, dtype=np.int64)
        self.eligible_success = np.zeros(capacity, dtype=np.bool_)
        self.relabel_preferences = np.zeros((capacity, reward_dim), dtype=np.float32)
        self._eligible_trajectories: dict[int, list[ReplayHandle]] = {}
        self._sampled_trajectory_ids: set[int] = set()
        self._label_histogram: dict[int, int] = {}
        self._effective_label_histogram: dict[int, int] = {}
        self._pool_indices = np.full(capacity, -1, dtype=np.int64)
        self._eligible_cache_dirty = False
        self._audit_counters: dict[str, float | int] = {
            "completed_trajectories": 0,
            "eligible_trajectories": 0,
            "eligible_transitions": 0,
            "success_positions_requested": 0,
            "success_positions_sampled": 0,
            "uniform_positions_sampled": 0,
            "fallback_positions": 0,
            "relabel_attempt_positions": 0,
            "relabel_changed_positions": 0,
            "projection_distance_sum": 0.0,
            "projection_distance_max": 0.0,
        }

        self.ptr = 0
        self.size = 0

    def add(
        self,
        state: np.ndarray,
        action: int,
        reward: np.ndarray,
        next_state: np.ndarray,
        terminated: bool,
        truncated: bool,
        behavior_preference: np.ndarray,
        bootstrap_mask: np.ndarray | None = None,
        trajectory_id: int = -1,
    ) -> ReplayHandle:
        preference = np.asarray(behavior_preference, dtype=np.float32)
        if preference.shape != (self.reward_dim,):
            raise ValueError(f"Expected preference shape {(self.reward_dim,)}, got {preference.shape}")
        if np.any(preference < 0.0) or not np.isclose(preference.sum(), 1.0, atol=1e-5):
            raise ValueError("behavior_preference must lie on the probability simplex")

        mask = self._make_bootstrap_mask() if bootstrap_mask is None else np.asarray(bootstrap_mask, dtype=np.float32)
        if mask.shape != (self.num_heads,):
            raise ValueError(f"Expected bootstrap mask shape {(self.num_heads,)}, got {mask.shape}")
        if not np.any(mask > 0.0):
            raise ValueError("At least one bootstrap head must receive each transition")

        index = self.ptr
        self.generations[index] += 1
        handle = ReplayHandle(index, int(self.generations[index]))
        new_priority = (
            float(self.priorities[: self.size].max()) if self.sampling == "prioritized" and self.size else 1.0
        )
        if self.eligible_success[index]:
            self._eligible_cache_dirty = True
        self.states[index] = np.asarray(state, dtype=np.float32)
        self.actions[index] = action
        self.rewards[index] = np.asarray(reward, dtype=np.float32)
        self.next_states[index] = np.asarray(next_state, dtype=np.float32)
        self.terminated[index] = float(terminated)
        self.truncated[index] = float(truncated)
        self.behavior_preferences[index] = preference
        self.bootstrap_masks[index] = mask
        self.priorities[index] = new_priority
        self.trajectory_ids[index] = trajectory_id
        self.eligible_success[index] = False
        self._pool_indices[index] = -1
        self.relabel_preferences[index] = preference

        self.ptr = (self.ptr + 1) % self.capacity
        self.size = min(self.size + 1, self.capacity)
        return handle

    def _make_bootstrap_mask(self) -> np.ndarray:
        mask = self.bootstrap_rng.binomial(1, self.bootstrap_probability, size=self.num_heads).astype(np.float32)
        if not np.any(mask):
            mask[self.bootstrap_rng.integers(self.num_heads)] = 1.0
        return mask

    def complete_trajectory(
        self,
        handles: Sequence[ReplayHandle],
        trajectory_id: int,
        discounted_return: np.ndarray,
        preference_pool: np.ndarray,
        ore_objective_indices: Sequence[int] = (0, 1),
    ) -> dict[str, float | int | bool | list[float]]:
        """Finalize one complete episode and register eligible success metadata."""
        episode_return = np.asarray(discounted_return, dtype=np.float64)
        pool = np.asarray(preference_pool, dtype=np.float64)
        if episode_return.shape != (self.reward_dim,) or not np.all(np.isfinite(episode_return)):
            raise ValueError("discounted_return must be a finite reward-dimension vector")
        if pool.ndim != 2 or pool.shape[1] != self.reward_dim or not np.all(np.isfinite(pool)):
            raise ValueError("preference_pool must be a finite matrix with reward_dim columns")
        if np.any(pool < 0.0) or not np.allclose(pool.sum(axis=1), 1.0, atol=1e-5):
            raise ValueError("preference_pool rows must lie on the probability simplex")
        ore_indices = np.asarray(tuple(ore_objective_indices), dtype=np.int64)
        if ore_indices.size == 0 or np.any(ore_indices < 0) or np.any(ore_indices >= self.reward_dim):
            raise ValueError("ore_objective_indices are invalid")

        valid_handles = [handle for handle in handles if self._handle_matches(handle, trajectory_id)]
        if len(valid_handles) != len(handles):
            raise ValueError("trajectory contains stale or mismatched replay handles")
        if not handles or not (self.terminated[handles[-1].buffer_index] or self.truncated[handles[-1].buffer_index]):
            raise ValueError("Only a completed episode may be finalized")
        eligible = bool(np.any(episode_return[ore_indices] > 0.0))
        self._audit_counters["completed_trajectories"] += 1
        result: dict[str, float | int | bool | list[float]] = {
            "trajectory_id": trajectory_id,
            "eligible": eligible,
            "transition_count": len(valid_handles),
            "discounted_return": episode_return.tolist(),
        }
        if not eligible:
            return result

        softplus = np.logaddexp(0.0, episode_return)
        continuous = softplus / softplus.sum()
        distances = np.linalg.norm(pool - continuous[None, :], axis=1)
        pool_index = int(np.argmin(distances))
        projected = pool[pool_index].astype(np.float32)
        distance = float(distances[pool_index])
        for handle in valid_handles:
            index = handle.buffer_index
            self.eligible_success[index] = True
            self.relabel_preferences[index] = projected
            self._pool_indices[index] = pool_index
        self._eligible_trajectories[trajectory_id] = list(valid_handles)
        self._label_histogram[pool_index] = self._label_histogram.get(pool_index, 0) + 1
        self._audit_counters["eligible_trajectories"] += 1
        self._audit_counters["eligible_transitions"] += len(valid_handles)
        self._audit_counters["projection_distance_sum"] += distance
        self._audit_counters["projection_distance_max"] = max(
            float(self._audit_counters["projection_distance_max"]), distance
        )
        result.update(
            {
                "projected_pool_index": pool_index,
                "projected_preference": projected.tolist(),
                "projection_distance": distance,
            }
        )
        return result

    def _handle_matches(self, handle: ReplayHandle, trajectory_id: int | None = None) -> bool:
        if handle.buffer_index < 0 or handle.buffer_index >= self.size:
            return False
        if int(self.generations[handle.buffer_index]) != handle.generation:
            return False
        return trajectory_id is None or int(self.trajectory_ids[handle.buffer_index]) == trajectory_id

    def _eligible_handles(self, trajectory_id: int) -> list[ReplayHandle]:
        handles = [
            handle
            for handle in self._eligible_trajectories.get(trajectory_id, [])
            if self._handle_matches(handle, trajectory_id) and self.eligible_success[handle.buffer_index]
        ]
        if handles:
            self._eligible_trajectories[trajectory_id] = handles
        else:
            self._eligible_trajectories.pop(trajectory_id, None)
        return handles

    def sampling_probabilities(self) -> np.ndarray:
        if self.size == 0:
            raise ValueError("Cannot sample from an empty replay buffer")
        if self.sampling == "uniform":
            return np.full(self.size, 1.0 / self.size, dtype=np.float64)
        scaled = np.power(self.priorities[: self.size], self.priority_alpha)
        return scaled / scaled.sum()

    def sample(
        self,
        batch_size: int,
        beta: float = 1.0,
        successful_fraction: float = 0.0,
        relabel_success: bool = False,
    ) -> ReplayBatch:
        if self.size == 0:
            raise ValueError("Cannot sample from an empty replay buffer")
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        if not 0.0 <= beta <= 1.0:
            raise ValueError("beta must be in [0, 1]")
        if not 0.0 <= successful_fraction <= 1.0:
            raise ValueError("successful_fraction must be in [0, 1]")
        if successful_fraction > 0.0 and self.sampling != "uniform":
            raise ValueError("successful trajectory stratification requires uniform base replay")
        requested_success = round(batch_size * successful_fraction)
        success_indices: list[int] = []
        if self._eligible_cache_dirty:
            for trajectory_id in list(self._eligible_trajectories):
                self._eligible_handles(trajectory_id)
            self._eligible_cache_dirty = False
        eligible_ids = sorted(self._eligible_trajectories)
        while len(success_indices) < requested_success and eligible_ids:
            trajectory_position = int(self.success_rng.integers(0, len(eligible_ids)))
            trajectory_id = eligible_ids[trajectory_position]
            handles = self._eligible_trajectories[trajectory_id]
            handle = handles[int(self.success_rng.integers(0, len(handles)))]
            success_indices.append(handle.buffer_index)
        uniform_count = batch_size - len(success_indices)
        if self.sampling == "uniform":
            uniform_indices = self.rng.integers(0, self.size, size=uniform_count)
            indices = np.concatenate((np.asarray(success_indices, dtype=np.int64), uniform_indices))
            importance_weights = np.ones(batch_size, dtype=np.float32)
        else:
            probabilities = self.sampling_probabilities()
            indices = self.rng.choice(self.size, size=batch_size, replace=True, p=probabilities)
            importance_weights = np.power(self.size * probabilities[indices], -beta)
            importance_weights = (importance_weights / importance_weights.max()).astype(np.float32)
        origins = np.zeros(batch_size, dtype=np.float32)
        origins[: len(success_indices)] = 1.0
        effective_preferences = self.behavior_preferences[indices].copy()
        eligible_sampled = self.eligible_success[indices]
        if relabel_success:
            effective_preferences[eligible_sampled] = self.relabel_preferences[indices][eligible_sampled]
        changed = np.any(
            np.abs(effective_preferences - self.behavior_preferences[indices]) > 1e-7,
            axis=1,
        )
        self._audit_counters["success_positions_requested"] += requested_success
        self._audit_counters["success_positions_sampled"] += len(success_indices)
        self._audit_counters["uniform_positions_sampled"] += uniform_count
        self._audit_counters["fallback_positions"] += requested_success - len(success_indices)
        self._audit_counters["relabel_attempt_positions"] += (
            int(np.count_nonzero(eligible_sampled)) if relabel_success else 0
        )
        self._audit_counters["relabel_changed_positions"] += int(np.count_nonzero(changed))
        self._sampled_trajectory_ids.update(int(value) for value in self.trajectory_ids[indices] if value >= 0)
        if relabel_success:
            labels, counts = np.unique(self._pool_indices[indices][eligible_sampled], return_counts=True)
            for label, count in zip(labels, counts, strict=True):
                self._effective_label_histogram[int(label)] = self._effective_label_histogram.get(int(label), 0) + int(
                    count
                )
        return ReplayBatch(
            states=torch.as_tensor(self.states[indices], device=self.device),
            actions=torch.as_tensor(self.actions[indices], device=self.device),
            rewards=torch.as_tensor(self.rewards[indices], device=self.device),
            next_states=torch.as_tensor(self.next_states[indices], device=self.device),
            terminated=torch.as_tensor(self.terminated[indices], device=self.device),
            truncated=torch.as_tensor(self.truncated[indices], device=self.device),
            behavior_preferences=torch.as_tensor(self.behavior_preferences[indices], device=self.device),
            bootstrap_masks=torch.as_tensor(self.bootstrap_masks[indices], device=self.device),
            indices=indices,
            importance_weights=torch.as_tensor(importance_weights, device=self.device),
            effective_preferences=torch.as_tensor(effective_preferences, device=self.device),
            sample_origins=torch.as_tensor(origins, device=self.device),
            trajectory_ids=torch.as_tensor(self.trajectory_ids[indices], device=self.device),
        )

    def update_priorities(self, indices: np.ndarray, td_errors: np.ndarray) -> None:
        replay_indices = np.asarray(indices, dtype=np.int64)
        errors = np.asarray(td_errors, dtype=np.float64)
        if replay_indices.shape != errors.shape:
            raise ValueError("indices and td_errors must have the same shape")
        if np.any(replay_indices < 0) or np.any(replay_indices >= self.size):
            raise ValueError("priority update index is outside the replay buffer")
        if not np.all(np.isfinite(errors)) or np.any(errors < 0.0):
            raise ValueError("td_errors must be finite and non-negative")
        self.priorities[replay_indices] = errors + self.priority_epsilon

    def sample_states(self, batch_size: int) -> torch.Tensor:
        if self.size == 0:
            raise ValueError("Cannot sample from an empty replay buffer")
        indices = self.diagnostic_rng.integers(0, self.size, size=batch_size)
        return torch.as_tensor(self.states[indices], device=self.device)

    def replay_audit(self) -> dict[str, float | int]:
        counters = dict(self._audit_counters)
        counters["live_eligible_trajectory_count"] = sum(
            bool(self._eligible_handles(trajectory_id)) for trajectory_id in list(self._eligible_trajectories)
        )
        counters["unique_sampled_trajectory_count"] = len(self._sampled_trajectory_ids)
        counters["distinct_projected_labels"] = len(self._label_histogram)
        counters["distinct_effective_relabel_labels"] = len(self._effective_label_histogram)
        return counters

    def replay_histograms(self) -> dict[str, dict[str, int]]:
        return {
            "projected_episode_label_counts": {str(key): value for key, value in self._label_histogram.items()},
            "effective_relabel_position_counts": {
                str(key): value for key, value in self._effective_label_histogram.items()
            },
        }

    def __len__(self) -> int:
        return self.size

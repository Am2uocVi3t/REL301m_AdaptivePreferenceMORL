from __future__ import annotations

from typing import NamedTuple

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
    ) -> None:
        if capacity <= 0 or num_heads <= 0:
            raise ValueError("capacity and num_heads must be positive")
        if not 0.0 < bootstrap_probability <= 1.0:
            raise ValueError("bootstrap_probability must be in (0, 1]")

        self.capacity = capacity
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.reward_dim = reward_dim
        self.num_heads = num_heads
        self.bootstrap_probability = bootstrap_probability
        self.device = device
        self.rng = np.random.default_rng(seed)

        self.states = np.zeros((capacity, state_dim), dtype=np.float32)
        self.actions = np.zeros(capacity, dtype=np.int64)
        self.rewards = np.zeros((capacity, reward_dim), dtype=np.float32)
        self.next_states = np.zeros((capacity, state_dim), dtype=np.float32)
        self.terminated = np.zeros(capacity, dtype=np.float32)
        self.truncated = np.zeros(capacity, dtype=np.float32)
        self.behavior_preferences = np.zeros((capacity, reward_dim), dtype=np.float32)
        self.bootstrap_masks = np.zeros((capacity, num_heads), dtype=np.float32)

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
    ) -> None:
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

        self.states[self.ptr] = np.asarray(state, dtype=np.float32)
        self.actions[self.ptr] = action
        self.rewards[self.ptr] = np.asarray(reward, dtype=np.float32)
        self.next_states[self.ptr] = np.asarray(next_state, dtype=np.float32)
        self.terminated[self.ptr] = float(terminated)
        self.truncated[self.ptr] = float(truncated)
        self.behavior_preferences[self.ptr] = preference
        self.bootstrap_masks[self.ptr] = mask

        self.ptr = (self.ptr + 1) % self.capacity
        self.size = min(self.size + 1, self.capacity)

    def _make_bootstrap_mask(self) -> np.ndarray:
        mask = self.rng.binomial(1, self.bootstrap_probability, size=self.num_heads).astype(np.float32)
        if not np.any(mask):
            mask[self.rng.integers(self.num_heads)] = 1.0
        return mask

    def sample(self, batch_size: int) -> ReplayBatch:
        if self.size == 0:
            raise ValueError("Cannot sample from an empty replay buffer")
        indices = self.rng.integers(0, self.size, size=batch_size)
        return ReplayBatch(
            states=torch.as_tensor(self.states[indices], device=self.device),
            actions=torch.as_tensor(self.actions[indices], device=self.device),
            rewards=torch.as_tensor(self.rewards[indices], device=self.device),
            next_states=torch.as_tensor(self.next_states[indices], device=self.device),
            terminated=torch.as_tensor(self.terminated[indices], device=self.device),
            truncated=torch.as_tensor(self.truncated[indices], device=self.device),
            behavior_preferences=torch.as_tensor(self.behavior_preferences[indices], device=self.device),
            bootstrap_masks=torch.as_tensor(self.bootstrap_masks[indices], device=self.device),
        )

    def sample_states(self, batch_size: int) -> torch.Tensor:
        if self.size == 0:
            raise ValueError("Cannot sample from an empty replay buffer")
        indices = self.rng.integers(0, self.size, size=batch_size)
        return torch.as_tensor(self.states[indices], device=self.device)

    def __len__(self) -> int:
        return self.size

"""Episode-local vector n-step returns, isolated from the frozen study runners."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

import numpy as np
import torch

from src.models.q_network import VectorQNetwork
from src.models.update import compute_double_dqn_targets


@dataclass
class Transition:
    state: np.ndarray
    action: int
    reward: np.ndarray
    next_state: np.ndarray
    terminated: bool
    truncated: bool
    preference: np.ndarray


@dataclass
class NStepTransition:
    first: Transition
    reward: np.ndarray
    last: Transition
    steps: int


class NStepAccumulator:
    def __init__(self, n: int, gamma: float):
        if n < 1 or not 0 < gamma <= 1:
            raise ValueError("Require n >= 1 and gamma in (0, 1]")
        self.n, self.gamma = n, gamma
        self.pending: deque[Transition] = deque()

    def append(self, transition: Transition) -> list[NStepTransition]:
        if self.pending and not np.array_equal(self.pending[0].preference, transition.preference):
            raise ValueError("Preference must remain fixed within an episode")
        self.pending.append(transition)
        if transition.terminated or transition.truncated:
            return self.flush()
        return [self._pop()] if len(self.pending) >= self.n else []

    def _pop(self) -> NStepTransition:
        items = list(self.pending)[: self.n]
        reward = np.zeros_like(items[0].reward, dtype=np.float64)
        for index, item in enumerate(items):
            reward += self.gamma**index * item.reward
        result = NStepTransition(items[0], reward.astype(np.float32), items[-1], len(items))
        self.pending.popleft()
        return result

    def flush(self) -> list[NStepTransition]:
        """Also usable at budget exhaustion; never invent a terminal flag."""
        result = []
        while self.pending:
            result.append(self._pop())
        return result


def n_step_targets(
    online: VectorQNetwork,
    target: VectorQNetwork,
    next_states: torch.Tensor,
    preferences: torch.Tensor,
    rewards: torch.Tensor,
    terminated: torch.Tensor,
    discounts: torch.Tensor,
) -> torch.Tensor:
    # Unit-discount continuation preserves the existing per-head Double-DQN rule.
    continuation = compute_double_dqn_targets(
        online, target, next_states, preferences, torch.zeros_like(rewards), terminated, 1.0
    )
    return rewards[None] + discounts[None, :, None] * continuation

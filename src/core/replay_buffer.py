import numpy as np
import torch
from typing import Tuple, Optional

class VectorReplayBuffer:
    """
    Experience Replay Buffer supporting multi-dimensional vector rewards r in R^d.
    Transitions can be relabeled with different preferences during update.
    """
    def __init__(self, capacity: int, state_dim: int, action_dim: int, reward_dim: int, device: str = "cpu"):
        self.capacity = capacity
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.reward_dim = reward_dim
        self.device = device

        self.states = np.zeros((capacity, state_dim), dtype=np.float32)
        self.actions = np.zeros(capacity, dtype=np.int64)
        self.rewards = np.zeros((capacity, reward_dim), dtype=np.float32)
        self.next_states = np.zeros((capacity, state_dim), dtype=np.float32)
        self.dones = np.zeros(capacity, dtype=np.float32)

        self.ptr = 0
        self.size = 0

    def add(self, state: np.ndarray, action: int, reward: np.ndarray, next_state: np.ndarray, done: bool):
        """Add a transition to the buffer."""
        self.states[self.ptr] = np.array(state, dtype=np.float32)
        self.actions[self.ptr] = action
        self.rewards[self.ptr] = np.array(reward, dtype=np.float32)
        self.next_states[self.ptr] = np.array(next_state, dtype=np.float32)
        self.dones[self.ptr] = float(done)

        self.ptr = (self.ptr + 1) % self.capacity
        self.size = min(self.size + 1, self.capacity)

    def sample(self, batch_size: int) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """Sample a batch of transitions."""
        indices = np.random.randint(0, self.size, size=batch_size)

        states = torch.as_tensor(self.states[indices], device=self.device)
        actions = torch.as_tensor(self.actions[indices], device=self.device)
        rewards = torch.as_tensor(self.rewards[indices], device=self.device)
        next_states = torch.as_tensor(self.next_states[indices], device=self.device)
        dones = torch.as_tensor(self.dones[indices], device=self.device)

        return states, actions, rewards, next_states, dones

    def sample_states(self, batch_size: int) -> torch.Tensor:
        """Sample only states (useful for bootstrap uncertainty estimation)."""
        indices = np.random.randint(0, self.size, size=batch_size)
        return torch.as_tensor(self.states[indices], device=self.device)

    def __len__(self) -> int:
        return self.size

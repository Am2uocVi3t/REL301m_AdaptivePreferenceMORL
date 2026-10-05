import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Tuple, Optional

class VectorQNetwork(nn.Module):
    """
    Preference-Conditioned Vector Q-Network with Multi-Head Bootstrap Ensemble.
    Takes [s, w] as input and outputs vector Q-values: Q_theta(s, a, w) in R^d for each action.
    """
    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        reward_dim: int,
        hidden_dims: List[int] = [256, 256],
        num_heads: int = 3,
    ):
        super().__init__()
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.reward_dim = reward_dim
        self.num_heads = num_heads

        input_dim = state_dim + reward_dim

        # Shared MLP feature extractor (Trunk)
        layers = []
        curr_dim = input_dim
        for h_dim in hidden_dims:
            layers.append(nn.Linear(curr_dim, h_dim))
            layers.append(nn.ReLU())
            curr_dim = h_dim
        self.trunk = nn.Sequential(*layers)

        # Bootstrap heads: K independent linear output heads
        self.heads = nn.ModuleList([
            nn.Linear(curr_dim, action_dim * reward_dim) for _ in range(num_heads)
        ])

    def forward(self, state: torch.Tensor, preference: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through shared trunk and all bootstrap heads.
        Args:
            state: Tensor shape [B, state_dim]
            preference: Tensor shape [B, reward_dim]
        Returns:
            q_values: Tensor shape [num_heads, B, action_dim, reward_dim]
        """
        x = torch.cat([state, preference], dim=-1)
        feat = self.trunk(x)

        all_head_outputs = []
        for head in self.heads:
            # Output: [B, action_dim * reward_dim] -> [B, action_dim, reward_dim]
            out = head(feat).view(-1, self.action_dim, self.reward_dim)
            all_head_outputs.append(out)

        return torch.stack(all_head_outputs, dim=0)

    def predict_action(
        self,
        state: torch.Tensor,
        preference: torch.Tensor,
        head_idx: int = 0
    ) -> Tuple[int, torch.Tensor]:
        """
        Select scalarized greedy action: a = argmax_a w^T Q(s, a, w).
        Args:
            state: shape [1, state_dim] or [state_dim]
            preference: shape [1, reward_dim] or [reward_dim]
            head_idx: which bootstrap head to use for greedy action
        Returns:
            action (int), scalarized_q_values (torch.Tensor [action_dim])
        """
        if state.ndim == 1:
            state = state.unsqueeze(0)
        if preference.ndim == 1:
            preference = preference.unsqueeze(0)

        # q_values: [num_heads, 1, action_dim, reward_dim]
        q_values = self.forward(state, preference)
        head_q = q_values[head_idx, 0]  # [action_dim, reward_dim]

        # Compute w^T Q for each action: [action_dim]
        scalarized_q = torch.matmul(head_q, preference[0])
        action = torch.argmax(scalarized_q).item()

        return action, scalarized_q

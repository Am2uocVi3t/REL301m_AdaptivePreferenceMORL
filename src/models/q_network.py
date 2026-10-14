from __future__ import annotations

from collections.abc import Sequence

import torch
from torch import nn


class VectorQNetwork(nn.Module):
    """
    Preference-conditioned vector Q-network with a masked multi-head ensemble.
    Takes [s, w] as input and outputs vector Q-values: Q_theta(s, a, w) in R^d for each action.
    """

    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        reward_dim: int,
        hidden_dims: Sequence[int] = (256, 256),
        num_heads: int = 3,
    ):
        super().__init__()
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.reward_dim = reward_dim
        self.num_heads = num_heads

        input_dim = state_dim + reward_dim

        layers: list[nn.Module] = []
        curr_dim = input_dim
        for h_dim in hidden_dims:
            layers.append(nn.Linear(curr_dim, h_dim))
            layers.append(nn.ReLU())
            curr_dim = h_dim
        self.trunk = nn.Sequential(*layers)

        self.heads = nn.ModuleList([nn.Linear(curr_dim, action_dim * reward_dim) for _ in range(num_heads)])

    def forward(self, state: torch.Tensor, preference: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through shared trunk and all bootstrap heads.
        Args:
            state: Tensor shape [B, state_dim]
            preference: Tensor shape [B, reward_dim]
        Returns:
            q_values: Tensor shape [num_heads, B, action_dim, reward_dim]
        """
        if state.ndim != 2 or preference.ndim != 2:
            raise ValueError("state and preference must both have shape [batch, features]")
        if state.shape[0] != preference.shape[0]:
            raise ValueError("state and preference batch sizes must match")
        if state.shape[1] != self.state_dim or preference.shape[1] != self.reward_dim:
            raise ValueError("state or preference feature dimension does not match the network")

        x = torch.cat([state, preference], dim=-1)
        feat = self.trunk(x)

        all_head_outputs = []
        for head in self.heads:
            out = head(feat).view(-1, self.action_dim, self.reward_dim)
            all_head_outputs.append(out)

        return torch.stack(all_head_outputs, dim=0)

    def predict_action(
        self, state: torch.Tensor, preference: torch.Tensor, head_idx: int | None = 0
    ) -> tuple[int, torch.Tensor]:
        """
        Select scalarized greedy action: a = argmax_a w^T Q(s, a, w).
        Args:
            state: shape [1, state_dim] or [state_dim]
            preference: shape [1, reward_dim] or [reward_dim]
            head_idx: which bootstrap head to use. If None, averages across all K heads.
        Returns:
            action (int), scalarized_q_values (torch.Tensor [action_dim])
        """
        if state.ndim == 1:
            state = state.unsqueeze(0)
        if preference.ndim == 1:
            preference = preference.unsqueeze(0)

        q_values = self.forward(state, preference)
        if head_idx is not None:
            head_q = q_values[head_idx, 0]  # [action_dim, reward_dim]
        else:
            head_q = torch.mean(q_values[:, 0], dim=0)  # Ensemble mean across K heads

        scalarized_q = torch.matmul(head_q, preference[0])
        action = int(torch.argmax(scalarized_q).item())

        return action, scalarized_q

    def update_target(self, target_network: VectorQNetwork, tau: float = 1.0) -> None:
        """
        Updates target network parameters using Polyak averaging:
        theta_target = tau * theta_online + (1 - tau) * theta_target.
        If tau == 1.0, this performs a hard copy.
        """
        if not 0.0 < tau <= 1.0:
            raise ValueError("tau must be in (0, 1]")
        with torch.no_grad():
            for p_online, p_target in zip(self.parameters(), target_network.parameters(), strict=True):
                p_target.data.copy_(tau * p_online.data + (1.0 - tau) * p_target.data)

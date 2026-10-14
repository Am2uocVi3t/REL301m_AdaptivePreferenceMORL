from __future__ import annotations

import torch
import torch.nn.functional as F

from src.models.q_network import VectorQNetwork


def compute_double_dqn_targets(
    online_network: VectorQNetwork,
    target_network: VectorQNetwork,
    next_states: torch.Tensor,
    preferences: torch.Tensor,
    rewards: torch.Tensor,
    terminated: torch.Tensor,
    gamma: float,
) -> torch.Tensor:
    """Compute a separate vector Double-DQN target for every ensemble head."""
    with torch.no_grad():
        online_q = online_network(next_states, preferences)
        scalarized = torch.einsum("kbad,bd->kba", online_q, preferences)
        greedy_actions = scalarized.argmax(dim=-1)

        target_q = target_network(next_states, preferences)
        gather_index = greedy_actions[..., None, None].expand(-1, -1, 1, target_q.shape[-1])
        selected_target_q = target_q.gather(dim=2, index=gather_index).squeeze(2)
        continuation = 1.0 - terminated[None, :, None]
        return rewards[None, :, :] + gamma * continuation * selected_target_q


def masked_bootstrap_loss(
    predicted_q: torch.Tensor,
    target_q: torch.Tensor,
    bootstrap_masks: torch.Tensor,
) -> torch.Tensor:
    """Huber loss where each replay transition trains only its sampled heads."""
    if predicted_q.shape != target_q.shape:
        raise ValueError("predicted_q and target_q must have the same shape")
    expected_mask_shape = (predicted_q.shape[1], predicted_q.shape[0])
    if bootstrap_masks.shape != expected_mask_shape:
        raise ValueError(f"Expected mask shape {expected_mask_shape}, got {tuple(bootstrap_masks.shape)}")

    per_element = F.smooth_l1_loss(predicted_q, target_q, reduction="none").mean(dim=-1)
    head_sample_mask = bootstrap_masks.transpose(0, 1)
    denominator = head_sample_mask.sum().clamp_min(1.0)
    return (per_element * head_sample_mask).sum() / denominator

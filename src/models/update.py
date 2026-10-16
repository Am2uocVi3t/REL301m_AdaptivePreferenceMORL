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


def masked_mean_absolute_td_error(
    predicted_q: torch.Tensor,
    target_q: torch.Tensor,
    bootstrap_masks: torch.Tensor,
) -> torch.Tensor:
    """Mean absolute vector TD error over active heads for each transition."""
    head_sample_mask = _validate_masked_tensors(predicted_q, target_q, bootstrap_masks)
    absolute_error = (target_q - predicted_q).abs()
    active_counts = head_sample_mask.sum(dim=0) * predicted_q.shape[-1]
    return (absolute_error * head_sample_mask[..., None]).sum(dim=(0, 2)) / active_counts


def weighted_masked_huber_loss(
    predicted_q: torch.Tensor,
    target_q: torch.Tensor,
    bootstrap_masks: torch.Tensor,
    importance_weights: torch.Tensor,
) -> torch.Tensor:
    """Apply per-transition importance weights to the masked Huber loss."""
    head_sample_mask = _validate_masked_tensors(predicted_q, target_q, bootstrap_masks)
    if importance_weights.shape != (predicted_q.shape[1],):
        raise ValueError(f"Expected importance weight shape {(predicted_q.shape[1],)}, got {importance_weights.shape}")
    if not torch.all(torch.isfinite(importance_weights)) or torch.any(importance_weights < 0.0):
        raise ValueError("importance_weights must be finite and non-negative")
    per_head_transition = F.smooth_l1_loss(predicted_q, target_q, reduction="none").mean(dim=-1)
    denominator = head_sample_mask.sum().clamp_min(1.0)
    return (per_head_transition * head_sample_mask * importance_weights[None, :]).sum() / denominator


def _validate_masked_tensors(
    predicted_q: torch.Tensor,
    target_q: torch.Tensor,
    bootstrap_masks: torch.Tensor,
) -> torch.Tensor:
    if predicted_q.shape != target_q.shape:
        raise ValueError("predicted_q and target_q must have the same shape")
    expected_mask_shape = (predicted_q.shape[1], predicted_q.shape[0])
    if bootstrap_masks.shape != expected_mask_shape:
        raise ValueError(f"Expected mask shape {expected_mask_shape}, got {tuple(bootstrap_masks.shape)}")
    head_sample_mask = bootstrap_masks.transpose(0, 1)
    if torch.any(head_sample_mask.sum(dim=0) <= 0.0):
        raise ValueError("Each transition must activate at least one bootstrap head")
    return head_sample_mask

"""Prospective P2 vector/scalar Huber intervention; old learners are untouched."""

from __future__ import annotations

import torch
import torch.nn.functional as F

from src.models.update import masked_bootstrap_loss


def recovery_loss(
    prediction: torch.Tensor,
    target: torch.Tensor,
    masks: torch.Tensor,
    preference: torch.Tensor,
    utility_aux_lambda: float,
) -> torch.Tensor:
    if not 0 <= utility_aux_lambda <= 1:
        raise ValueError("Loss mixing coefficient must be in [0,1]")
    if preference.shape != prediction.shape[1:2] + prediction.shape[2:]:
        raise ValueError("One reward-dimensional preference is required per replay row")
    vector = masked_bootstrap_loss(prediction, target, masks)
    if utility_aux_lambda == 0:
        return vector
    scalar_td = ((prediction - target) * preference[None]).sum(-1)
    scalar = F.smooth_l1_loss(scalar_td, torch.zeros_like(scalar_td), reduction="none")
    active = masks.T
    auxiliary = (scalar * active).sum() / active.sum().clamp_min(1.0)
    return (1 - utility_aux_lambda) * vector + utility_aux_lambda * auxiliary

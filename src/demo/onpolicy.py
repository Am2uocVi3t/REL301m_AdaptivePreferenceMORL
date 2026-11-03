"""Deterministic categorical actor adapter for the inference-only demo."""

import torch
from torch import nn

from src.models.onpolicy import ActorCritic


class CategoricalDemoPolicy(nn.Module):
    def __init__(self, **architecture: int):
        super().__init__()
        self.network = ActorCritic(**architecture)

    def predict_action(self, state: torch.Tensor, weights: torch.Tensor, head_idx: int | None = None):
        distribution = self.network.distribution(state.unsqueeze(0), weights.unsqueeze(0))
        probabilities = distribution.probs[0]
        return int(probabilities.argmax().item()), probabilities

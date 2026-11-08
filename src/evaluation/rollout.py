from __future__ import annotations

import random
from typing import Any

import numpy as np
import torch

from src.evaluation.protocol import validate_preferences
from src.models.q_network import VectorQNetwork


def evaluate_preferences(
    env: Any,
    q_network: VectorQNetwork,
    preferences: np.ndarray,
    episodes_per_preference: int,
    device: str,
    seed: int,
    discount_factor: float,
    isolate_global_rng: bool = False,
) -> dict[str, Any]:
    """Evaluate a conditioned policy on an immutable preference matrix."""
    if isolate_global_rng:
        numpy_state, python_state = np.random.get_state(), random.getstate()
        try:
            np.random.seed(seed)
            random.seed(seed)
            return evaluate_preferences(
                env, q_network, preferences, episodes_per_preference, device, seed, discount_factor
            )
        finally:
            np.random.set_state(numpy_state)
            random.setstate(python_state)
    if episodes_per_preference <= 0:
        raise ValueError("episodes_per_preference must be positive")
    if not 0.0 < discount_factor <= 1.0:
        raise ValueError("discount_factor must be in (0, 1]")
    preferences = validate_preferences(preferences, q_network.reward_dim)

    was_training = q_network.training
    q_network.eval()
    episode_returns = np.zeros(
        (len(preferences), episodes_per_preference, q_network.reward_dim),
        dtype=np.float32,
    )
    raw_episode_returns = np.zeros_like(episode_returns)
    episode_lengths = np.zeros((len(preferences), episodes_per_preference), dtype=np.int32)

    total_steps = 0
    with torch.no_grad():
        for preference_index, preference in enumerate(preferences):
            preference_tensor = torch.as_tensor(preference, device=device).unsqueeze(0)
            for episode_index in range(episodes_per_preference):
                episode_seed = seed + preference_index * episodes_per_preference + episode_index
                observation, _ = env.reset(seed=episode_seed)
                terminated = truncated = False
                discount = 1.0
                while not (terminated or truncated):
                    state_tensor = torch.as_tensor(observation, dtype=torch.float32, device=device).unsqueeze(0)
                    action, _ = q_network.predict_action(state_tensor, preference_tensor, head_idx=None)
                    observation, reward, terminated, truncated, _ = env.step(action)
                    reward_vector = np.asarray(reward, dtype=np.float32)
                    raw_episode_returns[preference_index, episode_index] += reward_vector
                    episode_returns[preference_index, episode_index] += discount * reward_vector
                    discount *= discount_factor
                    episode_lengths[preference_index, episode_index] += 1
                    total_steps += 1

    q_network.train(was_training)
    return {
        "mean_returns": episode_returns.mean(axis=1),
        "episode_returns": episode_returns,
        "raw_mean_returns": raw_episode_returns.mean(axis=1),
        "raw_episode_returns": raw_episode_returns,
        "episode_lengths": episode_lengths,
        "evaluation_steps": total_steps,
    }

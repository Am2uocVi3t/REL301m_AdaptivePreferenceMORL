from collections.abc import Sequence
from typing import Any

import gymnasium as gym
import numpy as np

try:
    import mo_gymnasium as _mo_gym
except ImportError:
    _mo_gym = None  # type: ignore[assignment]

mo_gym: Any = _mo_gym


class MORewardNormalizeWrapper(gym.RewardWrapper):
    """
    Normalizes multi-objective vector rewards using fixed static scale factors.
    Prevents one objective with large numerical range from dominating the Bellman loss.
    """

    def __init__(self, env: gym.Env, scale_vector: Sequence[float] | np.ndarray):
        super().__init__(env)
        self.scale_vector = np.asarray(scale_vector, dtype=np.float32)
        reward_shape = getattr(getattr(env.unwrapped, "reward_space", None), "shape", None)
        if reward_shape is not None and self.scale_vector.shape != reward_shape:
            raise ValueError(f"Expected reward scale shape {reward_shape}, got {self.scale_vector.shape}")
        if np.any(self.scale_vector <= 0.0):
            raise ValueError("All reward scale values must be positive")

    def reward(self, reward: Any) -> Any:
        return np.asarray(reward, dtype=np.float32) * self.scale_vector


def make_mo_env(
    env_id: str,
    seed: int | None = None,
    reward_scale: Sequence[float] | np.ndarray | None = None,
    render_mode: str | None = None,
    dynamics_shift_config: dict[str, Any] | None = None,
) -> gym.Env:
    """
    Factory function to initialize a Multi-Objective Gymnasium environment.
    """
    shift_config = dynamics_shift_config or {}
    constructor_kwargs = dict(shift_config.get("constructor_kwargs", {}))
    if mo_gym is not None:
        env = mo_gym.make(env_id, render_mode=render_mode, **constructor_kwargs)
    else:
        env = gym.make(env_id, render_mode=render_mode, **constructor_kwargs)

    attribute_overrides = shift_config.get("attribute_overrides", {})
    if attribute_overrides:
        from src.envs.shift import apply_dynamics_shift

        apply_dynamics_shift(env, attribute_overrides)

    if seed is not None:
        env.reset(seed=seed)
        env.action_space.seed(seed)

    if reward_scale is not None:
        env = MORewardNormalizeWrapper(env, reward_scale)

    return env

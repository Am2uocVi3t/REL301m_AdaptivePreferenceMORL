import gymnasium as gym
import numpy as np
from typing import Optional, List, Union

try:
    import mo_gymnasium as mo_gym
except ImportError:
    mo_gym = None

class MORewardNormalizeWrapper(gym.RewardWrapper):
    """
    Normalizes multi-objective vector rewards using fixed static scale factors.
    Prevents one objective with large numerical range from dominating the Bellman loss.
    """
    def __init__(self, env: gym.Env, scale_vector: Union[List[float], np.ndarray]):
        super().__init__(env)
        self.scale_vector = np.asarray(scale_vector, dtype=np.float32)

    def reward(self, reward: np.ndarray) -> np.ndarray:
        return np.asarray(reward, dtype=np.float32) * self.scale_vector

def make_mo_env(
    env_id: str,
    seed: Optional[int] = None,
    reward_scale: Optional[List[float]] = None,
    render_mode: Optional[str] = None
) -> gym.Env:
    """
    Factory function to initialize a Multi-Objective Gymnasium environment.
    """
    if mo_gym is not None:
        env = mo_gym.make(env_id, render_mode=render_mode)
    else:
        # Fallback to standard gymnasium if mo-gymnasium is not yet installed
        env = gym.make(env_id, render_mode=render_mode)

    if seed is not None:
        env.reset(seed=seed)
        env.action_space.seed(seed)

    if reward_scale is not None:
        env = MORewardNormalizeWrapper(env, reward_scale)

    return env

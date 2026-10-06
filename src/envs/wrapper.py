import gymnasium as gym
import numpy as np
from typing import Optional, List, Union, Tuple, Dict, Any

try:
    import mo_gymnasium as mo_gym
except ImportError:
    mo_gym = None

from src.envs.shift import apply_dynamics_shift, MODynamicsShiftRewardWrapper


class MORewardNormalizeWrapper(gym.RewardWrapper):
    """
    Normalizes multi-objective vector rewards using fixed static scale factors.
    Prevents one objective with large numerical range from dominating the Bellman loss.
    """
    def __init__(
        self,
        env: gym.Env,
        scale_vector: Union[List[float], np.ndarray],
        clip_range: Optional[Tuple[float, float]] = None
    ):
        super().__init__(env)
        self.scale_vector = np.asarray(scale_vector, dtype=np.float32)
        self.clip_range = clip_range

    def reward(self, reward: np.ndarray) -> np.ndarray:
        r = np.asarray(reward, dtype=np.float32) * self.scale_vector
        if self.clip_range is not None:
            r = np.clip(r, self.clip_range[0], self.clip_range[1])
        return r


def make_mo_env(
    env_id: str,
    seed: Optional[int] = None,
    dynamics_shift_config: Optional[Union[str, Dict[str, Any]]] = None,
    reward_scale: Optional[Union[List[float], np.ndarray]] = None,
    render_mode: Optional[str] = None
) -> gym.Env:
    """
    Factory function to initialize a Multi-Objective Gymnasium environment.

    Args:
        env_id: Environment identifier (e.g. 'mo-lunar-lander-v2', 'minecart-v0').
        seed: Random seed for environment reset and action space.
        dynamics_shift_config: Optional shift preset name or dictionary of parameters.
        reward_scale: Optional fixed scale factors for multi-objective rewards.
        render_mode: Optional render mode ('rgb_array', 'human', etc.).

    Returns:
        Configured and wrapped Gymnasium environment.
    """
    if mo_gym is not None:
        try:
            env = mo_gym.make(env_id, render_mode=render_mode)
        except Exception as e:
            # Fallback between mo-lunar-lander version deprecations across gymnasium releases
            if "mo-lunar-lander-v2" in env_id:
                try:
                    env = mo_gym.make("mo-lunar-lander-v3", render_mode=render_mode)
                except Exception:
                    raise e
            elif "mo-lunar-lander-v3" in env_id:
                try:
                    env = mo_gym.make("mo-lunar-lander-v2", render_mode=render_mode)
                except Exception:
                    raise e
            else:
                raise e
    else:
        # Fallback to standard gymnasium if mo-gymnasium is not yet installed
        env = gym.make(env_id, render_mode=render_mode)

    if seed is not None:
        env.reset(seed=seed)
        env.action_space.seed(seed)

    if dynamics_shift_config is not None:
        apply_dynamics_shift(env, dynamics_shift_config, env_id=env_id)
        env = MODynamicsShiftRewardWrapper(env, dynamics_shift_config)

    if reward_scale is not None:
        env = MORewardNormalizeWrapper(env, reward_scale)

    return env

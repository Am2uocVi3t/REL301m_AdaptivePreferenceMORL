import os
import yaml
import gymnasium as gym
import numpy as np
from typing import Dict, Any, Union, Optional

DEFAULT_SHIFTS: Dict[str, Dict[str, Dict[str, Any]]] = {
    "mo-lunar-lander-v2": {
        "nominal": {
            "gravity": -10.0,
            "enable_wind": False,
            "wind_power": 0.0,
            "turbulence_power": 0.0,
        },
        "heavy_gravity": {
            "gravity": -15.0,
            "enable_wind": False,
            "wind_power": 0.0,
            "turbulence_power": 0.0,
        },
        "strong_wind": {
            "gravity": -10.0,
            "enable_wind": True,
            "wind_power": 15.0,
            "turbulence_power": 0.5,
        },
        "extreme_turbulence": {
            "gravity": -8.0,
            "enable_wind": True,
            "wind_power": 20.0,
            "turbulence_power": 1.5,
        },
    },
    "mo-lunar-lander-v3": {
        "nominal": {
            "gravity": -10.0,
            "enable_wind": False,
            "wind_power": 0.0,
            "turbulence_power": 0.0,
        },
        "heavy_gravity": {
            "gravity": -15.0,
            "enable_wind": False,
            "wind_power": 0.0,
            "turbulence_power": 0.0,
        },
        "strong_wind": {
            "gravity": -10.0,
            "enable_wind": True,
            "wind_power": 15.0,
            "turbulence_power": 0.5,
        },
        "extreme_turbulence": {
            "gravity": -8.0,
            "enable_wind": True,
            "wind_power": 20.0,
            "turbulence_power": 1.5,
        },
    },
    "minecart-v0": {
        "nominal": {
            "fuel_cost_multiplier": 1.0,
            "ore_multiplier": 1.0,
        },
        "high_friction": {
            "fuel_cost_multiplier": 1.5,
            "ore_multiplier": 1.0,
        },
        "low_ore_yield": {
            "fuel_cost_multiplier": 1.0,
            "ore_multiplier": 0.7,
        },
    },
}


def load_shifts_config(config_path: Optional[str] = None) -> Dict[str, Dict[str, Dict[str, Any]]]:
    """Loads dynamics shifts from yaml file or falls back to DEFAULT_SHIFTS."""
    if config_path is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        config_path = os.path.join(base_dir, "configs", "shifts", "dynamics_shifts.yaml")

    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if isinstance(data, dict):
                    if "mo-lunar-lander-v2" in data and "mo-lunar-lander-v3" not in data:
                        data["mo-lunar-lander-v3"] = data["mo-lunar-lander-v2"]
                    return data
        except Exception:
            pass
    return DEFAULT_SHIFTS


def get_dynamics_shifts(env_id: str) -> Dict[str, Dict[str, Any]]:
    """Retrieves all preset dynamics shifts for a given environment ID."""
    all_shifts = load_shifts_config()
    clean_id = env_id.lower().replace("_", "-")

    if "lunar" in clean_id:
        return all_shifts.get("mo-lunar-lander-v2", DEFAULT_SHIFTS["mo-lunar-lander-v2"])
    elif "minecart" in clean_id:
        return all_shifts.get("minecart-v0", DEFAULT_SHIFTS["minecart-v0"])

    return all_shifts.get(env_id, {"nominal": {}})


def apply_dynamics_shift(
    env: gym.Env,
    shift_config: Union[str, Dict[str, Any]],
    env_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Applies environment dynamics perturbations (wind, gravity, friction)
    to test zero-shot robustness under dynamics shift.

    Args:
        env: Target Gymnasium environment.
        shift_config: Either a dictionary of shift parameters or a preset name.
        env_id: Optional environment identifier string for resolving preset names.

    Returns:
        Dict of applied shift parameters.
    """
    unwrapped = env.unwrapped
    resolved_id = env_id or (getattr(unwrapped, "spec", None) and getattr(unwrapped.spec, "id", None)) or "mo-lunar-lander-v2"

    if isinstance(shift_config, str):
        presets = get_dynamics_shifts(resolved_id)
        if shift_config not in presets:
            raise ValueError(f"Unknown shift preset '{shift_config}' for env '{resolved_id}'. Available: {list(presets.keys())}")
        config = presets[shift_config]
    else:
        config = shift_config

    env._active_dynamics_shift = config

    # 1. MO-LunarLander specific dynamics shifts
    if hasattr(unwrapped, "gravity") and "gravity" in config:
        unwrapped.gravity = float(config["gravity"])
        if hasattr(unwrapped, "world") and unwrapped.world is not None:
            unwrapped.world.gravity = (0, unwrapped.gravity)

    if hasattr(unwrapped, "enable_wind") and "enable_wind" in config:
        unwrapped.enable_wind = bool(config["enable_wind"])

    if hasattr(unwrapped, "wind_power") and "wind_power" in config:
        unwrapped.wind_power = float(config["wind_power"])

    if hasattr(unwrapped, "turbulence_power") and "turbulence_power" in config:
        unwrapped.turbulence_power = float(config["turbulence_power"])

    # 2. Minecart specific dynamics shifts
    if hasattr(unwrapped, "fuel_cost") and "fuel_cost_multiplier" in config:
        if not hasattr(unwrapped, "_base_fuel_cost"):
            unwrapped._base_fuel_cost = unwrapped.fuel_cost
        unwrapped.fuel_cost = unwrapped._base_fuel_cost * float(config["fuel_cost_multiplier"])

    return config


class MODynamicsShiftRewardWrapper(gym.RewardWrapper):
    """
    Applies reward multipliers specified in dynamics shift configurations
    (e.g., fuel_cost_multiplier, ore_multiplier for minecart).
    """
    def __init__(self, env: gym.Env, shift_config: Union[str, Dict[str, Any]]):
        super().__init__(env)
        if isinstance(shift_config, str):
            unwrapped = env.unwrapped
            resolved_id = getattr(unwrapped, "spec", None) and getattr(unwrapped.spec, "id", None) or "minecart-v0"
            presets = get_dynamics_shifts(resolved_id)
            self.shift_config = presets.get(shift_config, {})
        else:
            self.shift_config = shift_config

    def reward(self, reward: np.ndarray) -> np.ndarray:
        r = np.asarray(reward, dtype=np.float32).copy()
        # For Minecart (3 objectives: [ore_1, ore_2, fuel])
        if len(r) == 3:
            if "ore_multiplier" in self.shift_config:
                r[0:2] *= float(self.shift_config["ore_multiplier"])
            if "fuel_cost_multiplier" in self.shift_config:
                r[2] *= float(self.shift_config["fuel_cost_multiplier"])
        return r

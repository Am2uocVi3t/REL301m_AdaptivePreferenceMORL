import gymnasium as gym
from typing import Dict, Any

def apply_dynamics_shift(env: gym.Env, shift_config: Dict[str, Any]):
    """
    Applies environment dynamics perturbations (wind, gravity, friction)
    to test zero-shot robustness under dynamics shift.
    """
    unwrapped = env.unwrapped

    # MO-LunarLander specific dynamics shifts
    if hasattr(unwrapped, "gravity") and "gravity" in shift_config:
        unwrapped.gravity = float(shift_config["gravity"])

    if hasattr(unwrapped, "enable_wind") and "enable_wind" in shift_config:
        unwrapped.enable_wind = bool(shift_config["enable_wind"])

    if hasattr(unwrapped, "wind_power") and "wind_power" in shift_config:
        unwrapped.wind_power = float(shift_config["wind_power"])

    if hasattr(unwrapped, "turbulence_power") and "turbulence_power" in shift_config:
        unwrapped.turbulence_power = float(shift_config["turbulence_power"])

    # Minecart specific dynamics shifts
    if hasattr(unwrapped, "fuel_cost") and "fuel_cost_multiplier" in shift_config:
        unwrapped.fuel_cost *= float(shift_config["fuel_cost_multiplier"])

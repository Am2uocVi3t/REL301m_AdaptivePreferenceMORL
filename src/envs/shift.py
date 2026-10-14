from typing import Any


def apply_dynamics_shift(env: Any, shift_config: dict[str, Any]) -> None:
    """
    Applies environment dynamics perturbations (wind, gravity, friction)
    to test zero-shot robustness under dynamics shift.
    """
    unwrapped = env.unwrapped

    missing = [name for name in shift_config if not hasattr(unwrapped, name)]
    if missing:
        raise ValueError(
            "Shift requested attributes that the constructed environment does not expose: " + ", ".join(sorted(missing))
        )
    for name, value in shift_config.items():
        setattr(unwrapped, name, value)
        if getattr(unwrapped, name) != value:
            raise RuntimeError(f"Failed to apply dynamics shift for attribute {name}")

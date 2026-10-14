import os
from typing import Any


def load_config(config_path: str) -> dict[str, Any]:
    """Load a YAML configuration file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found at: {config_path}")
    try:
        import yaml
    except ImportError as error:
        raise RuntimeError("Loading YAML configuration requires PyYAML") from error
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)

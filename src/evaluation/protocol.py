from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np


def validate_preferences(preferences: np.ndarray, reward_dim: int) -> np.ndarray:
    values = np.asarray(preferences, dtype=np.float32)
    if values.ndim != 2 or values.shape[1] != reward_dim:
        raise ValueError(f"Expected preferences with shape [N, {reward_dim}], got {values.shape}")
    if not np.all(np.isfinite(values)) or np.any(values < 0.0):
        raise ValueError("Preferences must be finite and non-negative")
    if not np.allclose(values.sum(axis=1), 1.0, atol=1e-5):
        raise ValueError("Every preference must sum to one")
    return values


def generate_preferences(reward_dim: int, count: int, seed: int) -> np.ndarray:
    if count <= 0:
        raise ValueError("Preference count must be positive")
    rng = np.random.default_rng(seed)
    return rng.dirichlet(np.ones(reward_dim), size=count).astype(np.float32)


def load_protocol(path: str | Path, split: str = "validation") -> tuple[dict[str, Any], np.ndarray]:
    protocol_path = Path(path)
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    reward_dim = int(protocol["reward_dim"])
    split_spec = protocol["preference_splits"][split]

    if "values" in split_spec:
        preferences = np.asarray(split_spec["values"], dtype=np.float32)
    else:
        preferences = generate_preferences(reward_dim, int(split_spec["count"]), int(split_spec["seed"]))
    return protocol, validate_preferences(preferences, reward_dim)


def protocol_hash(protocol: dict[str, Any]) -> str:
    canonical = json.dumps(protocol, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def resolve_reference_point(protocol: dict[str, Any]) -> np.ndarray | None:
    value = protocol.get("reference_point")
    if value is None:
        return None
    return np.asarray(value, dtype=np.float32)


def resolve_reward_scale(protocol: dict[str, Any]) -> np.ndarray:
    reward_dim = int(protocol["reward_dim"])
    value = protocol.get("reward_scale", [1.0] * reward_dim)
    scale = np.asarray(value, dtype=np.float32)
    if scale.shape != (reward_dim,) or np.any(scale <= 0.0):
        raise ValueError("reward_scale must contain one positive value per objective")
    return scale


def resolve_training_pool_size(protocol: dict[str, Any], requested: int | None = None) -> int:
    pool_spec = protocol.get("training_preference_pool", {})
    if "count" not in pool_spec:
        raise ValueError("Protocol must define training_preference_pool.count")
    protocol_count = int(pool_spec["count"])
    if protocol_count <= 0:
        raise ValueError("training_preference_pool.count must be positive")
    if requested is not None and requested != protocol_count:
        raise ValueError("--pool-size must match protocol training_preference_pool.count")
    return protocol_count

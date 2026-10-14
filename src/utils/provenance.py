from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from importlib import metadata
from pathlib import Path
from typing import Any

import numpy as np


def collect_provenance(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "config": config,
        "config_sha256": _hash_json(config),
        "git_commit": _git_output("rev-parse", "HEAD"),
        "git_dirty": bool(_git_output("status", "--porcelain")),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "dependencies": {
            name: _package_version(name)
            for name in (
                "numpy",
                "scipy",
                "torch",
                "gymnasium",
                "mo-gymnasium",
                "morl-baselines",
                "pymoo",
            )
        },
    }


def write_json(path: str | Path, payload: dict[str, Any]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=_json_default),
        encoding="utf-8",
    )


def _hash_json(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=_json_default).encode()
    return hashlib.sha256(encoded).hexdigest()


def _git_output(*arguments: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", *arguments],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _package_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def _json_default(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(f"Cannot serialize {type(value).__name__}")

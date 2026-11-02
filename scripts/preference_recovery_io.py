"""Versioned P2 I/O amendment: bounded atomic-JSON retry, no learner changes."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from src.utils.training_recovery import atomic_json as _write_once

AMENDMENT = Path("configs/experiments/preference_recovery_p2_io_v1.json")
QUALIFICATION = Path("research/qualification/preference_recovery_p2_io_v1.json")
RETRIES = 0


def atomic_json_retry(path: Path, payload: Any) -> None:
    """Retry only Windows access/sharing/lock errors for at most 1.575 seconds.

    The original serializer, fsync and replacement remain unchanged. Permanent
    locks and all other errors fail closed; this never retries training jobs.
    """
    global RETRIES
    for attempt in range(8):
        try:
            _write_once(path, payload)
            return
        except PermissionError as exc:
            if getattr(exc, "winerror", None) not in (5, 32, 33) or attempt == 7:
                raise
            RETRIES += 1
            time.sleep(0.025 * 2 ** min(attempt, 4))


def verify_qualification() -> None:
    import hashlib

    receipt = json.loads(QUALIFICATION.read_text())
    if receipt["status"] != "pass":
        raise ValueError("P2 I/O qualification has not passed")
    for name, expected in receipt["source_sha256"].items():
        if hashlib.sha256(Path(name).read_bytes()).hexdigest() != expected:
            raise ValueError(f"Qualified I/O source changed: {name}")

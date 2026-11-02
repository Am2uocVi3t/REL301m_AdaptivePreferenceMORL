"""Extend the original P2 audit with retained-artifact and runtime-I/O receipts."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import analyze_preference_recovery as original
from scripts.preference_recovery_io import AMENDMENT, atomic_json_retry, verify_qualification

ROOT = original.ROOT


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    verify_qualification()
    amendment = json.loads(AMENDMENT.read_text())
    for path, expected in amendment["retained_files"].items():
        if sha(Path(path)) != expected:
            raise ValueError(f"A retained completed artifact changed: {path}")
    segments = []
    for job in amendment["remaining_jobs"]:
        receipts = [json.loads(p.read_text()) for p in (ROOT / "io_segments" / job).glob("*.json")]
        returned = [r for r in receipts if r["status"] == "returned"]
        if not returned:
            raise ValueError(f"Missing runtime I/O receipt for {job}")
        for receipt in receipts:
            assert not receipt["qualification_only"] and not receipt["provenance"]["git_dirty"]
            assert receipt["amendment_sha256"] == sha(AMENDMENT)
            assert receipt["adapter_sha256"] == sha(Path("scripts/preference_recovery_io.py"))
            assert receipt["wrapper_sha256"] == sha(Path("scripts/run_preference_recovery_io.py"))
        segments.extend(receipts)
    # Do not publish a numeric-only PASS before the runtime-I/O checks finish.
    captured = []

    def capture(path: Path, payload: dict) -> None:
        if path != ROOT / "analysis.json":
            raise ValueError("Unexpected audit output path")
        captured.append(payload)

    previous_writer = original.atomic_json
    original.atomic_json = capture
    try:
        original.main()
    finally:
        original.atomic_json = previous_writer
    if len(captured) != 1:
        raise ValueError("Expected exactly one complete numeric-audit result")
    result = captured[0]
    result["io_recovery_amendment"] = {"path": str(AMENDMENT), "sha256": sha(AMENDMENT)}
    result["runtime_io_segments"] = segments
    result["retained_completed_job_count"] = len(amendment["retained_jobs"])
    atomic_json_retry(ROOT / "analysis.json", result)


if __name__ == "__main__":
    if not __debug__:
        raise RuntimeError("Audit assertions must be enabled")
    main()

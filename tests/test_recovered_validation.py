from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.reaudit_recovered_validation import reaudit
from src.evaluation.course_validation import CourseValidationError

ROOT = Path(__file__).resolve().parents[1]


def test_embedded_historical_returns_recompute_without_missing_checkpoints():
    result = reaudit(ROOT)
    assert result["runs"] == 30
    assert result["checkpoints"] == 300
    assert result["episodes"] == 28_800
    assert result["new_environment_steps"] == 0
    assert result["unlocks_final_test"] is False


def test_recovery_reaudit_rejects_metric_tampering(tmp_path):
    aggregate = json.loads((ROOT / "research/evidence/course_primary_validation_v1.json").read_text())
    aggregate["runs"][0]["candidates"][0]["metrics"]["expected_utility"] += 1
    path = tmp_path / "tampered.json"
    path.write_text(json.dumps(aggregate), encoding="utf-8")
    with pytest.raises(CourseValidationError, match="expected utility does not match"):
        reaudit(ROOT, path)

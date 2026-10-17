from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from src.research_harness.aris import action_blockers, installation_errors

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def policy() -> dict:
    return json.loads((ROOT / "configs/aris/project.json").read_text())


@pytest.mark.parametrize("action", ["final-test", "checkpoint-lock", "paid-review", "account-switch", "unknown"])
def test_authority_actions_are_denied(policy: dict, action: str) -> None:
    assert action_blockers(policy, action, 100)


@pytest.mark.parametrize("action", ["scope-change", "protocol-change", "training"])
def test_recorded_f1_authority_actions_are_allowed(policy: dict, action: str) -> None:
    assert action_blockers(policy, action, 100) == []
    assert policy["authorization"]["id"] == "aris-full-workflow-20261017"


@pytest.mark.parametrize("quota", [None, 4, -1, 101, float("nan"), float("inf")])
def test_low_or_unknown_quota_stops_dispatch(policy: dict, quota: float | None) -> None:
    assert action_blockers(policy, "offline-tests", quota)


def test_routine_action_with_sufficient_quota(policy: dict) -> None:
    assert action_blockers(policy, "offline-tests", 10) == []
    assert policy["claude"]["paid_enabled"] is False
    assert policy["resume"]["provisional_advances"] is False
    assert policy["unattended_enabled"] is False


def test_missing_pinned_checkout_fails_closed(tmp_path: Path, policy: dict) -> None:
    policy["upstream_root"] = str(tmp_path / "missing")
    errors, skills, overlays = installation_errors(tmp_path, policy)
    assert errors
    assert skills == overlays == 0


def test_copy_overlay_merges_files_and_detects_drift(tmp_path: Path, policy: dict, monkeypatch) -> None:
    upstream = tmp_path / "upstream"
    project = tmp_path / "project"
    policy["upstream_root"] = str(upstream)
    base = upstream / "skills/skills-codex/review"
    overlay = upstream / "skills/skills-codex-claude-review/review"
    refs = upstream / "skills/skills-codex/shared-references"
    for directory in [base, overlay, refs, upstream / "tools", project / ".agents/skills/review"]:
        directory.mkdir(parents=True)
    (base / "SKILL.md").write_text("base")
    (base / "helper.txt").write_text("helper retained")
    (overlay / "SKILL.md").write_text("overlay")
    (refs / "contract.md").write_text("contract")
    (upstream / "tools/run_state.py").write_text("helper")
    target = project / ".agents/skills/review"
    (target / "SKILL.md").write_text("overlay")
    (target / "helper.txt").write_text("helper retained")
    local_refs = project / ".agents/skills/shared-references"
    local_refs.mkdir()
    (local_refs / "contract.md").write_text("contract")

    def fake_git(args, **kwargs):
        stdout = policy["upstream_commit"] if "rev-parse" in args else ""
        return subprocess.CompletedProcess(args, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(subprocess, "run", fake_git)
    assert installation_errors(project, policy) == ([], 1, 1)
    (target / "SKILL.md").write_text("unexpected")
    assert "review" in installation_errors(project, policy)[0][0]
    (target / "SKILL.md").write_text("overlay")
    (target / "helper.txt").unlink()
    assert installation_errors(project, policy)[0]

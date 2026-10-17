"""Synthetic only: aggregate reconciliation and finite batch dispatch/resume."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import subprocess
from pathlib import Path

import pytest

from scripts import aris_review_guard as guard
from scripts import run_aris_review_batch as batch
from src.research_harness.store import write_registry


def aggregate(root: Path) -> dict:
    (root / "reserved-calls.txt").write_text("reserved\nreserved\n")
    imported = guard.import_legacy(root)
    with sqlite3.connect(root / "usage.sqlite3") as db:
        ids = [row[0] for row in db.execute("SELECT id FROM calls ORDER BY id")]
    return {
        "source": "user_supplied_console_display",
        "status": "reconciled_aggregate",
        "legacy_source_sha256": imported["legacy_source_sha256"],
        "reservation_ids": ids,
        "group_id": "synthetic-historical",
        "console_display_spent_usd": 0.24,
        "display_precision_usd": 0.01,
        "per_invocation_costs_known": False,
        "user_statement": "$0.24 spent (synthetic fixture)",
    }


def test_aggregate_reconciliation_keeps_individual_cost_unknown(tmp_path: Path) -> None:
    report = aggregate(tmp_path)
    before = (tmp_path / "reserved-calls.txt").read_bytes()
    guard.reconcile_aggregate(tmp_path, report, "fixture")
    guard.reconcile_aggregate(tmp_path, report, "fixture")
    with sqlite3.connect(tmp_path / "usage.sqlite3") as db:
        rows = db.execute("SELECT id,reserved,status,metadata FROM calls ORDER BY id").fetchall()
    assert [row[0] for row in rows] == report["reservation_ids"]
    assert sum(row[1] for row in rows) == 0.5
    assert all(row[2] == "reconciled_aggregate" and json.loads(row[3])["actual_cost_usd"] is None for row in rows)
    assert all(json.loads(row[3])["aggregate_console_spent_usd"] == 0.24 for row in rows)
    assert (tmp_path / "reserved-calls.txt").read_bytes() == before


@pytest.mark.parametrize(
    "key,value",
    [
        ("reservation_ids", []),
        ("status", "reconciled"),
        ("console_display_spent_usd", float("nan")),
        ("console_display_spent_usd", 0.6),
        ("per_invocation_costs_known", True),
    ],
)
def test_bad_aggregate_does_not_settle(tmp_path: Path, key, value) -> None:
    report = {**aggregate(tmp_path), key: value}
    with pytest.raises(ValueError):
        guard.reconcile_aggregate(tmp_path, report, "fixture")
    with sqlite3.connect(tmp_path / "usage.sqlite3") as db:
        assert {row[0] for row in db.execute("SELECT status FROM calls")} == {"console_reconciliation_required"}


def setup(project: Path, monkeypatch) -> tuple[Path, dict]:
    bridge = project / "bridge"
    bridge.mkdir()
    report = aggregate(bridge)
    write_registry(bridge / "console-reconciliation.json", report)
    policy = {
        "enabled": False,
        "console_reconciled": True,
        "console_evidence_sha256": batch.sha(bridge / "console-reconciliation.json"),
    }
    write_registry(bridge / "policy.json", policy)
    (project / "docs").mkdir()
    (project / "docs/a.md").write_text("synthetic public artifact")
    (project / "prompt.md").write_text("synthetic prompt")
    write_registry(project / ".aris/preflight.json", {"reported_remaining_percent": 50, "quota_observed_at": "fixture"})
    _, digest = guard.packet(project, ["docs/a.md"])
    spec = {
        "id": "one-fixture",
        "maximum_invocations": 1,
        "invocation_budget_usd": 0.25,
        "total_authorized_envelope_usd": 1,
        "packet_files": ["docs/a.md"],
        "packet_sha256": digest,
        "prompt_file": "prompt.md",
        "prompt_sha256": hashlib.sha256(b"synthetic prompt").hexdigest(),
        "model": "sonnet",
        "timeout_seconds": 10,
    }
    monkeypatch.setattr(batch, "preflight", lambda *args: {"status": "PASS"})
    return bridge, spec


def test_batch_resume_never_repeats_completed_or_running_dispatch(tmp_path: Path, monkeypatch) -> None:
    bridge, spec = setup(tmp_path, monkeypatch)
    invocations = []
    status_polls = []

    def fake_rpc(root, name, arguments):
        if name == "review_start":
            state = json.loads((tmp_path / ".aris/batches/one-fixture/state.json").read_text())
            assert state["status"] == "dispatch_intent"
            invocations.append(name)
            policy = json.loads((bridge / "policy.json").read_text())
            call_id = guard.reserve(bridge / "usage.sqlite3", policy, "fixture")
            guard.record(bridge / "usage.sqlite3", call_id, "complete", {"actual_cost_usd": 0.01})
            return {"jobId": "synthetic-job", "done": False}
        assert arguments["jobId"] == "synthetic-job"
        status_polls.append(name)
        if len(status_polls) == 1:
            return {"done": False}
        return {"done": True, "status": "completed", "response": "synthetic review"}

    monkeypatch.setattr(batch, "rpc", fake_rpc)
    assert batch.step(tmp_path, bridge, spec, True)["status"] == "running"
    assert batch.step(tmp_path, bridge, spec, True)["status"] == "complete"
    assert batch.step(tmp_path, bridge, spec, True)["status"] == "complete"
    assert invocations == ["review_start"] and len(status_polls) == 2
    assert len(batch.calls(bridge, spec["id"])) == 1
    assert json.loads((bridge / "policy.json").read_text())["enabled"] is False


def test_ambiguous_start_is_not_retried(tmp_path: Path, monkeypatch) -> None:
    bridge, spec = setup(tmp_path, monkeypatch)
    attempts = []

    def timeout(*args):
        attempts.append(1)
        raise subprocess.TimeoutExpired("synthetic-mcp", 45)

    monkeypatch.setattr(batch, "rpc", timeout)
    with pytest.raises(subprocess.TimeoutExpired):
        batch.step(tmp_path, bridge, spec, True)
    with pytest.raises(ValueError, match="ambiguous"):
        batch.step(tmp_path, bridge, spec, True)
    assert len(attempts) == 1
    assert json.loads((bridge / "policy.json").read_text())["enabled"] is False

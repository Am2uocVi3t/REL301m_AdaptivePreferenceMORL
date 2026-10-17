"""All provider processes are synthetic Python fixtures; no paid calls."""

from __future__ import annotations

import hashlib
import json
import signal
import sqlite3
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from scripts import aris_review_guard as guard
from src.research_harness.aris import quota_errors


def policy() -> dict:
    return {
        "model": "sonnet",
        "batch_id": "offline-fixture",
        "max_calls": 4,
        "max_budget_usd_per_call": 0.25,
        "batch_budget_usd": 1,
    }


def result() -> dict:
    return {
        "type": "result",
        "session_id": "synthetic-session",
        "result": "fixture review",
        "total_cost_usd": 0.012,
        "usage": {"input_tokens": 30, "output_tokens": 5},
        "modelUsage": {"claude-synthetic-test": {"inputTokens": 30, "outputTokens": 5}},
    }


@pytest.mark.parametrize("encoding", ["object", "array", "ndjson"])
def test_metadata_formats(encoding: str) -> None:
    event = result()
    if encoding == "object":
        raw = json.dumps(event)
    elif encoding == "array":
        raw = json.dumps([{"type": "system"}, event])
    else:
        raw = json.dumps({"type": "system"}) + "\n" + json.dumps(event)
    _, audit = guard.metadata(raw)
    assert audit["actual_models"] == ["claude-synthetic-test"]
    assert audit["actual_cost_usd"] == 0.012
    assert audit["usage"]["input_tokens"] == 30


@pytest.mark.parametrize(
    "key,value",
    [
        ("total_cost_usd", None),
        ("total_cost_usd", float("nan")),
        ("total_cost_usd", -1),
        ("usage", {}),
        ("modelUsage", {}),
        ("session_id", None),
        ("type", "assistant"),
    ],
)
def test_unknown_metadata_rejected(key, value) -> None:
    with pytest.raises(ValueError):
        guard.metadata(json.dumps({**result(), key: value}))


def test_quota_age_timezone_and_clock_skew() -> None:
    now = datetime.now(UTC)
    for observed in [
        None,
        "garbage",
        now.replace(tzinfo=None).isoformat(),
        (now - timedelta(seconds=301)).isoformat(),
        (now + timedelta(seconds=1)).isoformat(),
    ]:
        assert quota_errors(observed, now=now)
    assert not quota_errors((now - timedelta(seconds=300)).isoformat(), now=now)


@pytest.mark.parametrize("entry", ["../docs/a.md", "/etc/passwd", ".aws/key.md", "docs/.env", "docs/a.pdf"])
def test_packet_paths_rejected(tmp_path: Path, entry: str) -> None:
    with pytest.raises(ValueError):
        guard.packet(tmp_path, [entry])


def test_packet_content_and_links(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    artifact = tmp_path / "docs/a.md"
    artifact.write_text("public fixture")
    content, digest = guard.packet(tmp_path, ["docs/a.md"])
    assert "public fixture" in content and len(digest) == 64
    artifact.write_text("api_key=synthetic-secret-value")
    with pytest.raises(ValueError, match="credentials"):
        guard.packet(tmp_path, ["docs/a.md"])
    artifact.unlink()
    artifact.symlink_to(tmp_path / "outside.md")
    with pytest.raises(ValueError, match="symlink"):
        guard.packet(tmp_path, ["docs/a.md"])
    artifact.unlink()
    (tmp_path / "outside.md").write_text("fixture")
    artifact.hardlink_to(tmp_path / "outside.md")
    with pytest.raises(ValueError, match="hardlink"):
        guard.packet(tmp_path, ["docs/a.md"])
    (tmp_path / "src").symlink_to(tmp_path / "docs", target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        guard.packet(tmp_path, ["src/a.md"])


def reserve_worker(path: str) -> str:
    try:
        return guard.reserve(Path(path), policy(), "fixture")
    except ValueError:
        return "blocked"


def test_concurrent_reservations_and_resume(tmp_path: Path) -> None:
    path = tmp_path / "usage.sqlite3"
    with ProcessPoolExecutor(max_workers=4) as pool:
        attempts = list(pool.map(reserve_worker, [str(path)] * 8))
    ids = [value for value in attempts if value != "blocked"]
    assert len(ids) == 1  # single active review; others fail closed
    guard.record(path, ids[0], "unknown_spend", {"failure_type": "SIGKILL"})
    assert reserve_worker(str(path)) == "blocked"
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT SUM(reserved) FROM calls").fetchone()[0] == 0.25


def test_completed_calls_do_not_refund_reserved_capacity(tmp_path: Path) -> None:
    path = tmp_path / "usage.sqlite3"
    for _ in range(4):
        call_id = guard.reserve(path, policy(), "fixture")
        guard.record(path, call_id, "complete", {"actual_cost_usd": 0.001})
    with pytest.raises(ValueError, match="exhausted"):
        guard.reserve(path, policy(), "fixture")


def test_command_boundaries() -> None:
    args = ["-p", "fixture", "--output-format", "json", "--permission-mode", "plan"]
    command = guard.guarded_command(args, policy())
    assert command[command.index("--tools") + 1] == ""
    assert "--no-session-persistence" in command
    for extra in [
        ["--resume", "old-session"],
        ["--tools", "Read"],
        ["--model", "opus"],
        ["--add-dir", "/"],
        ["-p", "duplicate"],
    ]:
        with pytest.raises(ValueError):
            guard.guarded_command(args + extra, policy())


def alive(pid: int) -> bool:
    stat = Path(f"/proc/{pid}/stat")
    deadline = time.monotonic() + 2
    while stat.exists() and stat.read_text().split()[2] != "Z" and time.monotonic() < deadline:
        time.sleep(0.01)
    return stat.exists() and stat.read_text().split()[2] != "Z"


def test_legacy_import_is_idempotent_and_unsettled(tmp_path: Path) -> None:
    source = tmp_path / "reserved-calls.txt"
    source.write_text("reserved\nreserved\n")
    before = source.read_bytes()
    first = guard.import_legacy(tmp_path)
    assert guard.import_legacy(tmp_path) == first
    assert first["reserved_usd"] == 0.5 and first["console_reconciled"] is False
    with pytest.raises(ValueError, match="Unsettled"):
        guard.reserve(tmp_path / "usage.sqlite3", policy(), "fixture")
    assert source.read_bytes() == before


def test_timeout_kills_grandchild(tmp_path: Path) -> None:
    pidfile = tmp_path / "descendant.pid"
    program = (
        "import subprocess,sys,time; from pathlib import Path; "
        "child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); "
        f"Path({str(pidfile)!r}).write_text(str(child.pid)); time.sleep(60)"
    )
    with pytest.raises(TimeoutError):
        guard.run_process([sys.executable, "-c", program], tmp_path, 0.3)
    assert not alive(int(pidfile.read_text()))


@pytest.mark.parametrize("sig", [signal.SIGTERM, signal.SIGINT, signal.SIGKILL])
def test_interrupted_guard_cleans_process_group(tmp_path: Path, sig: int) -> None:
    pidfile = tmp_path / "child.pid"
    fixture = (
        f"import os,time; from pathlib import Path; Path({str(pidfile)!r}).write_text(str(os.getpid())); time.sleep(60)"
    )
    wrapper = (
        "import sys; from pathlib import Path; from scripts.aris_review_guard import run_process; "
        f"run_process([sys.executable,'-c',{fixture!r}],Path({str(tmp_path)!r}),30)"
    )
    proc = subprocess.Popen([sys.executable, "-c", wrapper], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        deadline = time.monotonic() + 5
        while not pidfile.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert pidfile.exists()
        proc.send_signal(sig)
        proc.wait(timeout=5)
        assert not alive(int(pidfile.read_text()))
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=5)


def test_success_kills_detached_pipe_holding_child(tmp_path: Path) -> None:
    pidfile = tmp_path / "child.pid"
    program = (
        "import subprocess,sys; from pathlib import Path; "
        "p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); "
        f"Path({str(pidfile)!r}).write_text(str(p.pid)); print('ok')"
    )
    code, stdout, _ = guard.run_process([sys.executable, "-c", program], tmp_path, 2)
    assert code == 0 and stdout.strip() == "ok"
    assert not alive(int(pidfile.read_text()))


def prepare(tmp_path: Path) -> dict:
    (tmp_path / "project/docs").mkdir(parents=True)
    (tmp_path / "project/docs/review.md").write_text("public fixture")
    _, digest = guard.packet(tmp_path / "project", ["docs/review.md"])
    console = json.dumps({"source": "anthropic_console_export", "status": "reconciled"}).encode()
    (tmp_path / "console-reconciliation.json").write_bytes(console)
    config = {
        **policy(),
        "enabled": True,
        "console_reconciled": True,
        "console_evidence_sha256": hashlib.sha256(console).hexdigest(),
        "quota_observed_at": datetime.now(UTC).isoformat(),
        "codex_remaining_percent": 82,
        "project_root": str(tmp_path / "project"),
        "packet_files": ["docs/review.md"],
        "packet_sha256": digest,
        "timeout_seconds": 3,
    }
    (tmp_path / "policy.json").write_text(json.dumps(config))
    return config


def test_guard_e2e_offline_and_persistent_metadata(tmp_path: Path, monkeypatch) -> None:
    prepare(tmp_path)
    fake = tmp_path / "fake-claude"
    fake.write_text(f"#!{sys.executable}\nprint({json.dumps(result())!r})\n")
    fake.chmod(0o700)
    monkeypatch.setattr(guard, "CLI", fake)
    code, response = guard.execute(
        tmp_path, ["-p", "review fixture", "--output-format", "json", "--permission-mode", "plan"]
    )
    assert code == 0 and response["model"] == "claude-synthetic-test"
    with sqlite3.connect(tmp_path / "usage.sqlite3") as db:
        row = db.execute("SELECT status, metadata FROM calls").fetchone()
        assert row[0] == "complete"
        assert json.loads(row[1])["actual_cost_usd"] == 0.012


def test_disabled_and_historical_gates_do_not_spawn(tmp_path: Path, monkeypatch) -> None:
    config = prepare(tmp_path)

    def forbidden(*args, **kwargs):
        pytest.fail("Provider must never spawn")

    monkeypatch.setattr(guard, "run_process", forbidden)
    for update, match in [({"enabled": False}, "disabled"), ({"console_reconciled": False}, "Console")]:
        (tmp_path / "policy.json").write_text(json.dumps({**config, **update}))
        with pytest.raises(ValueError, match=match):
            guard.execute(tmp_path, [])
    (tmp_path / "policy.json").write_text(json.dumps(config))
    (tmp_path / "reserved-calls.txt").write_text("reserved\nreserved\n")
    with pytest.raises(ValueError, match="historical reservations"):
        guard.execute(tmp_path, [])
    with sqlite3.connect(tmp_path / "usage.sqlite3") as db:
        assert (
            db.execute("SELECT COUNT(*) FROM calls WHERE status='console_reconciliation_required'").fetchone()[0] == 2
        )


def test_synthetic_console_mapping_preserves_old_reservations(tmp_path: Path) -> None:
    config = prepare(tmp_path)
    (tmp_path / "reserved-calls.txt").write_text("reserved\nreserved\n")
    imported = guard.import_legacy(tmp_path)
    with sqlite3.connect(tmp_path / "usage.sqlite3") as db:
        ids = [row[0] for row in db.execute("SELECT id FROM calls ORDER BY id")]
    report = {
        "source": "anthropic_console_export",
        "status": "reconciled",
        "legacy_source_sha256": imported["legacy_source_sha256"],
        "calls": [
            {
                "reservation_id": call_id,
                "session_id": f"fixture-{i}",
                "console_record_id": f"fixture-only-{i}",
                "console_cost_usd": 0.01,
            }
            for i, call_id in enumerate(ids)
        ],
    }
    raw = json.dumps(report).encode()
    (tmp_path / "console-reconciliation.json").write_bytes(raw)
    config["console_evidence_sha256"] = hashlib.sha256(raw).hexdigest()
    guard.check_reconciliation(tmp_path, config)
    guard.check_reconciliation(tmp_path, config)
    with sqlite3.connect(tmp_path / "usage.sqlite3") as db:
        assert db.execute("SELECT SUM(reserved) FROM calls").fetchone()[0] == 0.5
        assert db.execute("SELECT COUNT(*) FROM calls WHERE status='reconciled'").fetchone()[0] == 2
    assert (tmp_path / "reserved-calls.txt").read_text() == "reserved\nreserved\n"


@pytest.mark.parametrize("failure", ["missing_metadata", "timeout", "provider_error", "over_budget"])
def test_failed_review_stops_new_dispatch(tmp_path: Path, monkeypatch, failure: str) -> None:
    config = prepare(tmp_path)
    args = ["-p", "fixture", "--output-format", "json", "--permission-mode", "plan"]
    event = result()
    if failure == "missing_metadata":
        event.pop("usage")
    if failure == "provider_error":
        event["is_error"] = True
    if failure == "over_budget":
        event["total_cost_usd"] = 0.26
    if failure == "timeout":
        config["timeout_seconds"] = 0.1
        (tmp_path / "policy.json").write_text(json.dumps(config))
        program = "import time; time.sleep(60)"
    else:
        program = f"print({json.dumps(event)!r})"
    fake = tmp_path / "provider"
    fake.write_text(f"#!{sys.executable}\n{program}\n")
    fake.chmod(0o700)
    monkeypatch.setattr(guard, "CLI", fake)
    if failure in {"missing_metadata", "timeout"}:
        with pytest.raises((ValueError, TimeoutError)):
            guard.execute(tmp_path, args)
    else:
        assert guard.execute(tmp_path, args)[0] == 1
    with pytest.raises(ValueError, match="Unsettled"):
        guard.execute(tmp_path, args)


def test_output_limit_stops_process(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="guardian stopped"):
        guard.run_process(
            [
                sys.executable,
                "-c",
                "import sys,time; sys.stdout.write('x'*2100000); sys.stdout.flush(); time.sleep(60)",
            ],
            tmp_path,
            2,
        )


def test_packet_drift_never_reserves_or_spawns(tmp_path: Path, monkeypatch) -> None:
    prepare(tmp_path)
    (tmp_path / "project/docs/review.md").write_text("changed after approval")
    with pytest.raises(ValueError, match="changed since approval"):
        guard.execute(tmp_path, ["-p", "fixture", "--output-format", "json", "--permission-mode", "plan"])
    assert not (tmp_path / "usage.sqlite3").exists()


def test_killed_execute_resumes_with_unsettled_reservation(tmp_path: Path, monkeypatch) -> None:
    prepare(tmp_path)
    pidfile = tmp_path / "provider.pid"
    fake = tmp_path / "provider"
    fake.write_text(
        f"#!{sys.executable}\nimport os,time\nfrom pathlib import Path\n"
        f"Path({str(pidfile)!r}).write_text(str(os.getpid()))\ntime.sleep(60)\n"
    )
    fake.chmod(0o700)
    args = ["-p", "fixture", "--output-format", "json", "--permission-mode", "plan"]
    wrapper = (
        "from pathlib import Path; from scripts import aris_review_guard as guard; "
        f"guard.CLI=Path({str(fake)!r}); guard.execute(Path({str(tmp_path)!r}), {args!r})"
    )
    process = subprocess.Popen([sys.executable, "-c", wrapper], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        deadline = time.monotonic() + 5
        while not pidfile.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert pidfile.exists()
        process.kill()
        process.wait(timeout=5)
        assert not alive(int(pidfile.read_text()))
        with sqlite3.connect(tmp_path / "usage.sqlite3") as db:
            assert db.execute("SELECT status, reserved FROM calls").fetchall() == [("reserved", 0.25)]
        monkeypatch.setattr(guard, "CLI", fake)
        with pytest.raises(ValueError, match="Unsettled"):
            guard.execute(tmp_path, args)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)

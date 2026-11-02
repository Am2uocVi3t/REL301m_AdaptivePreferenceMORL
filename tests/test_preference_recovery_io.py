from pathlib import Path

import pytest

from scripts import preference_recovery_io as io


def test_transient_windows_lock_retries_without_changing_payload(tmp_path, monkeypatch):
    calls, delays = [], []
    payload = {"step": 123}

    def writer(path, value):
        calls.append((path, value))
        if len(calls) < 3:
            error = PermissionError("sharing violation")
            error.winerror = 5
            raise error

    monkeypatch.setattr(io, "_write_once", writer)
    monkeypatch.setattr(io.time, "sleep", delays.append)
    io.atomic_json_retry(tmp_path / "heartbeat.json", payload)
    assert len(calls) == 3 and all(value is payload for _, value in calls)
    assert delays == [0.025, 0.05]


def test_permanent_lock_is_bounded_and_other_errors_are_not_retried(monkeypatch):
    calls, delays = [], []

    def writer(*_):
        calls.append(1)
        error = PermissionError("locked")
        error.winerror = 32
        raise error

    monkeypatch.setattr(io, "_write_once", writer)
    monkeypatch.setattr(io.time, "sleep", delays.append)
    with pytest.raises(PermissionError):
        io.atomic_json_retry(Path("ignored.json"), {})
    assert len(calls) == 8 and sum(delays) == pytest.approx(1.575)
    calls.clear()

    def disk_full(*_):
        calls.append(1)
        raise OSError("disk full")

    monkeypatch.setattr(io, "_write_once", disk_full)
    with pytest.raises(OSError, match="disk full"):
        io.atomic_json_retry(Path("ignored.json"), {})
    assert len(calls) == 1


def test_combined_audit_never_publishes_interim_numeric_pass(tmp_path, monkeypatch):
    import json

    from scripts import analyze_preference_recovery_io as audit

    root = tmp_path / "result"
    root.mkdir()
    amendment = tmp_path / "amendment.json"
    amendment.write_text(json.dumps({"retained_files": {}, "remaining_jobs": ["job"], "retained_jobs": []}))
    segment_dir = root / "io_segments/job"
    segment_dir.mkdir(parents=True)
    receipt = {
        "status": "returned",
        "qualification_only": False,
        "provenance": {"git_dirty": False},
        "amendment_sha256": audit.sha(amendment),
        "adapter_sha256": audit.sha(Path("scripts/preference_recovery_io.py")),
        "wrapper_sha256": audit.sha(Path("scripts/run_preference_recovery_io.py")),
    }
    (segment_dir / "one.json").write_text(json.dumps(receipt))
    monkeypatch.setattr(audit, "ROOT", root)
    monkeypatch.setattr(audit, "AMENDMENT", amendment)
    monkeypatch.setattr(audit, "verify_qualification", lambda: None)

    def numeric_audit():
        audit.original.atomic_json(root / "analysis.json", {"audit": "numeric-unit-fixture"})
        assert not (root / "analysis.json").exists()

    monkeypatch.setattr(audit.original, "main", numeric_audit)
    audit.main()
    result = json.loads((root / "analysis.json").read_text())
    assert result["audit"] == "numeric-unit-fixture" and len(result["runtime_io_segments"]) == 1

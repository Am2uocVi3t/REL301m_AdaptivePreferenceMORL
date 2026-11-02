from __future__ import annotations

import json
import threading
import time
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

from monitor import server


def test_append_log_reader_allows_live_writer(tmp_path):
    path = tmp_path / "stdout.log"
    with path.open("a", encoding="utf-8") as writer:
        writer.write("step=25000 updates=5001 sps=200\n")
        writer.flush()
        assert "step=25000" in server.shared_read(path)
        writer.write("step=50000 updates=11251 sps=200\n")
        writer.flush()
        assert "step=50000" in server.shared_read(path)


def test_observed_state_never_trusts_stale_running_flag():
    assert server.worker_state("running", False, False, 1) == "interrupted"
    assert server.worker_state("running", False, True, 120) == "stale"
    assert server.worker_state("running", False, None, 1) == "unknown"
    assert server.worker_state("running", False, False, 1, True) == "starting"
    assert server.worker_state("technical_failure", True, False, 9999) == "complete"


def fixture_monitor(tmp_path: Path, monkeypatch) -> server.Monitor:
    root = tmp_path / "artifacts/preference-recovery-p2-v1"
    job = "minecart-v0_A_seed20263211"
    directory = root / "runs" / job
    directory.mkdir(parents=True)
    (root / "execution_status.json").write_text(
        json.dumps(
            {
                "coordinator_state": "running",
                "coordinator_pid": 1,
                "coordinator_birth": "old",
                "jobs": [{"name": job, "state": "running", "arm": "A", "seed": 20263211}],
            }
        )
    )
    (directory / "heartbeat.json").write_text(
        json.dumps({"pid": 4, "process_birth": "old", "step": 12000, "updates": 1751, "updated_unix": time.time()})
    )
    (root / f"{job}.stderr.log").write_text("Example retained error")
    plans = tmp_path / "configs/experiments"
    plans.mkdir(parents=True)
    (plans / "preference_recovery_p2_v1.json").write_text(
        json.dumps({"seeds": [20263211], "factorial_arms": {"A": {}}, "training_interactions_per_job": 500000})
    )
    (root / f"{job}.stdout.log").write_text("step=12000 updates=1751 sps=200\n")
    monkeypatch.setattr(server.Monitor, "processes", lambda _: [])
    monkeypatch.setattr(server.Monitor, "hardware", lambda _: {"available": False})
    return server.Monitor(tmp_path)


def test_snapshot_is_read_only_and_distinguishes_partial_progress(tmp_path, monkeypatch):
    monitor = fixture_monitor(tmp_path, monkeypatch)
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    state = monitor.snapshot()
    assert state["state"] == "blocked" and state["jobs"][0]["state"] == "interrupted"
    assert state["total_steps"] == 12000 and state["counts"]["complete"] == 0
    assert state["jobs"][0]["task"] == []
    assert before == {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    for name in ("../outside", "minecart-v0_A_seed20263211/../other", "anything"):
        with pytest.raises(ValueError):
            monitor.detail(name, "stderr")


def test_http_api_rejects_mutation_rebinding_cross_origin_and_traversal(tmp_path, monkeypatch):
    monitor = fixture_monitor(tmp_path, monkeypatch)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.handler_for(monitor))
    worker = threading.Thread(target=httpd.serve_forever, daemon=True)
    worker.start()
    url = f"http://127.0.0.1:{httpd.server_port}"
    try:
        with urllib.request.urlopen(url + "/api/state", timeout=3) as response:
            assert json.load(response)["total_steps"] == 12000
            assert response.headers["X-MORL-Monitor"] == "read-only-v1"
        requests = [
            (urllib.request.Request(url + "/api/state", method="POST"), 405),
            (urllib.request.Request(url + "/api/state", headers={"Host": "attacker.example"}), 403),
            (urllib.request.Request(url + "/api/state", headers={"Origin": "https://attacker.example"}), 403),
            (urllib.request.Request(url + "/api/job?name=..%2Fsecret"), 400),
            (urllib.request.Request(url + "/../AGENTS.md"), 404),
        ]
        for request, status in requests:
            with pytest.raises(urllib.error.HTTPError) as caught:
                urllib.request.urlopen(request, timeout=3)
            assert caught.value.code == status
    finally:
        httpd.shutdown()
        httpd.server_close()
        worker.join(3)


@pytest.mark.parametrize("worker_script", ["run_preference_recovery.py", "run_preference_recovery_io.py"])
def test_monitor_never_opens_rotating_json_even_with_active_workers(tmp_path, monkeypatch, worker_script):
    monitor = fixture_monitor(tmp_path, monkeypatch)
    forbidden = {
        "heartbeat.json",
        "progress.json",
        "resume_latest.json",
        "execution_status.json",
        "evaluations.json",
        "losses.json",
    }
    original = server.shared_read
    reads = []

    def guarded(path, *args, **kwargs):
        assert path.name not in forbidden
        reads.append(path.name)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(server, "shared_read", guarded)
    monkeypatch.setattr(
        server.Monitor,
        "processes",
        lambda _: [
            {
                "pid": 9,
                "parent": 1,
                "command": str(tmp_path) + f"/python.exe scripts/{worker_script} --arm A --seed 20263211",
            }
        ],
    )
    data = monitor.snapshot()
    assert data["jobs"][0]["state"] == "running" and data["jobs"][0]["pid"] == 9
    assert data["total_steps"] == 12000
    assert monitor.detail("minecart-v0_A_seed20263211", "stderr")["losses"] == []
    assert "heartbeat.json" not in reads

import io
import json
import time

from rich.console import Console

from monitor import server
from monitor.terminal import Selection, render


def test_native_monitor_switches_to_specialist_without_reading_rotating_state(tmp_path, monkeypatch):
    root = tmp_path / "artifacts/minecart-onpolicy-specialist-v1"
    name = "minecart-v0_S_seed20264111"
    job = root / "runs" / name
    job.mkdir(parents=True)
    (job / "manifest.json").write_text(json.dumps({"provenance": {"git_commit": "source"}}))
    plan_dir = tmp_path / "configs/experiments"
    plan_dir.mkdir(parents=True)
    (plan_dir / "minecart_onpolicy_specialist_v1.json").write_text(json.dumps({"training_interactions": 4000000}))
    (root / f"{name}.stdout.log").write_text("step=25088 updates=1568 sps=500 entropy=1.7000 target=1.7800\n")
    monkeypatch.setattr(
        server.Monitor, "processes", lambda _: [{"pid": 4, "command": f"{tmp_path} run_minecart_onpolicy.py"}]
    )
    monkeypatch.setattr(server.Monitor, "hardware", lambda _: {"available": False})
    original = server.shared_read
    opened = []

    def read(path, *args, **kwargs):
        opened.append(path.name)
        assert path.name not in ("heartbeat.json", "resume_latest.json", "execution_status.json")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(server, "shared_read", read)
    monitor = server.Monitor(tmp_path)
    state = monitor.snapshot()
    assert state["state"] == "running" and state["total_steps"] == 25088
    assert state["study_label"] == "Minecart / PPO specialist"
    detail = monitor.detail(name, "stdout")
    assert "sps=500" in detail["log"]
    output = io.StringIO()
    Console(file=output, width=140, color_system=None).print(render(state, detail, Selection(), 140, 40))
    assert "PPO specialist" in output.getvalue() and "4,000,000" in output.getvalue()
    assert "Entropy 1.7000" in output.getvalue()
    assert "resume_latest.json" not in opened
    (job / "complete.json").write_text(
        json.dumps(
            {
                "training_interactions": 4000000,
                "actor_updates": 250080,
                "gates": {
                    "sampled": {"deliveries": 8, "episodes": 10, "mean_utility": -0.1},
                    "argmax": {"deliveries": 0, "episodes": 10, "mean_utility": -0.2},
                },
            }
        )
    )
    monitor.onpolicy.sampled = time.monotonic() - 10
    final = monitor.snapshot()
    assert final["state"] == "complete"
    assert [t["mode"] for t in final["jobs"][0]["task"]] == ["sampled", "argmax"]

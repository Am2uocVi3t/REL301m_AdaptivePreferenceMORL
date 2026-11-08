import json
from pathlib import Path

import pytest

from scripts.run_lunar_confirmation import read_plan


def test_confirmation_preserves_pilot_candidate_and_rejects_pilot_seed():
    pilot = json.loads(Path("configs/experiments/lunar_onpolicy_specialist_v1.json").read_text())
    candidate = read_plan(20266311)
    for key in [
        "preference",
        "gamma",
        "gae_lambda",
        "width",
        "epochs",
        "minibatches",
        "streams",
        "fragment_steps",
        "actor_lr",
        "critic_lr",
        "adam_eps",
        "clip",
        "popart_rate",
        "popart_std_floor",
        "entropy_end",
        "entropy_initial_multiplier",
        "entropy_damping",
        "entropy_multiplier_lr",
        "max_grad_norm",
        "critic_steps_per_actor",
        "actor_advantage",
        "nominal",
        "training_interactions",
        "checkpoints",
    ]:
        assert candidate[key] == pilot[key]
    with pytest.raises(ValueError, match="outside"):
        read_plan(pilot["seed"])


def test_confirmation_monitor_separates_two_seeds_and_routes_details(tmp_path, monkeypatch):
    from monitor.server import Monitor

    root = tmp_path / "artifacts/lunar-onpolicy-confirmation-v1"
    root.mkdir(parents=True)
    (root / "cohort_manifest.json").write_text("{}")
    plans = tmp_path / "configs/experiments"
    plans.mkdir(parents=True)
    (plans / "lunar_onpolicy_confirmation_v1.json").write_text(json.dumps({"training_interactions": 4000000}))
    for seed in [20266311, 20266312]:
        (root / f"mo-lunar-lander-v3_LG_seed{seed}.stdout.log").write_text("step=25088 updates=784 sps=200\n")
    monkeypatch.setattr(Monitor, "hardware", lambda _: {"available": False})
    monkeypatch.setattr(
        Monitor,
        "processes",
        lambda _: [
            {"pid": 11, "command": f"{tmp_path} run_lunar_confirmation.py --seed 20266311 --device cuda"},
            {"pid": 12, "command": f"{tmp_path} run_lunar_confirmation.py --seed 20266312 --device cuda"},
        ],
    )
    monitor = Monitor(tmp_path)
    state = monitor.snapshot()
    assert state["counts"]["running"] == 2 and state["budget"] == 8000000
    assert [j["pid"] for j in state["jobs"]] == [11, 12]
    assert [j["seed"] for j in state["jobs"]] == [20266311, 20266312]
    assert state["task_label"] == "LANDINGS"
    assert "25088" in monitor.detail(state["jobs"][1]["name"], "stdout")["log"]

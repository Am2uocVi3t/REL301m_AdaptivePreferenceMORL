import json
import math
from pathlib import Path

import numpy as np
import torch

from src.envs.lunar_replay import ReplayLunar
from src.models.lunar_onpolicy import LunarPPO, gae_advantages
from src.models.onpolicy import ActorCritic


def test_vector_gae_bootstrap_and_reset_boundaries():
    rewards = torch.ones(3, 2, 1)
    values = torch.zeros_like(rewards)
    next_values = torch.tensor([[[2.0], [2.0]], [[3.0], [4.0]], [[5.0], [6.0]]])
    terminated = torch.tensor([[False, False], [True, False], [False, False]])
    truncated = torch.tensor([[False, False], [False, True], [False, False]])
    actual = gae_advantages(rewards, values, next_values, terminated, truncated, 0.5, 0.8)
    torch.testing.assert_close(actual.squeeze(-1), torch.tensor([[2.4, 3.2], [1.0, 3.0], [3.5, 4.0]]))


def test_lunar_four_action_ppo_updates_finite_and_frozen_budget():
    plan = json.loads(Path("configs/experiments/lunar_onpolicy_specialist_v1.json").read_text())
    model = ActorCritic(8, 4, 4, width=16)
    learner = LunarPPO(model, plan)
    states = torch.randn(8, 8, 8)
    weights = torch.tensor([0.7, 0.1, 0.1, 0.1]).expand(8, 8, 4)
    with torch.no_grad():
        dist = model.distribution(states, weights)
        actions = dist.sample()
        batch = {
            "states": states,
            "preferences": weights,
            "actions": actions,
            "logp": dist.log_prob(actions),
            "values": model.value(states, weights),
            "next_values": model.value(states + 0.01, weights),
            "rewards": torch.randn(8, 8, 4),
            "terminated": torch.zeros(8, 8, dtype=torch.bool),
            "truncated": torch.zeros(8, 8, dtype=torch.bool),
        }
    loss = learner.update(batch, 64)
    assert abs(loss["entropy_target"] - math.log(4)) < 0.001
    assert loss["entropy"] <= math.log(4) + 1e-5 and all(math.isfinite(v) for v in loss.values())
    assert learner.actor_updates == 32 and learner.critic_updates == 64
    rounds = sum(
        ((end - start) // 8 + 127) // 128
        for start, end in zip([0, 500000, 1000000, 2000000], plan["checkpoints"], strict=True)
    )
    assert rounds == plan["expected_rounds"] == 3909
    assert rounds * 32 == plan["expected_actor_updates"] and rounds * 64 == plan["expected_critic_updates"]


def test_box2d_replay_reconstructs_ongoing_state_and_future():
    stream = ReplayLunar(20265311, 0, {"constructor_kwargs": {"enable_wind": False}})
    try:
        stream.reset()
        for _ in range(30):
            stream.step(0)
        saved = stream.state_dict()
        expected = [stream.step(a)[:4] for a in [2, 0, 1, 3]]
        assert stream.restore(saved, saved["observation"]) == 30
        actual = [stream.step(a)[:4] for a in [2, 0, 1, 3]]
        for a, b in zip(expected, actual, strict=True):
            np.testing.assert_array_equal(a[0], b[0])
            np.testing.assert_array_equal(a[1], b[1])
            assert a[2:] == b[2:]
    finally:
        stream.close()


def test_native_monitor_prefers_lunar_over_finished_minecart(tmp_path, monkeypatch):
    from monitor import server

    root = tmp_path / "artifacts/lunar-onpolicy-specialist-v1"
    name = "mo-lunar-lander-v3_L_seed20265311"
    directory = root / "runs" / name
    directory.mkdir(parents=True)
    (directory / "manifest.json").write_text("{}")
    plans = tmp_path / "configs/experiments"
    plans.mkdir(parents=True)
    (plans / "lunar_onpolicy_specialist_v1.json").write_text(
        json.dumps({"seed": 20265311, "training_interactions": 4000000})
    )
    (root / f"{name}.stdout.log").write_text("step=25600 updates=800 sps=300\n")
    monkeypatch.setattr(
        server.Monitor, "processes", lambda _: [{"pid": 30, "command": f"{tmp_path} run_lunar_onpolicy.py"}]
    )
    monkeypatch.setattr(server.Monitor, "hardware", lambda _: {"available": False})
    monitor = server.Monitor(tmp_path)
    state = monitor.snapshot()
    assert state["study_label"] == "Lunar / PPO landing specialist" and state["task_label"] == "LANDINGS"
    assert state["jobs"][0]["seed"] == 20265311 and state["jobs"][0]["state"] == "running"
    assert "updates=800" in monitor.detail(name, "stdout")["log"]

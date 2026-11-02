from __future__ import annotations

import copy
import json
import os
import threading
import time
from pathlib import Path

import numpy as np
import pytest
import torch

from scripts.run_minecart_onpolicy import environment_state, restore_environment, seed_all
from src.envs.wrapper import make_mo_env
from src.models.onpolicy import PPO, ActorCritic, clipped_policy_loss, scalar_advantage, td1_returns
from src.utils.training_recovery import global_rng_state, restore_global_rng


def test_td1_stops_at_terminal_and_truncation_and_bootstraps_fragment():
    # Stream0 terminates at t1; stream1 truncates at t1. t2 is a new episode.
    rewards = torch.ones(3, 2, 1)
    following = torch.tensor([[[5.0], [5.0]], [[30.0], [40.0]], [[50.0], [60.0]]])
    terminated = torch.tensor([[False, False], [True, False], [False, False]])
    truncated = torch.tensor([[False, False], [False, True], [False, False]])
    result = td1_returns(rewards, following, terminated, truncated, 0.5).squeeze(-1)
    torch.testing.assert_close(result, torch.tensor([[1.5, 11.5], [1.0, 21.0], [26.0, 31.0]]))


def test_ppo_ratio_clip_sign_and_gradient():
    logits = torch.tensor([np.log(1.5), np.log(0.5)], requires_grad=True, dtype=torch.float32)
    loss = clipped_policy_loss(logits, torch.zeros(2), torch.tensor([2.0, -2.0]), 0.2)
    # Positive advantage clamps at1.2; negative advantage clamps at0.8.
    torch.testing.assert_close(loss, torch.tensor(-0.4))
    loss.backward()
    torch.testing.assert_close(logits.grad, torch.zeros(2))
    original = clipped_policy_loss(torch.zeros(2), torch.zeros(2), torch.tensor([2.0, -2.0]), 0.2)
    assert original == 0


def test_popart_preserves_denormalized_values_and_utility():
    torch.manual_seed(1)
    model = ActorCritic(width=16)
    states, weights = torch.randn(12, 7), torch.tensor([[0.45, 0.45, 0.1]]).expand(12, -1)
    before = model.value(states, weights).detach()
    targets = torch.randn(12, 3) * torch.tensor([1.0, 200.0, 0.01]) + 10
    model.update_popart(targets, 0.1, 1e-4)
    torch.testing.assert_close(model.value(states, weights), before, atol=2e-6, rtol=2e-5)
    expected = ((targets - before) * weights).sum(-1)
    torch.testing.assert_close(scalar_advantage(targets, before, weights), expected)


def test_finite_update_changes_actor_critic_and_counts_every_sample():
    plan = json.loads(Path("configs/experiments/minecart_onpolicy_specialist_v1.json").read_text())
    torch.manual_seed(2)
    model = ActorCritic(width=16)
    learner = PPO(model, plan)
    states = torch.randn(8, 8, 7)
    weights = torch.tensor([0.45, 0.45, 0.1]).expand(8, 8, -1)
    with torch.no_grad():
        distribution = model.distribution(states, weights)
        actions = distribution.sample()
        batch = {
            "states": states,
            "preferences": weights,
            "actions": actions,
            "logp": distribution.log_prob(actions),
            "values": model.value(states, weights),
            "next_values": model.value(states + 0.01, weights),
            "rewards": torch.randn(8, 8, 3),
            "terminated": torch.zeros(8, 8, dtype=torch.bool),
            "truncated": torch.zeros(8, 8, dtype=torch.bool),
        }
    old = copy.deepcopy(model.state_dict())
    loss = learner.update(batch, 64)
    assert all(np.isfinite(list(loss.values())))
    assert learner.actor_updates == 32 and learner.critic_updates == 64
    assert not torch.equal(old["actor.head.weight"], model.actor.head.weight)
    assert not torch.equal(old["critic.head.weight"], model.critic.head.weight)
    # Initial near-uniform policy > a late low target: signed MDMM must decrease lambda.
    learner.update(batch, 4000000)
    assert learner.multiplier < 0.01


def test_frozen_milestone_and_update_budget():
    plan = json.loads(Path("configs/experiments/minecart_onpolicy_specialist_v1.json").read_text())
    previous, rounds = 0, 0
    for milestone in plan["checkpoints"]:
        ticks = (milestone - previous) // plan["streams"]
        rounds += (ticks + 63) // 64
        previous = milestone
    assert rounds == plan["expected_rounds"] == 7815
    assert rounds * 4 * 8 == plan["expected_actor_updates"]
    assert rounds * 4 * 8 * 2 == plan["expected_critic_updates"]
    episodes = 4 * 2 * (2 * 10 + 32 * 3)
    assert episodes == plan["evaluation_episodes"] == 928


def test_eight_stream_mining_and_time_limit_state_roundtrip():
    seed_all(8)
    envs = [make_mo_env("minecart-v0", seed=100 + i) for i in range(8)]
    try:
        states = []
        for i, env in enumerate(envs):
            core = env.unwrapped
            core.cart.pos = core.mines[i % len(core.mines)].pos.copy()
            core.cart.speed = 0
            core.cart.departed = True
            env._elapsed_steps = 998
            states.append(environment_state(env))
        rng = global_rng_state()
        expected = [[env.step(0)[:4] for env in envs] for _ in range(2)]
        assert all(row[3] for row in expected[-1])
        assert any(env.unwrapped.cart.content.sum() > 0 for env in envs)
        for env, state in zip(envs, states, strict=True):
            # Save/get expected observation from cart directly after restoring.
            vars(env.unwrapped.cart).update(copy.deepcopy(state["cart"]))
            restore_environment(env, state, env.unwrapped.get_state())
        restore_global_rng(rng)
        actual = [[env.step(0)[:4] for env in envs] for _ in range(2)]
        for want_tick, got_tick in zip(expected, actual, strict=True):
            for want, got in zip(want_tick, got_tick, strict=True):
                np.testing.assert_array_equal(want[0], got[0])
                np.testing.assert_array_equal(want[1], got[1])
                assert want[2:] == got[2:]
    finally:
        for env in envs:
            env.close()


def test_evaluation_isolates_all_training_rng(tmp_path):
    from scripts.run_minecart_onpolicy import evaluate

    seed_all(10)
    model = ActorCritic(width=16)
    plan = json.loads(Path("configs/experiments/minecart_onpolicy_specialist_v1.json").read_text())
    saved = global_rng_state()
    result = evaluate(model, plan, tmp_path, 64, engineering=True)
    observed = (np.random.random(3), torch.rand(3))
    restore_global_rng(saved)
    expected = (np.random.random(3), torch.rand(3))
    np.testing.assert_array_equal(observed[0], expected[0])
    torch.testing.assert_close(observed[1], expected[1], rtol=0, atol=0)
    assert len(result["records"]) == 2
    assert set(result["gates"]) == {"sampled", "argmax"}
    assert not any(g["pass"] for g in result["gates"].values())


def test_bounded_publish_retries_only_windows_sharing_errors(tmp_path, monkeypatch):
    from scripts import run_minecart_onpolicy as runner

    calls = []

    def locked(path, value):
        calls.append(path)
        error = PermissionError("Reader blocks atomic replacement")
        error.winerror = 5
        raise error

    monkeypatch.setattr(runner, "atomic_json", locked)
    monkeypatch.setattr(runner.time, "sleep", lambda _: None)
    with pytest.raises(PermissionError):
        runner.publish(tmp_path / "state.json", {})
    assert len(calls) == 8


@pytest.mark.skipif(os.name != "nt", reason="Windows atomic replacement sharing witness")
def test_atomic_publication_survives_real_short_windows_reader(tmp_path):
    import ctypes
    from ctypes import wintypes

    from scripts.run_minecart_onpolicy import publish

    path = tmp_path / "witness.json"
    publish(path, {"step": 0})
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.c_void_p,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.CreateFileW(str(path), 0x80000000, 1, None, 3, 0, None)
    assert handle != ctypes.c_void_p(-1).value

    def release():
        time.sleep(0.12)
        kernel.CloseHandle(handle)

    thread = threading.Thread(target=release)
    thread.start()
    try:
        publish(path, {"step": 1})
    finally:
        thread.join()
    assert json.loads(path.read_text()) == {"step": 1}

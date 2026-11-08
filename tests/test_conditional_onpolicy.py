from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

import numpy as np
import torch

from scripts.run_minecart_conditional import conditional_gates
from src.core.episode_preferences import EpisodePreferences
from src.curriculum.sampler import AdaptivePreferenceSampler


def pool():
    return AdaptivePreferenceSampler(3, pool_size=32, pool_seed=20261001).pool


def test_frozen_pool_and_candidate_match_specialist_without_warm_start():
    specialist = json.loads(Path("configs/experiments/minecart_onpolicy_specialist_v1.json").read_text())
    plan = json.loads(Path("configs/experiments/minecart_onpolicy_conditional_v1.json").read_text())
    np.testing.assert_array_equal(np.asarray(plan["training_preference_pool"]["values"], dtype=np.float32), pool())
    differences = {key for key in specialist.keys() & plan.keys() if specialist[key] != plan[key]}
    assert differences == {"study_id", "stage", "selection", "method_contract", "engineering_step_ceiling"}
    assert plan["warm_start"] is False and plan["conditional_dispatch"] is False
    assert plan["evaluation_episodes"] == 928 and plan["final_test_steps"] == 0


def test_episode_preferences_stay_fixed_and_stored_weights_never_alias_reset():
    sampler = EpisodePreferences(pool(), streams=8, seed=20264111)
    initial = sampler.values()
    for _ in range(64):
        sampler.record_tick()
        np.testing.assert_array_equal(initial, sampler.values())
    saved_indices = sampler.indices.copy()
    sampler.reset(3)
    np.testing.assert_array_equal(sampler.indices[:3], saved_indices[:3])
    np.testing.assert_array_equal(sampler.indices[4:], saved_indices[4:])
    np.testing.assert_array_equal(initial, pool()[saved_indices])
    assert sampler.draw_counts.sum() == 9 and sampler.interaction_counts.sum() == 512


def test_uniform_rng_is_independent_and_exactly_resumable_with_exposure_counts():
    np.random.seed(12)
    expected = np.random.random(4)
    np.random.seed(12)
    original = EpisodePreferences(pool(), streams=8, seed=20264111)
    for i in range(21):
        original.record_tick()
        original.reset(i % 8)
    np.testing.assert_array_equal(np.random.random(4), expected)
    state = original.state_dict()
    restored = EpisodePreferences(pool(), streams=8, seed=8)
    restored.load_state_dict(state)
    for i in range(100):
        original.reset(i % 8)
        restored.reset(i % 8)
        original.record_tick()
        restored.record_tick()
        np.testing.assert_array_equal(original.values(), restored.values())
    for key in ["indices", "draw_counts", "interaction_counts"]:
        np.testing.assert_array_equal(original.state_dict()[key], restored.state_dict()[key])
    assert original.interaction_counts.sum() == 121 * 8
    # Inputs/state snapshots are copies, not mutable aliases.
    state["indices"].fill(0)
    assert not np.all(original.indices == 0)


def test_conditional_gate_needs_both_profiles_and_preserves_mode_failures():
    plan = json.loads(Path("configs/experiments/minecart_onpolicy_conditional_v1.json").read_text())
    rows = [
        {
            "kind": "task",
            "mode": mode,
            "preference_index": profile,
            "ore_delivered": case < (7 if mode == "argmax" and profile == 1 else 10),
            "utility": 0.1,
        }
        for mode in ["sampled", "argmax"]
        for profile in [0, 1]
        for case in range(10)
    ]
    gates = conditional_gates(rows, plan, engineering=False)
    assert gates["sampled"]["pass"] is True
    assert gates["argmax"]["pass"] is False
    assert gates["argmax"]["profiles"][0]["pass"] is True
    assert gates["argmax"]["profiles"][1]["deliveries"] == 7
    # Deliveries alone cannot pass if utility is worse than idle.
    for row in rows:
        if row["mode"] == "sampled" and row["preference_index"] == 1:
            row["utility"] = -2
    assert conditional_gates(rows, plan, False)["sampled"]["pass"] is False
    assert not any(g["pass"] for g in conditional_gates(rows, plan, True).values())


def test_real_runner_keeps_collection_preferences_through_resets_within_fragment(tmp_path, monkeypatch):
    from scripts import run_minecart_conditional as runner

    original_env, original_update = runner.make_mo_env, runner.PPO.update
    captured = []

    def short_episodes(*args, **kwargs):
        env = original_env(*args, **kwargs)
        step = env.step

        def limited(action):
            observation, reward, terminated, truncated, info = step(action)
            return observation, reward, terminated, truncated or env._elapsed_steps >= 3, info

        env.step = limited
        return env

    def verify_update(learner, batch, step):
        expected = EpisodePreferences(pool(), streams=8, seed=20264111)
        resets = 0
        for tick in range(len(batch["states"])):
            np.testing.assert_array_equal(batch["preferences"][tick].cpu().numpy(), expected.values())
            expected.record_tick()
            for stream in range(8):
                if bool(batch["terminated"][tick, stream] or batch["truncated"][tick, stream]):
                    expected.reset(stream)
                    resets += 1
        assert resets >= 16  # Two reset cycles inside this same64-sample fragment.
        assert batch["preferences"].shape == (8, 8, 3)
        assert torch.isfinite(batch["next_values"]).all()
        captured.append(expected.state_dict())
        return original_update(learner, batch, step)

    monkeypatch.setattr(runner, "ROOT", tmp_path / "conditional-engineering")
    monkeypatch.setattr(runner, "make_mo_env", short_episodes)
    monkeypatch.setattr(runner.PPO, "update", verify_update)
    args = Namespace(
        engineering=True, steps=64, name="reset-test", device="cpu", resume=False, pause_at=None, hold=False
    )
    directory = runner.run(args)
    saved = runner.load_state(directory)
    np.testing.assert_array_equal(saved["preferences"]["indices"], captured[0]["indices"])
    assert int(saved["preferences"]["interaction_counts"].sum()) == 64

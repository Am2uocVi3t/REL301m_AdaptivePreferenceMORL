from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import torch

from scripts import run_minecart_confirmation as runner
from src.evaluation.protocol import generate_preferences, load_protocol
from src.models.onpolicy import ActorCritic
from src.utils.training_recovery import global_rng_state, restore_global_rng


def test_confirmation_freezes_same_candidate_new_preferences_and_exact_budget():
    c = json.loads(Path("configs/experiments/minecart_onpolicy_conditional_v1.json").read_text())
    g = json.loads(runner.PLAN.read_text())
    changed = {key for key in c.keys() & g.keys() if c[key] != g[key]}
    assert changed == {
        "study_id",
        "stage",
        "protocol",
        "protocol_file_sha256",
        "prerequisite",
        "task_seeds",
        "validation_seeds",
        "evaluation_episodes",
        "evaluation_step_ceiling",
        "selection",
        "method_contract",
        "engineering_step_ceiling",
    }
    assert g["seeds"] == [20264311, 20264312, 20264313]
    protocol, weights = load_protocol(g["protocol"], "validation")
    assert "test" not in protocol["preference_splits"]
    np.testing.assert_array_equal(weights, generate_preferences(3, 32, 20264421))
    assert g["task_seeds"] == list(range(20264431, 20264441))
    assert g["anchor_preferences"] == c["training_preference_pool"]["values"][:7]
    assert (2 * 10 + 32 * 3 + 7 * 3) * 2 * 4 == g["evaluation_episodes"] == 1096
    assert g["cohort_training_interactions"] == 3 * g["training_interactions"] == 12000000
    assert g["cohort_evaluation_episodes"] == 3 * 1096 == 3288


def test_seed_is_bound_into_checkpoint_identity():
    # No environment stepping: signatures must differ even under the same plan hash.
    plan = json.loads(runner.PLAN.read_text())
    env = runner.make_mo_env("minecart-v0", seed=10)
    try:
        identities = [runner.binding({**plan, "seed": seed}, "cuda", 4000000, env) for seed in plan["seeds"]]
        assert [d["training_seed"] for d in identities] == plan["seeds"]
        assert identities[0] != identities[1]
    finally:
        env.close()


def test_full_confirmation_evaluation_matrix_and_rng_isolation(tmp_path, monkeypatch):
    # Shorten only this engineering fixture; production horizon remains frozen1000.
    plan = json.loads(runner.PLAN.read_text())
    plan["horizon"] = 1
    runner.seed_all(20264311)
    model = ActorCritic(width=16)
    saved = global_rng_state()
    result = runner.evaluate(model, plan, tmp_path, 64, engineering=False)
    observed = (np.random.random(3), torch.rand(3))
    restore_global_rng(saved)
    np.testing.assert_array_equal(observed[0], np.random.random(3))
    torch.testing.assert_close(observed[1], torch.rand(3), rtol=0, atol=0)
    assert len(result["records"]) == 274
    assert result["evaluation_steps"] == 274
    assert {kind: sum(r["kind"] == kind for r in result["records"]) for kind in ["task", "validation", "anchor"]} == {
        "task": 40,
        "validation": 192,
        "anchor": 42,
    }
    assert all(not g["pass"] for g in result["gates"].values())


def test_unregistered_confirmation_seed_is_rejected_before_output(tmp_path, monkeypatch):
    from argparse import Namespace

    monkeypatch.setattr(runner, "ROOT", tmp_path)
    with pytest.raises(ValueError, match="Seed outside"):
        runner.run(Namespace(seed=20264111))
    assert not list(tmp_path.iterdir())


def test_native_confirmation_monitor_tracks_all_seeds_and_logs(tmp_path, monkeypatch):
    from monitor import server

    root = tmp_path / "artifacts/minecart-onpolicy-confirmation-v1"
    root.mkdir(parents=True)
    (root / "cohort_manifest.json").write_text("{}")
    plans = tmp_path / "configs/experiments"
    plans.mkdir(parents=True)
    (plans / "minecart_onpolicy_confirmation_v1.json").write_text(json.dumps({"training_interactions": 4000000}))
    seeds = [20264311, 20264312, 20264313]
    for seed in seeds:
        name = f"minecart-v0_G_seed{seed}"
        directory = root / "runs" / name
        directory.mkdir(parents=True)
        (directory / "manifest.json").write_text(json.dumps({"provenance": {"git_commit": "source-G"}}))
        (root / f"{name}.stdout.log").write_text("step=25088 updates=1568 sps=250 entropy=1.7 target=1.78\n")
    processes = [
        {"pid": i + 10, "command": f"{tmp_path} run_minecart_confirmation.py --seed {seed}"}
        for i, seed in enumerate(seeds)
    ]
    monkeypatch.setattr(server.Monitor, "processes", lambda _: processes)
    monkeypatch.setattr(server.Monitor, "hardware", lambda _: {"available": False})
    monitor = server.Monitor(tmp_path)
    state = monitor.snapshot()
    assert state["counts"]["running"] == 3 and state["total_steps"] == 3 * 25088
    assert state["budget"] == 12000000 and "3 seeds" in state["study_label"]
    assert [j["pid"] for j in state["jobs"]] == [10, 11, 12]
    assert [j["seed"] for j in state["jobs"]] == seeds
    assert "sps=250" in monitor.detail("minecart-v0_G_seed20264312", "stdout")["log"]
    # A completed seed is not inferred to be running from stale process metadata.
    (root / "runs/minecart-v0_G_seed20264311/complete.json").write_text(json.dumps({"training_interactions": 4000000}))
    monitor.confirmation.sampled = 0
    for child in monitor.confirmation.children:
        child.sampled = 0
    final = monitor.snapshot()
    assert final["counts"]["complete"] == 1 and final["counts"]["running"] == 2

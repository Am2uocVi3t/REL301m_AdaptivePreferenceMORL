"""Audit completed prospective Lunar runs and replay every recorded task trace."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import torch

from scripts.run_lunar_confirmation import PLAN, QUALIFICATION, ROOT, SOURCE, binding, read_plan
from scripts.run_minecart_onpolicy import load_state, publish, sha
from src.envs.wrapper import make_mo_env
from src.evaluation.protocol import load_protocol, resolve_reward_scale


def finite(value):
    if isinstance(value, torch.Tensor):
        assert torch.isfinite(value).all()
    elif isinstance(value, dict):
        for item in value.values():
            finite(item)
    elif isinstance(value, (tuple, list)):
        for item in value:
            finite(item)
    elif isinstance(value, float):
        assert math.isfinite(value)


def main():
    qualification = json.loads(QUALIFICATION.read_text())
    source = {p: sha(p) for p in SOURCE}
    assert source == qualification["source"]
    cohort = json.loads(PLAN.read_text())
    jobs, initial_hashes = [], []
    replay_steps = trace_count = 0
    for seed in cohort["seeds"]:
        plan = read_plan(seed)
        directory = ROOT / "runs" / f"mo-lunar-lander-v3_LG_seed{seed}"
        manifest = json.loads((directory / "manifest.json").read_text())
        complete = json.loads((directory / "complete.json").read_text())
        checkpoint = directory / "resume_step004000000.pt"
        assert sha(checkpoint) == complete["snapshot_sha256"]
        saved = load_state(directory)
        assert saved["step"] == 4000000 and saved["counters"][:2] == (4000000, 3909)
        assert complete["training_interactions"] == 4000000
        assert complete["actor_updates"] == saved["learner"]["actor_updates"] == 125088
        assert complete["critic_updates"] == saved["learner"]["critic_updates"] == 250176
        assert complete["restoration_steps"] == saved["restoration_steps"] == 0
        assert complete["final_test_steps"] == 0 and not complete["engineering"]
        assert saved["trace_hash"] == complete["trace_hash"]
        assert sum(e["length"] for e in saved["histories"][0]) + sum(saved["episode_state"][0]) == 4000000
        finite(saved["learner"])
        finite(saved["histories"][:2])
        assert manifest["provenance"]["git_dirty"] is False
        assert manifest["provenance"]["git_commit"] == "c3a1d2757214ff9cd8477fb65d6da1ee56e58d6a"
        initial_hashes.append(manifest["initial_parameter_sha256"])
        assert saved["initial_parameter_sha256"] == complete["initial_parameter_sha256"] == initial_hashes[-1]
        env = make_mo_env("mo-lunar-lander-v3", dynamics_shift_config=plan["nominal"])
        protocol, validation = load_protocol(plan["protocol"], "validation")
        scale = resolve_reward_scale(protocol)
        evaluations, milestones, files = [], [], {}
        try:
            contract = binding(plan, "cuda", 4000000, env)
            assert saved["binding"] == manifest["binding"] == contract
            assert qualification["runtime_by_seed"][str(seed)] == {
                k: v for k, v in contract.items() if k not in ("source", "total")
            }
            for step, recorded in zip(plan["checkpoints"], saved["histories"][2], strict=True):
                path = directory / f"evaluation_step{step:09}.json"
                assert sha(path) == recorded["sha256"]
                result = json.loads(path.read_text())
                assert result["step"] == step and len(result["records"]) == 232
                expected_cases = {
                    (mode, kind, index, case_seed)
                    for mode in plan["evaluation_modes"]
                    for kind, weights, seeds in [
                        ("task", plan["task_preferences"], plan["task_seeds"]),
                        ("validation", validation, plan["validation_seeds"]),
                    ]
                    for index in range(len(weights))
                    for case_seed in seeds
                }
                assert {
                    (r["mode"], r["kind"], r["preference_index"], r["env_seed"]) for r in result["records"]
                } == expected_cases
                for row in result["records"]:
                    finite(row)
                    weights = (plan["task_preferences"] if row["kind"] == "task" else validation)[
                        row["preference_index"]
                    ]
                    np.testing.assert_array_equal(weights, row["preference"])
                    np.testing.assert_allclose(
                        np.asarray(row["discounted_return"]) * scale, row["scaled_discounted_return"]
                    )
                    np.testing.assert_allclose(np.dot(weights, row["scaled_discounted_return"]), row["utility"])
                    assert sum(row["action_counts"]) == row["steps"]
                    if row["kind"] != "task":
                        continue
                    trace = Path(row["trace"])
                    assert sha(trace) == row["trace_sha256"]
                    with np.load(trace, allow_pickle=False) as data:
                        actions, rewards, states = data["actions"], data["raw_rewards"], data["states"]
                    assert len(actions) == row["steps"]
                    np.testing.assert_allclose(rewards.sum(0), row["raw_return"], rtol=1e-12, atol=1e-12)
                    np.testing.assert_allclose(
                        (rewards * plan["gamma"] ** np.arange(len(actions))[:, None]).sum(0),
                        row["discounted_return"],
                        rtol=1e-12,
                        atol=1e-12,
                    )
                    np.random.seed(row["policy_seed"])
                    observation, _ = env.reset(seed=row["env_seed"])
                    original_score = 0.0
                    for index, action in enumerate(actions):
                        np.testing.assert_array_equal(observation, states[index])
                        observation, reward, terminated, truncated, info = env.step(int(action))
                        np.testing.assert_array_equal(np.asarray(reward, dtype=np.float64), rewards[index])
                        original_score += info["original_reward"]
                        if index < len(actions) - 1:
                            assert not terminated and not truncated
                    body: Any = env.unwrapped
                    inside = bool(body.helipad_x1 <= body.lander.position.x <= body.helipad_x2)
                    native = bool(terminated and rewards[:, 0].sum() > 0)
                    assert inside == row["inside_pad_x"] and native == row["native_plus100"]
                    assert (native and inside) == row["pad_success"]
                    assert terminated == row["terminated"] and truncated == row["truncated"]
                    assert original_score == row["original_score"] and float(body.lander.angle) == row["final_angle"]
                    np.testing.assert_array_equal(list(body.lander.linearVelocity), row["final_velocity"])
                    replay_steps += len(actions)
                    trace_count += 1
                assert result["evaluation_steps"] == sum(r["steps"] for r in result["records"])
                cells = []
                for mode in plan["evaluation_modes"]:
                    for profile in range(2):
                        rows = [
                            r
                            for r in result["records"]
                            if r["kind"] == "task" and r["mode"] == mode and r["preference_index"] == profile
                        ]
                        cells.append(
                            {
                                "mode": mode,
                                "profile": profile,
                                "pad_successes": sum(r["pad_success"] for r in rows),
                                "mean_utility": float(np.mean([r["utility"] for r in rows])),
                            }
                        )
                    primary = next(c for c in cells if c["mode"] == mode and c["profile"] == 0)
                    assert primary["pad_successes"] == result["gates"][mode]["deliveries"]
                    assert result["gates"][mode]["pass"] == (primary["pad_successes"] >= 8)
                milestones.append({"step": step, "task": cells})
                evaluations.append(result)
                files[str(path)] = sha(path)
        finally:
            env.close()
        assert (
            sum(e["evaluation_steps"] for e in evaluations)
            == complete["development_evaluation_steps"]
            == saved["counters"][2]
        )
        assert evaluations[-1]["gates"] == complete["gates"]
        for path in [directory / "manifest.json", directory / "complete.json", checkpoint]:
            files[str(path)] = sha(path)
        jobs.append(
            {"seed": seed, "completion": complete, "files": files, "milestones": milestones, "evaluations": evaluations}
        )
        print(f"Seed{seed}: 928 evaluation rows /160 task traces audited and replayed", flush=True)
    assert len(set(initial_hashes)) == 2 and trace_count == 320
    result = {
        "study_id": cohort["study_id"],
        "audit": "source_numeric_budget_and_all_task_physics_replay_pass",
        "review_independence": "executor_only",
        "source": source,
        "auditor_sha256": sha(__file__),
        "training_interactions": 8000000,
        "actor_updates": 250176,
        "critic_updates": 500352,
        "development_episodes": 1856,
        "development_steps": sum(j["completion"]["development_evaluation_steps"] for j in jobs),
        "task_traces": trace_count,
        "additional_diagnostic_replay_steps": replay_steps,
        "final_test_steps": 0,
        "training_restoration_steps": 0,
        "prospective_training_seeds": 2,
        "pilot_included": False,
        "all_seed_both_mode_primary_gate_pass": all(g["pass"] for j in jobs for g in j["completion"]["gates"].values()),
        "jobs": jobs,
    }
    publish(Path("research/evidence/lunar_onpolicy_confirmation_v1.json"), result)
    print({k: v for k, v in result.items() if k not in ("source", "jobs")})


if __name__ == "__main__":
    main()

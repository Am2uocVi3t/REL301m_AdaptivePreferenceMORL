"""Paired frozen-model policy extraction and replay diagnostics; zero learning."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
import time
from pathlib import Path
from typing import Any

os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import torch
from gymnasium.envs.box2d.lunar_lander import heuristic

from src.core.n_step import n_step_targets
from src.envs.wrapper import make_mo_env
from src.evaluation.protocol import load_protocol, resolve_reward_scale
from src.models.q_network import VectorQNetwork
from src.utils.provenance import collect_provenance
from src.utils.training_recovery import atomic_json, load_boundary, process_lease

PLAN = Path("configs/experiments/policy_extraction_diagnosis_v1.json")
ROOT = Path("artifacts/policy-extraction-diagnosis-v1")


def read(path: Path) -> Any:
    return json.loads(path.read_text())


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def scores(q: torch.Tensor, preference: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    """Use the exact matmul/mean ordering of VectorQNetwork.predict_action."""
    return torch.stack([torch.matmul(head, preference) for head in q]), torch.matmul(q.mean(0), preference)


def vote_action(head_scores: torch.Tensor, mean_scores: torch.Tensor) -> int:
    votes = torch.bincount(head_scores.argmax(-1), minlength=mean_scores.shape[0])
    tied = votes == votes.max()
    return int(mean_scores.masked_fill(~tied, -torch.inf).argmax().item())


def greedy_action(policy: str, head: int, head_scores: torch.Tensor, mean_scores: torch.Tensor) -> int:
    if policy.startswith("head"):
        return int(head_scores[int(policy[4])].argmax().item())
    if policy == "episode_head_eps005":
        return int(head_scores[head].argmax().item())
    if policy == "plurality_vote":
        return vote_action(head_scores, mean_scores)
    return int(mean_scores.argmax().item())


def rollout(
    model: VectorQNetwork,
    spec: dict[str, Any],
    plan: dict[str, Any],
    policy: str,
    preference: list[float],
    seed: int,
    trace_path: Path,
    device: str,
) -> dict[str, Any]:
    env = make_mo_env(spec["env_id"])
    body: Any = env.unwrapped
    np.random.seed(seed)
    random.seed(seed)
    observation, _ = env.reset(seed=seed)
    head = int(np.random.default_rng(np.random.SeedSequence([seed, 30])).integers(3))
    coins = np.random.default_rng(np.random.SeedSequence([seed, 31]))
    actions_rng = np.random.default_rng(np.random.SeedSequence([seed, 32]))
    w = torch.tensor(preference, dtype=torch.float32, device=device)
    actions, rewards, states, exploratory, probe_steps, probe_q = [], [], [np.asarray(observation).copy()], [], [], []
    terminated = truncated = False
    probe_head_actions, probe_mean_actions = [], []
    cargo_peak = 0.0
    counts = np.zeros(model.action_dim, dtype=np.int64)
    started = time.time()
    try:
        with torch.inference_mode():
            for step in range(plan["max_episode_steps"]):
                q = model(torch.as_tensor(observation, device=device).unsqueeze(0), w.unsqueeze(0))[:, 0]
                hs, ms = scores(q, w)
                coin, random_action = coins.random(), int(actions_rng.integers(model.action_dim))
                explore = policy == "uniform_random" or (policy.endswith("eps005") and coin < plan["epsilon"])
                if policy == "gymnasium_heuristic":
                    action = int(heuristic(env, observation))
                elif explore:
                    action = random_action
                else:
                    action = greedy_action(policy, head, hs, ms)
                if step % plan["probe_stride"] == 0:
                    probe_steps.append(step)
                    probe_q.append(q.cpu().numpy())
                    probe_head_actions.append(hs.argmax(-1).cpu().numpy())
                    probe_mean_actions.append(int(ms.argmax().item()))
                observation, reward, terminated, truncated, _ = env.step(action)
                actions.append(action)
                rewards.append(np.asarray(reward).copy())
                states.append(np.asarray(observation).copy())
                exploratory.append(explore)
                counts[action] += 1
                if spec["env_id"] == "minecart-v0":
                    cargo_peak = max(cargo_peak, float(np.asarray(body.cart.content).sum()))
                if terminated or truncated:
                    break
        native = np.asarray(rewards, dtype=np.float64)
        raw = native.sum(0)
        discounted = (native * np.power(plan["gamma"], np.arange(len(actions)))[:, None]).sum(0)
        scaled = discounted * np.asarray(spec["reward_scale"])
        result = {
            "policy": policy,
            "preference": preference,
            "seed": seed,
            "sampled_episode_head": head,
            "steps": len(actions),
            "native_raw_return": raw,
            "native_discounted_return": discounted,
            "scaled_discounted_return": scaled,
            "utility": float(np.dot(preference, scaled)),
            "objective_utility_contributions": scaled * preference,
            "terminated": bool(terminated),
            "truncated": bool(truncated),
            "action_counts": counts,
            "initial_state_sha256": hashlib.sha256(np.asarray(states[0], dtype=np.float32).tobytes()).hexdigest(),
        }
        if not (terminated or truncated):
            raise AssertionError("A diagnostic episode hit its guard without environment end flags")
        if spec["env_id"] == "minecart-v0":
            result.update(ore_delivered=bool(np.any(raw[:2] > 0)), cargo_peak=cargo_peak)
        else:
            result.update(
                native_plus100=bool(raw[0] > 0 and terminated),
                inside_pad_x=bool(body.helipad_x1 <= body.lander.position.x <= body.helipad_x2),
            )
        np.savez_compressed(
            trace_path,
            states=np.asarray(states),
            actions=np.asarray(actions, dtype=np.int8),
            native_rewards=native,
            exploratory=np.asarray(exploratory),
            probe_steps=np.asarray(probe_steps),
            probe_q=np.asarray(probe_q),
            probe_head_actions=np.asarray(probe_head_actions),
            probe_mean_actions=np.asarray(probe_mean_actions),
        )
        result.update(trace=str(trace_path), trace_sha256=sha(trace_path), wall_seconds=time.time() - started)
        return result
    finally:
        env.close()


def replay_audit(spec: dict[str, Any], plan: dict[str, Any], device: str) -> dict[str, Any]:
    directory = Path(spec["directory"])
    if not (directory / "resume_latest.json").exists():
        return {"status": "unavailable_legacy_checkpoint_has_no_replay"}
    saved = load_boundary(directory)
    rb = saved["replay"]
    online = VectorQNetwork(rb["state_dim"], rb["action_dim"], rb["reward_dim"]).to(device)
    target = VectorQNetwork(rb["state_dim"], rb["action_dim"], rb["reward_dim"]).to(device)
    online.load_state_dict(saved["model"])
    target.load_state_dict(saved["target"])
    online.eval()
    target.eval()
    size = rb["size"]
    if spec["env_id"] == "minecart-v0":
        positive = np.any(rb["rewards"][:size, :2] > 0, axis=1)
    else:
        positive = rb["rewards"][:size, 0] > 0
    rng = np.random.default_rng(plan["replay_audit"]["seed"])
    groups = []
    with torch.inference_mode():
        for label, mask in (("positive_task_reward", positive), ("no_positive_task_reward", ~positive)):
            positions = np.flatnonzero(mask)
            sampled = rng.choice(
                positions, size=min(len(positions), plan["replay_audit"]["per_group_sample"]), replace=False
            )
            entry = {
                "group": label,
                "population": len(positions),
                "sample_size": len(sampled),
                "active_mask_population_per_head": rb["bootstrap_masks"][:size][mask].sum(0),
            }
            if len(sampled):
                batch = {
                    key: torch.as_tensor(rb[key][sampled], device=device)
                    for key in (
                        "states",
                        "actions",
                        "rewards",
                        "next_states",
                        "terminated",
                        "bootstrap_masks",
                        "behavior_preferences",
                    )
                }
                w = batch["behavior_preferences"]
                q = online(batch["states"], w)
                prediction = q.gather(
                    2, batch["actions"][None, :, None, None].expand(3, -1, 1, rb["reward_dim"])
                ).squeeze(2)
                targets = n_step_targets(
                    online,
                    target,
                    batch["next_states"],
                    w,
                    batch["rewards"],
                    batch["terminated"],
                    torch.as_tensor(saved["discounts"][sampled], device=device),
                )
                active = batch["bootstrap_masks"].T
                td = (prediction - targets).abs().mean(-1)
                entry.update(
                    mean_masked_absolute_td_per_head=((td * active).sum(1) / active.sum(1).clamp_min(1)).cpu().numpy(),
                    sampled_true_terminal_fraction=float(rb["terminated"][sampled].mean()),
                    behavior_preference_mean=rb["behavior_preferences"][sampled].mean(0),
                )
            groups.append(entry)
    return {
        "status": "same_boundary_model_target_and_replay",
        "step": saved["step"],
        "replay_size": size,
        "n_step_span": spec["n"],
        "note": "Positive n-step reward windows are not independent successes or one-step native rewards",
        "groups": groups,
    }


def run(name: str, device: str, qualify: bool = False) -> None:
    plan = read(PLAN)
    spec = next(s for s in plan["models"] if s["name"] == name)
    directory = ROOT / ("qualification" if qualify else "runs") / name
    directory.mkdir(parents=True, exist_ok=True)
    with process_lease(directory / "worker.lock"):
        if any(p.name != "worker.lock" for p in directory.iterdir()):
            raise ValueError("Refusing to overwrite diagnostic output")
        if sha(Path(spec["checkpoint"])) != spec["checkpoint_sha256"]:
            raise ValueError("Frozen checkpoint hash changed")
        torch.set_num_threads(1)
        torch.use_deterministic_algorithms(True)
        torch.backends.cudnn.benchmark = False
        checkpoint = torch.load(spec["checkpoint"], map_location="cpu", weights_only=True)
        model = VectorQNetwork(**checkpoint["architecture"]).to(device)
        model.load_state_dict(checkpoint["model_state_dict"])
        model.eval().requires_grad_(False)
        protocol, _ = load_protocol(spec["protocol"], "validation")
        spec = dict(spec, reward_scale=resolve_reward_scale(protocol).tolist())
        source = read(Path(plan["source_evidence"]))
        previous = next(row for row in source["records"] if row["job"]["name"] == name)["evaluations"][-1]["task"][
            "records"
        ]
        records = []
        for index, expected in enumerate(previous):
            actual = rollout(
                model,
                spec,
                plan,
                "mean_greedy",
                expected["preference"],
                expected["seed"],
                directory / f"replication_{index:02}.npz",
                device,
            )
            for key in ("steps", "terminated", "truncated", "action_counts"):
                np.testing.assert_array_equal(actual[key], expected[key])
            for key in ("native_raw_return", "native_discounted_return", "scaled_discounted_return"):
                np.testing.assert_allclose(actual[key], expected[key], rtol=1e-6, atol=1e-6)
            actual["block"] = "baseline_replication"
            records.append(actual)
        replay = {"status": "qualification_only"} if qualify else replay_audit(spec, plan, device)
        if not qualify:
            policies = [*plan["policies"]]
            if spec["env_id"] == "mo-lunar-lander-v3":
                policies.append(plan["lunar_positive_control"])
            for pref_index, preference in enumerate(plan["preferences"][spec["env_id"]]):
                for seed in plan["development_environment_seeds"]:
                    initial = None
                    for policy in policies:
                        record = rollout(
                            model,
                            spec,
                            plan,
                            policy,
                            preference,
                            seed,
                            directory / f"pref{pref_index}_seed{seed}_{policy}.npz",
                            device,
                        )
                        if initial is None:
                            initial = record["initial_state_sha256"]
                        if record["initial_state_sha256"] != initial:
                            raise AssertionError("Paired policy initial states differ")
                        record["block"] = "paired_extraction"
                        record["preference_index"] = pref_index
                        records.append(record)
                    atomic_json(
                        directory / "progress.json",
                        {
                            "episodes": len(records),
                            "last_seed": seed,
                            "preference_index": pref_index,
                            "pid": os.getpid(),
                            "updated_unix": time.time(),
                        },
                    )
                    print(name, "episodes", len(records), flush=True)
        if sha(Path(spec["checkpoint"])) != spec["checkpoint_sha256"]:
            raise AssertionError("Diagnostic changed its input checkpoint")
        atomic_json(
            directory / "complete.json",
            {
                "study_id": plan["study_id"],
                "plan_sha256": sha(PLAN),
                "model": spec,
                "provenance": collect_provenance({"name": name, "qualify": qualify}),
                "replication_pass": True,
                "training_interactions": 0,
                "gradient_updates": 0,
                "final_test_steps": 0,
                "diagnostic_steps": sum(r["steps"] for r in records),
                "records": records,
                "replay_audit": replay,
            },
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--job", required=True)
    parser.add_argument("--device", default="cuda", choices=["cuda", "cpu"])
    parser.add_argument("--qualify", action="store_true")
    args = parser.parse_args()
    run(args.job, args.device, args.qualify)

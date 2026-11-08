"""Recovery-amended n-step screen with qualified episode-boundary checkpoints."""

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

from src.core.n_step import NStepAccumulator, Transition, n_step_targets
from src.core.replay_buffer import VectorReplayBuffer
from src.curriculum.sampler import AdaptivePreferenceSampler
from src.envs.wrapper import make_mo_env
from src.evaluation.protocol import load_protocol, protocol_hash, resolve_reward_scale
from src.evaluation.rollout import evaluate_preferences
from src.models.q_network import VectorQNetwork
from src.models.update import masked_bootstrap_loss
from src.utils.provenance import collect_provenance
from src.utils.training_recovery import (
    atomic_json,
    global_rng_state,
    load_boundary,
    process_birth,
    process_lease,
    reconstruct_reset,
    reset_snapshot,
    restore_global_rng,
    save_boundary,
)

PLAN = Path("configs/experiments/credit_assignment_v1.json")
ROOT = Path("artifacts/credit-assignment-recovery-v1")
AMENDMENT = Path("configs/experiments/credit_assignment_recovery_v1.json")


def save_json(path: Path, value: Any) -> None:
    atomic_json(path, value)


def parameter_hash(model: VectorQNetwork) -> str:
    digest = hashlib.sha256()
    for name, value in model.state_dict().items():
        digest.update(name.encode())
        digest.update(value.detach().cpu().numpy().tobytes())
    return digest.hexdigest()


def seed_all(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.set_num_threads(1)


def task_evaluation(
    model: VectorQNetwork, protocol: dict[str, Any], plan: dict[str, Any], device: str
) -> dict[str, Any]:
    """Separate development cases; retain native vectors and explicit task diagnostics."""
    numpy_state, python_state = np.random.get_state(), random.getstate()
    records = []
    scale = resolve_reward_scale(protocol)
    env = make_mo_env(protocol["env_id"])
    body: Any = env.unwrapped
    try:
        with torch.inference_mode():
            for preference in plan["task_preferences"][protocol["env_id"]]:
                w = torch.tensor(preference, dtype=torch.float32, device=device)
                for seed in plan["task_environment_seeds"]:
                    np.random.seed(seed)
                    random.seed(seed)
                    observation, _ = env.reset(seed=seed)
                    raw = np.zeros(model.reward_dim, dtype=np.float64)
                    discounted = raw.copy()
                    actions = np.zeros(model.action_dim, dtype=np.int64)
                    terminated = truncated = False
                    count = 0
                    cargo_peak = 0.0
                    while not (terminated or truncated):
                        action, _ = model.predict_action(torch.as_tensor(observation, device=device), w, None)
                        observation, reward, terminated, truncated, _ = env.step(action)
                        vector = np.asarray(reward)
                        raw += vector
                        discounted += plan["gamma"] ** count * vector
                        actions[action] += 1
                        count += 1
                        if protocol["env_id"] == "minecart-v0":
                            cargo_peak = max(cargo_peak, float(np.asarray(body.cart.content).sum()))
                    record = {
                        "preference": preference,
                        "seed": seed,
                        "steps": count,
                        "native_raw_return": raw,
                        "native_discounted_return": discounted,
                        "scaled_discounted_return": discounted * scale,
                        "terminated": bool(terminated),
                        "truncated": bool(truncated),
                        "action_counts": actions,
                    }
                    if protocol["env_id"] == "minecart-v0":
                        record.update(ore_delivered=bool(np.any(raw[:2] > 0)), cargo_peak=cargo_peak)
                    else:
                        record.update(
                            native_plus100=bool(raw[0] > 0 and terminated),
                            inside_pad_x=bool(body.helipad_x1 <= body.lander.position.x <= body.helipad_x2),
                        )
                    records.append(record)
    finally:
        env.close()
        np.random.set_state(numpy_state)
        random.setstate(python_state)
    return {"records": records, "evaluation_steps": sum(r["steps"] for r in records)}


def run(
    protocol_path: str,
    n: int,
    seed: int,
    device: str,
    smoke: bool = False,
    resume: bool = False,
    smoke_steps: int = 6000,
    pause_after: int | None = None,
    hold_at_boundary: bool = False,
) -> Path:
    plan = json.loads(PLAN.read_text())
    protocol, preferences = load_protocol(protocol_path, "validation")
    output = ROOT / ("smoke" if smoke else "runs") / f"{protocol['env_id']}_n{n}_seed{seed}"
    output.mkdir(parents=True, exist_ok=True)
    if not resume and any(path.name != "worker.lock" for path in output.iterdir()):
        raise ValueError(f"Refusing to overwrite existing job {output}")
    if resume and (output / "complete.json").exists():
        raise ValueError("Completed jobs must not be resumed")
    if n not in plan["arms"] or (not smoke and seed not in plan["seeds"]):
        raise ValueError("Job outside frozen plan")
    amendment = json.loads(AMENDMENT.read_text())
    if amendment["parent_plan_sha256"] != hashlib.sha256(PLAN.read_bytes()).hexdigest():
        raise ValueError("Parent plan changed")
    if not smoke and output.name not in amendment["new_jobs"]:
        raise ValueError("Recovery must preserve the three completed original jobs")
    binding = {
        "schema": 1,
        "plan_sha256": hashlib.sha256(PLAN.read_bytes()).hexdigest(),
        "amendment_sha256": hashlib.sha256(AMENDMENT.read_bytes()).hexdigest(),
        "protocol_sha256": protocol_hash(protocol),
        "n": n,
        "seed": seed,
        "device": device,
        "total": smoke_steps if smoke else plan["training_interactions_per_job"],
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "recovery_helper_sha256": hashlib.sha256(Path("src/utils/training_recovery.py").read_bytes()).hexdigest(),
        "source_files": {
            str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(Path("src").rglob("*.py"))
        },
        "dependencies": collect_provenance({})["dependencies"],
    }
    seed_all(seed)
    env = make_mo_env(protocol["env_id"], seed=seed, reward_scale=resolve_reward_scale(protocol))
    evaluation_env = make_mo_env(protocol["env_id"], reward_scale=resolve_reward_scale(protocol))
    shape = env.observation_space.shape
    action_count = getattr(env.action_space, "n", None)
    if shape is None or len(shape) != 1 or action_count is None:
        raise ValueError("Require vector observations and discrete actions")
    model = VectorQNetwork(int(shape[0]), int(action_count), protocol["reward_dim"]).to(device)
    target = VectorQNetwork(model.state_dim, model.action_dim, model.reward_dim).to(device)
    target.load_state_dict(model.state_dict())
    target.eval()
    optimizer = torch.optim.Adam(model.parameters(), lr=plan["lr"])
    initial_hash = parameter_hash(model)
    if not resume:
        save_json(
            output / "manifest.json",
            {
                "plan_sha256": hashlib.sha256(PLAN.read_bytes()).hexdigest(),
                "plan": plan,
                "protocol": protocol,
                "protocol_sha256": protocol_hash(protocol),
                "n": n,
                "seed": seed,
                "device": device,
                "initial_parameter_sha256": initial_hash,
                "provenance": collect_provenance({"n": n, "seed": seed, "smoke": smoke}),
                "deterministic_algorithms": True,
                "recovery_binding": binding,
            },
        )
    replay = VectorReplayBuffer(
        plan["replay_capacity"], model.state_dim, model.action_dim, model.reward_dim, device=device, seed=seed
    )
    discounts = np.zeros(replay.capacity, dtype=np.float32)
    queue = NStepAccumulator(n, plan["gamma"])
    sampler = AdaptivePreferenceSampler(
        model.reward_dim, pool_size=32, seed=seed, pool_seed=int(protocol["training_preference_pool"]["seed"])
    )
    rng = np.random.default_rng(np.random.SeedSequence([seed, 4]))
    env.action_space.seed(int(np.random.SeedSequence([seed, 5]).generate_state(1)[0]))
    total = smoke_steps if smoke else plan["training_interactions_per_job"]
    checkpoints = [total] if smoke else plan["checkpoints"]
    started = time.time()
    updates = episodes = validation_steps = task_steps = 0
    observation, _ = env.reset(seed=seed)
    preference = sampler.sample_uniform()
    head = int(rng.integers(3))
    episode_raw = np.zeros(model.reward_dim)
    episode_discounted = episode_raw.copy()
    episode_length = 0
    episode_records = []
    validation_records = []
    losses = []
    first_step = 1
    last_saved_step = 0
    reconstruction = None
    if resume:
        saved = load_boundary(output)
        if saved["binding"] != binding:
            raise ValueError("Resume configuration/source/device differs from saved checkpoint")
        reconstruct_reset(env, saved["reconstruction"], saved["observation"])
        model.load_state_dict(saved["model"])
        target.load_state_dict(saved["target"])
        optimizer.load_state_dict(saved["optimizer"])
        replay.__dict__.update(saved["replay"])
        sampler.__dict__.update(saved["sampler"])
        rng.bit_generator.state = saved["exploration_rng"]
        env.action_space.np_random.bit_generator.state = saved["action_rng"]
        restore_global_rng(saved["global_rng"])
        observation, preference, head = saved["observation"], saved["preference"], saved["head"]
        discounts = saved["discounts"]
        updates, episodes, validation_steps, task_steps = saved["counters"]
        episode_records, validation_records, losses = saved["histories"]
        initial_hash = saved["initial_hash"]
        first_step = saved["step"] + 1
        last_saved_step = saved["step"]
        reconstruction = saved["reconstruction"]
        started = time.time() - saved["wall_seconds"]
        save_json(
            output / f"resumed_from_step{saved['step']}.json",
            {"pid": os.getpid(), "step": saved["step"], "binding": binding},
        )
    try:
        for step in range(first_step, total + 1):
            epsilon = max(0.05, 1.0 - 0.95 * (step - 1) / (plan["epsilon"]["fraction"] * total))
            if rng.random() < epsilon:
                action = int(env.action_space.sample())
            else:
                with torch.inference_mode():
                    action, _ = model.predict_action(
                        torch.as_tensor(observation, device=device), torch.as_tensor(preference, device=device), head
                    )
            next_observation, reward, terminated, truncated, _ = env.step(action)
            reward = np.asarray(reward, dtype=np.float32)
            emitted = queue.append(
                Transition(
                    np.asarray(observation).copy(),
                    action,
                    reward.copy(),
                    np.asarray(next_observation).copy(),
                    bool(terminated),
                    bool(truncated),
                    preference.copy(),
                )
            )
            if step == total:
                emitted.extend(queue.flush())
            for item in emitted:
                discounts[replay.ptr] = plan["gamma"] ** item.steps
                replay.add(
                    item.first.state,
                    item.first.action,
                    item.reward,
                    item.last.next_state,
                    item.last.terminated,
                    item.last.truncated,
                    item.first.preference,
                )
            episode_raw += reward / resolve_reward_scale(protocol)
            episode_discounted += plan["gamma"] ** episode_length * reward
            episode_length += 1
            observation = next_observation
            if step >= plan["learning_starts"] and step % plan["train_freq"] == 0:
                batch = replay.sample(plan["batch_size"])
                targets = n_step_targets(
                    model,
                    target,
                    batch.next_states,
                    batch.behavior_preferences,
                    batch.rewards,
                    batch.terminated,
                    torch.as_tensor(discounts[batch.indices], device=device),
                )
                all_q = model(batch.states, batch.behavior_preferences)
                predicted = all_q.gather(
                    2, batch.actions[None, :, None, None].expand(3, -1, 1, model.reward_dim)
                ).squeeze(2)
                loss = masked_bootstrap_loss(predicted, targets, batch.bootstrap_masks)
                if not torch.isfinite(loss):
                    raise FloatingPointError("Non-finite loss")
                optimizer.zero_grad(set_to_none=True)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 10.0, error_if_nonfinite=True)
                optimizer.step()
                updates += 1
                if updates % 1000 == 0:
                    losses.append({"step": step, "loss": float(loss.item())})
            if step % plan["target_sync"] == 0:
                target.load_state_dict(model.state_dict())
            if terminated or truncated or step == total:
                episode_records.append(
                    {
                        "end_step": step,
                        "steps": episode_length,
                        "completed": bool(terminated or truncated),
                        "terminated": bool(terminated),
                        "truncated": bool(truncated),
                        "preference": preference,
                        "native_raw_return": episode_raw,
                        "scaled_discounted_return": episode_discounted,
                    }
                )
                episodes += int(terminated or truncated)
                if step < total:
                    reconstruction = reset_snapshot(env)
                    observation, _ = env.reset()
                    preference = sampler.sample_uniform()
                    head = int(rng.integers(3))
                    episode_raw = np.zeros(model.reward_dim)
                    episode_discounted = episode_raw.copy()
                    episode_length = 0
            if step in checkpoints:
                counters = {
                    "training_interactions": step,
                    "gradient_updates": updates,
                    "validation_evaluation_steps": validation_steps,
                    "task_diagnostic_steps": task_steps,
                    "final_test_steps": 0,
                    "curriculum_evaluation_steps": 0,
                }
                torch.save(
                    {
                        "model_state_dict": model.state_dict(),
                        "target_state_dict": target.state_dict(),
                        "optimizer_state_dict": optimizer.state_dict(),
                        "architecture": {
                            "state_dim": model.state_dim,
                            "action_dim": model.action_dim,
                            "reward_dim": model.reward_dim,
                            "hidden_dims": [256, 256],
                            "num_heads": 3,
                        },
                        "protocol": protocol,
                        "counters": counters,
                        "n": n,
                    },
                    output / f"step{step}.pt",
                )
                validation = evaluate_preferences(
                    evaluation_env,
                    model,
                    preferences[:1] if smoke else preferences,
                    1 if smoke else plan["validation_episodes_per_preference"],
                    device,
                    plan["validation_environment_seed"],
                    plan["gamma"],
                    isolate_global_rng=True,
                )
                task: dict[str, Any] = (
                    {"records": [], "evaluation_steps": 0} if smoke else task_evaluation(model, protocol, plan, device)
                )
                validation_steps += validation["evaluation_steps"]
                task_steps += task["evaluation_steps"]
                validation_records.append(
                    {
                        "step": step,
                        "preferences": preferences[:1] if smoke else preferences,
                        "validation": validation,
                        "task": task,
                        "parameter_sha256": parameter_hash(model),
                    }
                )
                save_json(output / "evaluations.json", validation_records)
            if (
                (terminated or truncated)
                and step < total
                and (step - last_saved_step >= 10000 or (pause_after is not None and step >= pause_after))
            ):
                if queue.pending or episode_length:
                    raise AssertionError("Resume checkpoints require an empty n-step queue and a fresh episode")
                save_boundary(
                    output,
                    step,
                    {
                        "binding": binding,
                        "step": step,
                        "model": model.state_dict(),
                        "target": target.state_dict(),
                        "optimizer": optimizer.state_dict(),
                        "replay": replay.__dict__,
                        "sampler": sampler.__dict__,
                        "discounts": discounts,
                        "exploration_rng": rng.bit_generator.state,
                        "action_rng": env.action_space.np_random.bit_generator.state,
                        "global_rng": global_rng_state(),
                        "reconstruction": reconstruction,
                        "observation": observation,
                        "preference": preference,
                        "head": head,
                        "counters": (updates, episodes, validation_steps, task_steps),
                        "histories": (episode_records, validation_records, losses),
                        "initial_hash": initial_hash,
                        "wall_seconds": time.time() - started,
                    },
                )
                last_saved_step = step
                if pause_after is not None and step >= pause_after:
                    save_json(
                        output / "paused.json",
                        {"step": step, "pid": os.getpid(), "reason": "qualification fault-injection boundary"},
                    )
                    if hold_at_boundary:
                        while True:
                            time.sleep(1)
                    return output
            if step % 1000 == 0 or step == total:
                save_json(
                    output / "heartbeat.json",
                    {
                        "pid": os.getpid(),
                        "process_birth": process_birth(os.getpid()),
                        "step": step,
                        "updates": updates,
                        "updated_unix": time.time(),
                        "resume_step": last_saved_step,
                    },
                )
            if step % 25000 == 0 or step == total:
                save_json(
                    output / "progress.json",
                    {
                        "step": step,
                        "updates": updates,
                        "episodes": episodes,
                        "wall_seconds": time.time() - started,
                        "validation_steps": validation_steps,
                        "task_steps": task_steps,
                    },
                )
                print(
                    f"{output.name} step={step} updates={updates} sps={step / (time.time() - started):.0f}", flush=True
                )
        if updates != (total // 4 - (5000 - 1) // 4):
            raise AssertionError("Unexpected update budget")
        save_json(output / "training_episodes.json", episode_records)
        save_json(output / "losses.json", losses)
        save_json(
            output / "complete.json",
            {
                "training_interactions": total,
                "gradient_updates": updates,
                "episodes": episodes,
                "validation_evaluation_steps": validation_steps,
                "task_diagnostic_steps": task_steps,
                "final_test_steps": 0,
                "curriculum_evaluation_steps": 0,
                "initial_parameter_sha256": initial_hash,
                "final_parameter_sha256": parameter_hash(model),
                "wall_seconds": time.time() - started,
                "replay_size": replay.size,
                "pending_transitions": len(queue.pending),
            },
        )
    finally:
        env.close()
        evaluation_env.close()
    return output


def main() -> None:
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--protocol", required=True)
    parser.add_argument("--n", type=int, choices=[1, 20], required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cuda")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--smoke-steps", type=int, default=6000)
    parser.add_argument("--pause-after", type=int)
    parser.add_argument("--hold-at-boundary", action="store_true")
    parser.add_argument("--qualification-root", type=Path)
    args = parser.parse_args()
    if (
        args.qualification_root is not None
        or args.pause_after is not None
        or args.hold_at_boundary
        or args.smoke_steps != 6000
    ) and not args.smoke:
        raise ValueError("Qualification controls are forbidden for main jobs")
    global ROOT
    if args.qualification_root is not None:
        ROOT = args.qualification_root
    output = (
        ROOT
        / ("smoke" if args.smoke else "runs")
        / f"{json.loads(Path(args.protocol).read_text())['env_id']}_n{args.n}_seed{args.seed}"
    )
    with process_lease(output / "worker.lock"):
        print(
            run(
                args.protocol,
                args.n,
                args.seed,
                args.device,
                args.smoke,
                args.resume,
                args.smoke_steps,
                args.pause_after,
                args.hold_at_boundary,
            ),
            flush=True,
        )


if __name__ == "__main__":
    main()

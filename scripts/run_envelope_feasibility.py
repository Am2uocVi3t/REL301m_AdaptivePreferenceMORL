"""Bounded upstream Envelope training with independent, fully retained validation."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import random
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import torch

from src.envs.wrapper import make_mo_env
from src.evaluation.metrics import compute_expected_utility, compute_hypervolume
from src.evaluation.protocol import load_protocol, protocol_hash, resolve_reward_scale
from src.utils.provenance import collect_provenance, write_json


class HostIndexReplay:
    """Keep NumPy SumTree indices on the host without changing priorities."""

    def __init__(self, buffer: Any) -> None:
        self.buffer = buffer

    def __getattr__(self, name: str) -> Any:
        return getattr(self.buffer, name)

    def update_priorities(self, indices: Any, priorities: Any) -> None:
        if isinstance(indices, torch.Tensor):
            indices = indices.detach().cpu().numpy()
        self.buffer.update_priorities(indices, priorities)


def evaluate(agent: Any, protocol: dict[str, Any], weights: np.ndarray, episodes: int, seed: int) -> dict[str, Any]:
    """Evaluation cannot advance training RNGs, replay, optimizer or environment."""
    numpy_state, python_state = np.random.get_state(), random.getstate()
    agent_rng = copy.deepcopy(agent.np_random.bit_generator.state)
    torch_state = torch.random.get_rng_state()
    cuda_states = torch.cuda.get_rng_state_all() if torch.cuda.is_available() else []
    was_training = agent.q_net.training
    env = make_mo_env(protocol["env_id"], reward_scale=resolve_reward_scale(protocol))
    raw = np.zeros((len(weights), episodes, protocol["reward_dim"]), dtype=np.float64)
    discounted = np.zeros_like(raw)
    lengths = np.zeros((len(weights), episodes), dtype=np.int64)
    terminations = np.zeros_like(lengths, dtype=bool)
    truncations = np.zeros_like(terminations)
    try:
        np.random.seed(seed)
        random.seed(seed)
        agent.q_net.eval()
        with torch.no_grad():
            for i, weight in enumerate(weights):
                for j in range(episodes):
                    obs, _ = env.reset(seed=seed + i * episodes + j)
                    terminated = truncated = False
                    discount = 1.0
                    while not (terminated or truncated):
                        action = agent.eval(obs, weight)
                        obs, reward, terminated, truncated, _ = env.step(action)
                        raw[i, j] += reward
                        discounted[i, j] += discount * np.asarray(reward)
                        discount *= protocol["return_definition"]["gamma"]
                        lengths[i, j] += 1
                    terminations[i, j], truncations[i, j] = terminated, truncated
    finally:
        env.close()
        agent.q_net.train(was_training)
        np.random.set_state(numpy_state)
        random.setstate(python_state)
        agent.np_random.bit_generator.state = agent_rng
        torch.random.set_rng_state(torch_state)
        if cuda_states:
            torch.cuda.set_rng_state_all(cuda_states)
    mean = discounted.mean(axis=1)
    return {
        "split": "validation",
        "preferences": weights,
        "evaluation_seed": seed,
        "raw_return_units": "undiscounted protocol-scaled reward, not native units",
        "raw_episode_returns": raw,
        "episode_returns": discounted,
        "episode_lengths": lengths,
        "terminated": terminations,
        "truncated": truncations,
        "evaluation_steps": int(lengths.sum()),
        "ore_positive_episodes": (raw[:, :, :2] > 0).sum(axis=(0, 1)),
        "hypervolume": compute_hypervolume(mean, np.asarray(protocol["reference_point"])),
        "expected_utility": compute_expected_utility(mean, weights),
    }


def run(
    plan_path: Path, output_root: Path, device: str, smoke_steps: int = 0, selected_seed: int | None = None
) -> None:
    from morl_baselines.common.weights import random_weights
    from morl_baselines.multi_policy.envelope.envelope import Envelope

    plan_bytes = plan_path.read_bytes()
    plan = json.loads(plan_bytes)
    protocol, weights = load_protocol(plan["protocol"], "validation")
    plan_sha = hashlib.sha256(plan_bytes).hexdigest()
    torch.set_num_threads(1)
    total = smoke_steps or int(plan["training_interactions"])
    checkpoints = [total] if smoke_steps else plan["validation_checkpoints"]
    seeds = plan["seeds"][:1] if smoke_steps else plan["seeds"]
    if selected_seed is not None:
        if selected_seed not in seeds:
            raise ValueError("Requested seed is outside the frozen plan")
        seeds = [selected_seed]
    status_path = output_root / (
        f"execution_status_seed{selected_seed}.json" if selected_seed else "execution_status.json"
    )
    output_root.mkdir(parents=True, exist_ok=True)
    status: dict[str, Any] = {
        "study_id": plan["study_id"],
        "plan_sha256": plan_sha,
        "smoke": bool(smoke_steps),
        "jobs": [],
    }
    for seed in seeds:
        directory = output_root / f"seed{seed}"
        manifest_path = directory / "run_manifest.json"
        if manifest_path.exists():
            prior = json.loads(manifest_path.read_text())
            if prior["plan_sha256"] != plan_sha or prior["smoke"] != bool(smoke_steps):
                raise ValueError("Existing output belongs to a different plan or execution mode")
            if prior["status"] == "complete":
                status["jobs"].append(prior)
                continue
            raise RuntimeError(f"Partial job preserved at {directory}; use a new output directory after diagnosing it")
        directory.mkdir(parents=True, exist_ok=True)
        env = make_mo_env(protocol["env_id"], seed=seed, reward_scale=resolve_reward_scale(protocol))
        agent = Envelope(
            env=env, seed=seed, device=device, log=False, gamma=protocol["return_definition"]["gamma"], **plan["agent"]
        )
        if device == "cuda":
            agent.replay_buffer = HostIndexReplay(agent.replay_buffer)
        manifest: dict[str, Any] = {
            "status": "running",
            "smoke": bool(smoke_steps),
            "seed": seed,
            "plan_sha256": plan_sha,
            "plan": plan,
            "protocol": protocol,
            "protocol_sha256": protocol_hash(protocol),
            "provenance": collect_provenance({"device": device}),
            "training_interactions": 0,
            "gradient_updates": 0,
            "validation_steps": 0,
            "curriculum_steps": 0,
            "final_test_steps": 0,
            "validation_artifacts": [],
        }
        write_json(manifest_path, manifest)
        started = time.perf_counter()
        obs, _ = env.reset(seed=seed)
        weight = random_weights(agent.reward_dim, 1, dist="gaussian", rng=agent.np_random)
        try:
            for step in range(1, total + 1):
                if agent.global_step < agent.learning_starts:
                    action = env.action_space.sample()
                else:
                    action = agent.act(
                        torch.as_tensor(obs, dtype=torch.float32, device=device),
                        torch.as_tensor(weight, dtype=torch.float32, device=device),
                    )
                next_obs, reward, terminated, truncated, _ = env.step(action)
                agent.global_step += 1
                agent.replay_buffer.add(obs, action, reward, next_obs, terminated)
                if step >= agent.learning_starts:
                    agent.update()
                    manifest["gradient_updates"] += agent.gradient_updates
                if terminated or truncated:
                    obs, _ = env.reset()
                    agent.num_episodes += 1
                    weight = random_weights(agent.reward_dim, 1, dist="gaussian", rng=agent.np_random)
                else:
                    obs = next_obs
                manifest["training_interactions"] = step
                if step % 1000 == 0:
                    manifest["elapsed_seconds"] = time.perf_counter() - started
                    write_json(manifest_path, manifest)
                    print(
                        f"seed={seed} step={step}/{total} updates={manifest['gradient_updates']} "
                        f"elapsed={manifest['elapsed_seconds']:.1f}s",
                        flush=True,
                    )
                if step in checkpoints:
                    agent.save(save_replay_buffer=False, save_dir=str(directory), filename=f"step{step}")
                    model_path = directory / f"step{step}.tar"
                    result = evaluate(
                        agent,
                        protocol,
                        weights[:2] if smoke_steps else weights,
                        1 if smoke_steps else plan["episodes_per_preference"],
                        plan["evaluation_seed"],
                    )
                    result.update(
                        {
                            "training_interactions": step,
                            "gradient_updates": manifest["gradient_updates"],
                            "checkpoint_sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
                        }
                    )
                    artifact = directory / f"validation_step{step}.json"
                    write_json(artifact, result)
                    manifest["validation_steps"] += result["evaluation_steps"]
                    manifest["validation_artifacts"].append(
                        {"path": str(artifact), "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest()}
                    )
                    write_json(manifest_path, manifest)
            manifest["status"] = "complete"
        except BaseException as error:
            manifest["status"] = "interrupted"
            manifest["error"] = repr(error)
            raise
        finally:
            env.close()
            manifest["elapsed_seconds"] = time.perf_counter() - started
            write_json(manifest_path, manifest)
            status["jobs"].append(manifest)
            write_json(status_path, status)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=Path("configs/experiments/envelope_feasibility_v1.json"))
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    parser.add_argument("--smoke-steps", type=int, default=0)
    parser.add_argument("--seed", type=int, help="Execute one declared seed; other seeds are not substituted")
    arguments = parser.parse_args()
    if arguments.smoke_steps and arguments.smoke_steps < 100:
        parser.error("Smoke must include at least the first real update (100 steps)")
    os.environ.setdefault("WANDB_MODE", "disabled")
    run(arguments.plan, arguments.output_dir, arguments.device, arguments.smoke_steps, arguments.seed)

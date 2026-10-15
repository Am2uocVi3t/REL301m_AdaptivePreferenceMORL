#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import os
import sys
from pathlib import Path
from typing import Any

import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.envs.wrapper import make_mo_env
from src.evaluation.metrics import (
    compute_expected_utility,
    compute_hypervolume,
    compute_igd,
    compute_per_objective_controllability,
    compute_scalarized_regret,
    compute_sparsity,
    pareto_prune,
)
from src.evaluation.protocol import (
    load_protocol,
    protocol_hash,
    resolve_reference_point,
    resolve_reward_scale,
)
from src.evaluation.rollout import evaluate_preferences
from src.models.q_network import VectorQNetwork
from src.utils.config import load_config
from src.utils.provenance import collect_provenance, write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate a checkpoint on a fixed MORL protocol")
    parser.add_argument("--model-path", required=True, help="Training checkpoint (.pt)")
    parser.add_argument("--protocol", required=True, help="Versioned protocol JSON")
    parser.add_argument("--split", choices=("validation", "test"), default="test")
    parser.add_argument("--episodes-per-preference", type=int, default=30)
    parser.add_argument("--seed", type=int, default=31000)
    parser.add_argument("--shift-file", default="configs/shifts/dynamics_shifts.yaml")
    parser.add_argument("--shift", default="nominal")
    parser.add_argument(
        "--reference-front",
        help="Optional .npy reference front frozen before final testing",
    )
    parser.add_argument("--output", default="results/evaluation.json")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    return parser.parse_args()


def load_shift(path: str, env_id: str, shift_name: str) -> dict[str, Any]:
    shifts = load_config(path)
    env_shifts = shifts.get(env_id, {})
    if shift_name not in env_shifts or shift_name.startswith("_"):
        available = sorted(name for name in env_shifts if not name.startswith("_"))
        raise ValueError(f"Unknown verified shift {shift_name!r} for {env_id}; available: {available}")
    return dict(env_shifts[shift_name])


def load_network(
    checkpoint: dict[str, Any],
    state_dim: int,
    action_dim: int,
    reward_dim: int,
    device: str,
) -> VectorQNetwork:
    architecture = checkpoint.get("architecture", {})
    network = VectorQNetwork(
        state_dim=state_dim,
        action_dim=action_dim,
        reward_dim=reward_dim,
        hidden_dims=architecture.get("hidden_dims", (256, 256)),
        num_heads=int(architecture.get("num_heads", 3)),
    ).to(device)
    network.load_state_dict(checkpoint["model_state_dict"])
    network.eval()
    return network


def checkpoint_hash(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as checkpoint_file:
        for block in iter(lambda: checkpoint_file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    args = parse_args()
    protocol, preferences = load_protocol(args.protocol, args.split)
    env_id = str(protocol["env_id"])
    reward_dim = int(protocol["reward_dim"])
    return_definition = protocol.get("return_definition", {})
    if return_definition.get("type") != "discounted":
        raise ValueError("Protocol must explicitly define discounted returns")
    discount_factor = float(return_definition["gamma"])
    reward_scale = resolve_reward_scale(protocol)
    shift_config = load_shift(args.shift_file, env_id, args.shift)

    checkpoint = torch.load(args.model_path, map_location=args.device, weights_only=True)
    checkpoint_gamma = float(checkpoint.get("args", {}).get("gamma", discount_factor))
    if not np.isclose(checkpoint_gamma, discount_factor):
        raise ValueError("Checkpoint gamma does not match the evaluation protocol")
    env = make_mo_env(
        env_id,
        seed=args.seed,
        reward_scale=reward_scale,
        dynamics_shift_config=shift_config,
    )
    observation_shape = env.observation_space.shape
    if observation_shape is None or len(observation_shape) != 1:
        raise ValueError("Only flat vector observation spaces are supported")
    action_count = getattr(env.action_space, "n", None)
    if action_count is None:
        raise ValueError("PCQN currently requires a discrete action space")
    state_dim = int(observation_shape[0])
    action_dim = int(action_count)
    network = load_network(checkpoint, state_dim, action_dim, reward_dim, args.device)

    rollout = evaluate_preferences(
        env,
        network,
        preferences,
        episodes_per_preference=args.episodes_per_preference,
        device=args.device,
        seed=args.seed,
        discount_factor=discount_factor,
    )
    frontier = pareto_prune(rollout["mean_returns"])
    metrics: dict[str, Any] = {
        "expected_utility": compute_expected_utility(rollout["mean_returns"], preferences),
        "frontier_size": len(frontier),
        "sparsity": compute_sparsity(frontier),
        "evaluation_steps": rollout["evaluation_steps"],
        "hypervolume": None,
    }
    metrics["controllability"] = compute_per_objective_controllability(rollout["mean_returns"], preferences)

    reference_point = resolve_reference_point(protocol)
    if reference_point is not None:
        metrics["hypervolume"] = compute_hypervolume(frontier, reference_point)

    reference_front = None
    if args.reference_front:
        reference_front = np.load(args.reference_front)
        metrics.update(compute_scalarized_regret(rollout["mean_returns"], reference_front, preferences))
        metrics["igd"] = compute_igd(frontier, reference_front)

    run_config = vars(args) | {
        "env_id": env_id,
        "protocol_sha256": protocol_hash(protocol),
        "checkpoint_sha256": checkpoint_hash(args.model_path),
        "reward_scale": reward_scale,
        "reference_point": reference_point,
    }
    output = {
        "schema_version": 1,
        "provenance": collect_provenance(run_config),
        "protocol": protocol,
        "split": args.split,
        "shift": args.shift,
        "preferences": preferences,
        "episode_returns": rollout["episode_returns"],
        "raw_episode_returns": rollout["raw_episode_returns"],
        "episode_lengths": rollout["episode_lengths"],
        "mean_returns": rollout["mean_returns"],
        "raw_mean_returns": rollout["raw_mean_returns"],
        "pareto_front": frontier,
        "reference_front": reference_front,
        "metrics": metrics,
    }
    write_json(args.output, output)
    env.close()

    print(f"Wrote {args.split} evaluation to {Path(args.output).resolve()}")
    for name, value in metrics.items():
        print(f"{name}: {value}")


if __name__ == "__main__":
    main()

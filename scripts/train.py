#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.pareto_archive import ParetoArchive
from src.core.replay_buffer import ReplayBatch, VectorReplayBuffer
from src.curriculum.gap import compute_conditioning_gap
from src.curriculum.sampler import AdaptivePreferenceSampler
from src.curriculum.uncertainty import compute_bootstrap_uncertainty
from src.envs.wrapper import make_mo_env
from src.evaluation.metrics import (
    compute_expected_utility,
    compute_hypervolume,
    pareto_prune,
)
from src.evaluation.protocol import (
    load_protocol,
    protocol_hash,
    resolve_reference_point,
    resolve_reward_scale,
    resolve_training_pool_size,
)
from src.evaluation.rollout import evaluate_preferences
from src.models.q_network import VectorQNetwork
from src.models.update import compute_double_dqn_targets, masked_bootstrap_loss
from src.utils.logger import ExperimentLogger
from src.utils.provenance import collect_provenance, write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a preference-conditioned vector DQN")
    parser.add_argument("--env", default="mo-lunar-lander-v3")
    parser.add_argument("--protocol", default="configs/protocols/course_mo_lunar_lander_v3.json")
    parser.add_argument(
        "--algo",
        choices=("adaptive-pcqn", "uniform-pcqn", "random-curriculum-pcqn"),
        default="adaptive-pcqn",
    )
    parser.add_argument(
        "--allocation-target",
        choices=("rollout_only", "update_only", "rollout_and_update"),
        default="rollout_and_update",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--total-timesteps", type=int, default=500_000)
    parser.add_argument("--learning-starts", type=int, default=5_000)
    parser.add_argument("--train-freq", type=int, default=4)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--buffer-capacity", type=int, default=200_000)
    parser.add_argument("--bootstrap-probability", type=float, default=0.8)
    parser.add_argument("--num-heads", type=int, default=3)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--gamma", type=float, default=0.99)
    parser.add_argument("--target-update-freq", type=int, default=1_000)
    parser.add_argument("--curriculum-update-freq", type=int, default=15_000)
    parser.add_argument("--curriculum-eval-episodes", type=int, default=1)
    parser.add_argument("--pool-size", type=int, default=None)
    parser.add_argument("--gap-weight", type=float, default=0.25)
    parser.add_argument("--uncertainty-weight", type=float, default=0.25)
    parser.add_argument("--coverage-weight", type=float, default=0.25)
    parser.add_argument("--progress-weight", type=float, default=0.25)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--uniform-floor", type=float, default=0.2)
    parser.add_argument("--locality-bandwidth", type=float, default=0.2)
    parser.add_argument("--eval-freq", type=int, default=25_000)
    parser.add_argument("--eval-episodes", type=int, default=3)
    parser.add_argument("--eval-seed", type=int, default=20_000)
    parser.add_argument("--save-freq", type=int, default=50_000)
    parser.add_argument("--eps-start", type=float, default=1.0)
    parser.add_argument("--eps-end", type=float, default=0.05)
    parser.add_argument("--eps-fraction", type=float, default=0.3)
    parser.add_argument("--wandb-project", default=None)
    parser.add_argument("--output-dir", default="artifacts")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    return parser.parse_args()


def linear_epsilon(
    step: int,
    total_steps: int,
    start: float,
    end: float,
    fraction: float,
) -> float:
    decay_steps = max(1, int(total_steps * fraction))
    progress = min(1.0, step / decay_steps)
    return start + progress * (end - start)


def choose_rollout_preference(
    args: argparse.Namespace,
    sampler: AdaptivePreferenceSampler,
    rng: np.random.Generator,
    reward_dim: int,
) -> np.ndarray:
    uses_curriculum = args.algo != "uniform-pcqn" and args.allocation_target in {
        "rollout_only",
        "rollout_and_update",
    }
    if uses_curriculum:
        return sampler.sample()
    return rng.dirichlet(np.ones(reward_dim)).astype(np.float32)


def choose_update_preferences(
    args: argparse.Namespace,
    batch: ReplayBatch,
    sampler: AdaptivePreferenceSampler,
) -> torch.Tensor:
    uses_curriculum = args.algo != "uniform-pcqn" and args.allocation_target in {
        "update_only",
        "rollout_and_update",
    }
    if not uses_curriculum:
        return batch.behavior_preferences
    sampled = sampler.sample_batch(len(batch.states))
    return torch.as_tensor(sampled, dtype=torch.float32, device=batch.states.device)


def update_network(
    q_network: VectorQNetwork,
    target_network: VectorQNetwork,
    optimizer: torch.optim.Optimizer,
    batch: ReplayBatch,
    preferences: torch.Tensor,
    gamma: float,
) -> float:
    targets = compute_double_dqn_targets(
        q_network,
        target_network,
        batch.next_states,
        preferences,
        batch.rewards,
        batch.terminated,
        gamma,
    )
    all_q = q_network(batch.states, preferences)
    action_indices = batch.actions[None, :, None, None].expand(
        q_network.num_heads,
        -1,
        1,
        q_network.reward_dim,
    )
    predicted = all_q.gather(dim=2, index=action_indices).squeeze(2)
    loss = masked_bootstrap_loss(predicted, targets, batch.bootstrap_masks)

    optimizer.zero_grad()
    loss.backward()
    torch.nn.utils.clip_grad_norm_(q_network.parameters(), max_norm=10.0)
    optimizer.step()
    return float(loss.item())


def update_curriculum(
    args: argparse.Namespace,
    sampler: AdaptivePreferenceSampler,
    q_network: VectorQNetwork,
    replay_buffer: VectorReplayBuffer,
    archive: ParetoArchive,
    evaluation_env: Any,
    previous_utilities: np.ndarray,
    rng: np.random.Generator,
) -> tuple[dict[str, float], np.ndarray, int]:
    rollout = evaluate_preferences(
        evaluation_env,
        q_network,
        sampler.pool,
        episodes_per_preference=args.curriculum_eval_episodes,
        device=args.device,
        seed=args.eval_seed + 1_000_000,
        discount_factor=args.gamma,
    )
    current_returns = rollout["mean_returns"]
    current_utilities = np.sum(current_returns * sampler.pool, axis=1)
    progress = np.where(
        np.isfinite(previous_utilities),
        np.abs(current_utilities - previous_utilities),
        0.0,
    ).astype(np.float32)
    gaps = np.asarray(
        [
            compute_conditioning_gap(weight, archive, value)
            for weight, value in zip(sampler.pool, current_returns, strict=True)
        ],
        dtype=np.float32,
    )

    states = replay_buffer.sample_states(min(128, len(replay_buffer)))
    uncertainty = np.asarray(
        [compute_bootstrap_uncertainty(q_network, states, weight, args.device) for weight in sampler.pool],
        dtype=np.float32,
    )
    previous_gap_scores = sampler.gap_scores.copy()
    previous_uncertainty_scores = sampler.uncertainty_scores.copy()
    random_scores = rng.random(sampler.pool_size) if args.algo == "random-curriculum-pcqn" else None
    if args.algo != "uniform-pcqn":
        sampler.update_distribution(gaps, uncertainty, progress, random_scores=random_scores)

    metrics = {
        "curriculum/mean_gap": float(gaps.mean()),
        "curriculum/mean_uncertainty": float(uncertainty.mean()),
        "curriculum/mean_learning_progress": float(progress.mean()),
        "curriculum/entropy": float(-np.sum(sampler.probabilities * np.log(sampler.probabilities + 1e-12))),
        "curriculum/evaluation_steps": float(rollout["evaluation_steps"]),
        "curriculum/gap_future_progress_correlation": safe_correlation(previous_gap_scores, progress),
        "curriculum/uncertainty_future_progress_correlation": safe_correlation(previous_uncertainty_scores, progress),
    }
    return metrics, current_utilities, int(rollout["evaluation_steps"])


def safe_correlation(first: np.ndarray, second: np.ndarray) -> float:
    if np.std(first) < 1e-12 or np.std(second) < 1e-12:
        return 0.0
    return float(np.corrcoef(first, second)[0, 1])


def validation_metrics(
    args: argparse.Namespace,
    env: Any,
    network: VectorQNetwork,
    preferences: np.ndarray,
    reference_point: np.ndarray | None,
) -> tuple[dict[str, float | int | None], int]:
    rollout = evaluate_preferences(
        env,
        network,
        preferences,
        episodes_per_preference=args.eval_episodes,
        device=args.device,
        seed=args.eval_seed,
        discount_factor=args.gamma,
    )
    frontier = pareto_prune(rollout["mean_returns"])
    metrics: dict[str, float | int | None] = {
        "eval/expected_utility": compute_expected_utility(rollout["mean_returns"], preferences),
        "eval/frontier_size": len(frontier),
        "eval/hypervolume": None,
    }
    if reference_point is not None:
        metrics["eval/hypervolume"] = compute_hypervolume(frontier, reference_point)
    return metrics, int(rollout["evaluation_steps"])


def save_checkpoint(
    path: Path,
    step: int,
    network: VectorQNetwork,
    optimizer: torch.optim.Optimizer,
    archive: ParetoArchive,
    args: argparse.Namespace,
    protocol: dict[str, Any],
    counters: dict[str, int],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "schema_version": 2,
            "step": step,
            "model_state_dict": network.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "archive_points": torch.as_tensor(archive.get_points()),
            "args": vars(args),
            "architecture": {
                "state_dim": network.state_dim,
                "action_dim": network.action_dim,
                "reward_dim": network.reward_dim,
                "hidden_dims": [256, 256],
                "num_heads": network.num_heads,
            },
            "protocol": protocol,
            "protocol_sha256": protocol_hash(protocol),
            "counters": counters,
            "provenance": collect_provenance(vars(args)),
        },
        path,
    )


def main() -> None:
    args = parse_args()
    protocol, validation_preferences = load_protocol(args.protocol, "validation")
    if protocol["env_id"] != args.env:
        raise ValueError(f"Protocol environment {protocol['env_id']} does not match --env {args.env}")
    return_definition = protocol.get("return_definition", {})
    if return_definition.get("type") != "discounted":
        raise ValueError("Protocol must explicitly define discounted returns")
    if not np.isclose(float(return_definition.get("gamma")), args.gamma):
        raise ValueError("Training gamma must match protocol return_definition.gamma")
    pool_spec = protocol.get("training_preference_pool", {})
    args.pool_size = resolve_training_pool_size(protocol, args.pool_size)
    preference_pool_seed = int(pool_spec.get("seed", 20261001))

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    rng = np.random.default_rng(args.seed)
    output_dir = Path(args.output_dir) / f"{args.algo}_{args.env}_seed{args.seed}"
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(
        output_dir / "run_manifest.json",
        collect_provenance(vars(args) | {"protocol": protocol}),
    )

    reward_scale = resolve_reward_scale(protocol)
    train_env = make_mo_env(args.env, seed=args.seed, reward_scale=reward_scale)
    validation_env = make_mo_env(args.env, seed=args.eval_seed, reward_scale=reward_scale)
    curriculum_env = make_mo_env(args.env, seed=args.eval_seed + 1, reward_scale=reward_scale)

    observation_shape = train_env.observation_space.shape
    if observation_shape is None or len(observation_shape) != 1:
        raise ValueError("Only flat vector observation spaces are supported")
    action_count = getattr(train_env.action_space, "n", None)
    if action_count is None:
        raise ValueError("PCQN currently requires a discrete action space")
    state_dim = int(observation_shape[0])
    action_dim = int(action_count)
    reward_dim = int(protocol["reward_dim"])
    reward_space = getattr(train_env.unwrapped, "reward_space", None)
    if reward_space is None or reward_space.shape is None:
        raise ValueError("Environment must expose a vector reward_space")
    actual_reward_dim = int(reward_space.shape[0])
    if actual_reward_dim != reward_dim:
        raise ValueError(f"Protocol reward_dim={reward_dim}, environment reward_dim={actual_reward_dim}")

    q_network = VectorQNetwork(state_dim, action_dim, reward_dim, num_heads=args.num_heads).to(args.device)
    target_network = VectorQNetwork(state_dim, action_dim, reward_dim, num_heads=args.num_heads).to(args.device)
    target_network.load_state_dict(q_network.state_dict())
    target_network.eval()
    optimizer = torch.optim.Adam(q_network.parameters(), lr=args.lr)

    replay_buffer = VectorReplayBuffer(
        args.buffer_capacity,
        state_dim,
        action_dim,
        reward_dim,
        num_heads=args.num_heads,
        bootstrap_probability=args.bootstrap_probability,
        device=args.device,
        seed=args.seed,
    )
    archive = ParetoArchive(reward_dim)
    sampler = AdaptivePreferenceSampler(
        reward_dim,
        pool_size=args.pool_size,
        gap_weight=args.gap_weight,
        uncertainty_weight=args.uncertainty_weight,
        coverage_weight=args.coverage_weight,
        progress_weight=args.progress_weight,
        temperature=args.temperature,
        uniform_floor=args.uniform_floor,
        locality_bandwidth=args.locality_bandwidth,
        seed=args.seed,
        pool_seed=preference_pool_seed,
    )
    logger = ExperimentLogger(
        project_name=args.wandb_project or "REL301m-MORL",
        experiment_name=output_dir.name,
        config=vars(args),
        use_wandb=args.wandb_project is not None,
        use_tensorboard=True,
        log_dir=str(output_dir / "logs"),
    )

    step = episodes = gradient_updates = curriculum_evaluation_steps = validation_evaluation_steps = 0
    previous_utilities = np.full(args.pool_size, np.nan, dtype=np.float32)
    reference_point = resolve_reference_point(protocol)
    started_at = time.time()

    while step < args.total_timesteps:
        behavior_preference = choose_rollout_preference(args, sampler, rng, reward_dim)
        preference_tensor = torch.as_tensor(behavior_preference, device=args.device).unsqueeze(0)
        behavior_head = int(rng.integers(args.num_heads))
        observation, _ = train_env.reset()
        episode_return = np.zeros(reward_dim, dtype=np.float32)
        raw_episode_return = np.zeros(reward_dim, dtype=np.float32)
        episode_length = 0
        episode_discount = 1.0
        terminated = truncated = False

        while not (terminated or truncated) and step < args.total_timesteps:
            epsilon = linear_epsilon(
                step,
                args.total_timesteps,
                args.eps_start,
                args.eps_end,
                args.eps_fraction,
            )
            if rng.random() < epsilon:
                action = train_env.action_space.sample()
            else:
                state_tensor = torch.as_tensor(observation, dtype=torch.float32, device=args.device).unsqueeze(0)
                with torch.no_grad():
                    action, _ = q_network.predict_action(state_tensor, preference_tensor, behavior_head)

            next_observation, reward, terminated, truncated, _ = train_env.step(action)
            reward_vector = np.asarray(reward, dtype=np.float32)
            replay_buffer.add(
                observation,
                action,
                reward_vector,
                next_observation,
                terminated,
                truncated,
                behavior_preference,
            )
            observation = next_observation
            raw_episode_return += reward_vector
            episode_return += episode_discount * reward_vector
            episode_discount *= args.gamma
            episode_length += 1
            step += 1

            if step >= args.learning_starts and step % args.train_freq == 0:
                batch = replay_buffer.sample(args.batch_size)
                update_preferences = choose_update_preferences(args, batch, sampler)
                loss = update_network(
                    q_network,
                    target_network,
                    optimizer,
                    batch,
                    update_preferences,
                    args.gamma,
                )
                gradient_updates += 1
                if gradient_updates % 100 == 0:
                    logger.log({"train/loss": loss, "train/epsilon": epsilon}, step)

            if step % args.target_update_freq == 0:
                q_network.update_target(target_network)

            if step >= args.learning_starts and step % args.curriculum_update_freq == 0:
                curriculum_metrics, previous_utilities, used_steps = update_curriculum(
                    args,
                    sampler,
                    q_network,
                    replay_buffer,
                    archive,
                    curriculum_env,
                    previous_utilities,
                    rng,
                )
                curriculum_evaluation_steps += used_steps
                logger.log(curriculum_metrics, step)

            if step >= args.learning_starts and step % args.eval_freq == 0:
                eval_metrics, used_steps = validation_metrics(
                    args,
                    validation_env,
                    q_network,
                    validation_preferences,
                    reference_point,
                )
                validation_evaluation_steps += used_steps
                logger.log(
                    {key: value for key, value in eval_metrics.items() if value is not None},
                    step,
                )
                print(f"[{step}] validation: {eval_metrics}")

            if step % args.save_freq == 0:
                counters = {
                    "training_interactions": step,
                    "gradient_updates": gradient_updates,
                    "curriculum_evaluation_steps": curriculum_evaluation_steps,
                    "validation_evaluation_steps": validation_evaluation_steps,
                }
                save_checkpoint(
                    output_dir / f"checkpoint_step{step}.pt",
                    step,
                    q_network,
                    optimizer,
                    archive,
                    args,
                    protocol,
                    counters,
                )

        episodes += 1
        if terminated or truncated:
            archive.add(
                episode_return,
                {"step": step, "preference": behavior_preference.tolist()},
            )
        logger.log(
            {
                "episode/length": episode_length,
                "episode/utility": float(np.dot(behavior_preference, episode_return)),
                "episode/raw_utility": float(np.dot(behavior_preference, raw_episode_return)),
                "episode/archive_size": len(archive),
            },
            step,
        )
        if episodes % 10 == 0:
            elapsed = max(time.time() - started_at, 1e-6)
            print(f"episode={episodes} step={step} sps={int(step / elapsed)} archive={len(archive)}")

    counters = {
        "training_interactions": step,
        "gradient_updates": gradient_updates,
        "curriculum_evaluation_steps": curriculum_evaluation_steps,
        "validation_evaluation_steps": validation_evaluation_steps,
    }
    final_path = output_dir / "final.pt"
    save_checkpoint(final_path, step, q_network, optimizer, archive, args, protocol, counters)
    print(f"Training complete: {final_path.resolve()}")

    logger.finish()
    train_env.close()
    validation_env.close()
    curriculum_env.close()


if __name__ == "__main__":
    main()

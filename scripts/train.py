import argparse
import os
import sys
import time
import json
import torch
import torch.nn.functional as F
import numpy as np
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.logger import ExperimentLogger
from src.envs.wrapper import make_mo_env
from src.core.replay_buffer import VectorReplayBuffer
from src.core.pareto_archive import ParetoArchive
from src.models.q_network import VectorQNetwork
from src.curriculum.sampler import AdaptivePreferenceSampler
from src.curriculum.uncertainty import compute_bootstrap_uncertainty
from src.curriculum.gap import compute_conditioning_gap
from src.evaluation.metrics import compute_hypervolume, pareto_prune


def parse_args():
    parser = argparse.ArgumentParser(description="Train Adaptive Preference MORL Agent")
    parser.add_argument("--env", type=str, default="mo-lunar-lander-v2", help="Environment ID")
    parser.add_argument("--algo", type=str, default="adaptive-pcqn", choices=["adaptive-pcqn", "uniform-pcqn"], help="Algorithm type")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--total-timesteps", type=int, default=500000, help="Total environment steps")
    parser.add_argument("--learning-starts", type=int, default=5000, help="Steps before neural network training starts")
    parser.add_argument("--train-freq", type=int, default=4, help="Frequency of gradient updates (steps)")
    parser.add_argument("--batch-size", type=int, default=64, help="Batch size for gradient updates")
    parser.add_argument("--buffer-capacity", type=int, default=200000, help="Capacity of replay buffer")
    parser.add_argument("--lr", type=float, default=3e-4, help="Learning rate for Adam optimizer")
    parser.add_argument("--gamma", type=float, default=0.99, help="Discount factor")
    parser.add_argument("--target-update-freq", type=int, default=1000, help="Hard target network update frequency (steps)")
    parser.add_argument("--curriculum-update-freq", type=int, default=10000, help="Curriculum checkpoint update frequency (steps)")
    parser.add_argument("--eval-freq", type=int, default=25000, help="Evaluation frequency on unseen preferences")
    parser.add_argument("--eval-episodes", type=int, default=10, help="Number of evaluation episodes per eval checkpoint")
    parser.add_argument("--save-freq", type=int, default=50000, help="Checkpoint saving frequency (steps)")
    parser.add_argument("--eps-start", type=float, default=1.0, help="Starting epsilon for exploration")
    parser.add_argument("--eps-end", type=float, default=0.05, help="Ending epsilon for exploration")
    parser.add_argument("--eps-fraction", type=float, default=0.3, help="Fraction of total steps over which epsilon decays")
    parser.add_argument("--wandb-project", type=str, default="REL301m-MORL", help="WandB Project Name")
    parser.add_argument("--output-dir", type=str, default="checkpoints", help="Output directory for checkpoints")
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu", help="PyTorch device")
    return parser.parse_args()


def get_linear_epsilon(step: int, total_steps: int, eps_start: float, eps_end: float, fraction: float) -> float:
    decay_steps = int(total_steps * fraction)
    if step >= decay_steps:
        return eps_end
    return eps_start - (eps_start - eps_end) * (step / max(1, decay_steps))


def evaluate_policy(
    env,
    q_net: VectorQNetwork,
    device: str,
    reward_dim: int,
    num_preferences: int = 10,
    episodes_per_pref: int = 1,
    seed: int = 999
) -> dict:
    """Quick evaluation across random preference vectors to track Hypervolume."""
    q_net.eval()
    rng = np.random.default_rng(seed)
    eval_prefs = rng.dirichlet(np.ones(reward_dim), size=num_preferences).astype(np.float32)
    collected_returns = []

    for w in eval_prefs:
        w_tensor = torch.as_tensor(w, dtype=torch.float32, device=device).unsqueeze(0)
        for _ in range(episodes_per_pref):
            obs, _ = env.reset()
            ep_return = np.zeros(reward_dim, dtype=np.float32)
            done = False
            while not done:
                s_tensor = torch.as_tensor(obs, dtype=torch.float32, device=device).unsqueeze(0)
                with torch.no_grad():
                    action, _ = q_net.predict_action(s_tensor, w_tensor, head_idx=None)
                obs, reward, terminated, truncated, _ = env.step(action)
                ep_return += np.asarray(reward, dtype=np.float32)
                done = terminated or truncated
            collected_returns.append(ep_return)

    q_net.train()
    collected_returns = np.array(collected_returns, dtype=np.float32)
    pruned_frontier = pareto_prune(collected_returns)
    ref_point = np.zeros(reward_dim, dtype=np.float32) - 100.0  # conservative reference point
    hv = compute_hypervolume(pruned_frontier, ref_point)

    return {
        "eval_hypervolume": hv,
        "eval_mean_return_norm": float(np.mean(np.linalg.norm(collected_returns, axis=1))),
        "eval_frontier_size": len(pruned_frontier)
    }


def main():
    args = parse_args()
    print(f"=== Starting Training: {args.algo} on {args.env} (Seed: {args.seed}) on {args.device} ===")

    # Set seeds
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    os.makedirs(args.output_dir, exist_ok=True)

    # Initialize environment
    env = make_mo_env(args.env, seed=args.seed)
    eval_env = make_mo_env(args.env, seed=args.seed + 1000)

    state_dim = env.observation_space.shape[0]
    action_dim = env.action_space.n
    reward_dim = env.unwrapped.reward_space.shape[0] if hasattr(env.unwrapped, "reward_space") else 4

    print(f"Environment config: state_dim={state_dim}, action_dim={action_dim}, reward_dim={reward_dim}")

    # Initialize neural networks
    q_net = VectorQNetwork(state_dim, action_dim, reward_dim, num_heads=3).to(args.device)
    target_net = VectorQNetwork(state_dim, action_dim, reward_dim, num_heads=3).to(args.device)
    target_net.load_state_dict(q_net.state_dict())
    target_net.eval()

    optimizer = torch.optim.Adam(q_net.parameters(), lr=args.lr)

    # Replay buffer & Pareto archive
    replay_buffer = VectorReplayBuffer(
        capacity=args.buffer_capacity,
        state_dim=state_dim,
        action_dim=action_dim,
        reward_dim=reward_dim,
        device=args.device
    )
    pareto_archive = ParetoArchive(reward_dim=reward_dim)

    # Adaptive preference sampler
    sampler = AdaptivePreferenceSampler(reward_dim=reward_dim, pool_size=100, seed=args.seed)

    # Logger
    exp_name = f"{args.algo}_{args.env}_seed{args.seed}"
    logger = ExperimentLogger(
        project_name=args.wandb_project,
        experiment_name=exp_name,
        config=vars(args),
        use_wandb=bool(args.wandb_project)
    )

    # Training state
    step = 0
    episodes = 0
    rng = np.random.default_rng(args.seed)
    start_time = time.time()

    while step < args.total_timesteps:
        # Sample preference vector for the episode
        if args.algo == "adaptive-pcqn":
            w_ep = sampler.sample()
        else:
            # Uniform Dirichlet sampling for Uniform-PCQN baseline
            w_ep = rng.dirichlet(np.ones(reward_dim)).astype(np.float32)

        w_tensor = torch.as_tensor(w_ep, dtype=torch.float32, device=args.device).unsqueeze(0)

        obs, _ = env.reset()
        ep_return = np.zeros(reward_dim, dtype=np.float32)
        ep_length = 0
        done = False

        while not done and step < args.total_timesteps:
            epsilon = get_linear_epsilon(
                step, args.total_timesteps, args.eps_start, args.eps_end, args.eps_fraction
            )

            # Epsilon-greedy action selection
            if rng.random() < epsilon:
                action = env.action_space.sample()
            else:
                s_tensor = torch.as_tensor(obs, dtype=torch.float32, device=args.device).unsqueeze(0)
                with torch.no_grad():
                    action, _ = q_net.predict_action(s_tensor, w_tensor, head_idx=0)

            # Step environment
            next_obs, reward, terminated, truncated, _ = env.step(action)
            step += 1
            ep_length += 1
            ep_return += np.asarray(reward, dtype=np.float32)
            done = terminated or truncated

            # Store in vector replay buffer
            replay_buffer.add(obs, action, reward, next_obs, terminated)
            obs = next_obs

            # Gradient update
            if step >= args.learning_starts and step % args.train_freq == 0:
                s_b, a_b, r_b, ns_b, d_b = replay_buffer.sample(args.batch_size)
                B = s_b.size(0)

                # Relabeling: sample random preferences for batch updates to generalize across simplex
                w_batch = torch.as_tensor(
                    rng.dirichlet(np.ones(reward_dim), size=B),
                    dtype=torch.float32,
                    device=args.device
                )

                with torch.no_grad():
                    # 1. Double DQN: select best action with online network
                    q_next_online = q_net(ns_b, w_batch)  # [K, B, action_dim, reward_dim]
                    # Scalarize head 0 to pick greedy next action
                    scalarized_next = torch.einsum("kbad,bd->kba", q_next_online, w_batch)  # [K, B, action_dim]
                    a_star = torch.argmax(scalarized_next[0], dim=-1)  # [B]

                    # 2. Evaluate target Q at a_star with target network
                    q_next_target = target_net(ns_b, w_batch)  # [K, B, action_dim, reward_dim]
                    # Gather at a_star: [K, B, reward_dim]
                    target_q_at_astar = q_next_target[:, torch.arange(B), a_star, :]

                    # 3. Vector Bellman target: y = r + gamma * (1 - done) * Q_target
                    y_target = r_b.unsqueeze(0) + args.gamma * (1.0 - d_b.unsqueeze(-1).unsqueeze(0)) * target_q_at_astar

                # Current Q predictions: [K, B, action_dim, reward_dim]
                q_current = q_net(s_b, w_batch)
                q_pred_at_a = q_current[:, torch.arange(B), a_b, :]  # [K, B, reward_dim]

                # Huber loss across all heads and all objective dimensions
                loss = F.smooth_l1_loss(q_pred_at_a, y_target)

                optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(q_net.parameters(), max_norm=10.0)
                optimizer.step()

                if step % 500 == 0:
                    logger.log({
                        "train/loss": loss.item(),
                        "train/epsilon": epsilon,
                        "train/step": step
                    }, step=step)

            # Target network update
            if step % args.target_update_freq == 0:
                target_net.load_state_dict(q_net.state_dict())

            # Curriculum update checkpoint
            if args.algo == "adaptive-pcqn" and step >= args.learning_starts and step % args.curriculum_update_freq == 0:
                print(f"[{step}/{args.total_timesteps}] Updating Adaptive Curriculum...")
                pool = sampler.pool
                gap_scores = np.zeros(len(pool), dtype=np.float32)
                uncertainty_scores = np.zeros(len(pool), dtype=np.float32)

                # Sample batch of states for uncertainty estimation
                states_sample = replay_buffer.sample_states(min(128, len(replay_buffer)))

                for i, w_cand in enumerate(pool):
                    gap_scores[i] = compute_conditioning_gap(w_cand, pareto_archive)
                    uncertainty_scores[i] = compute_bootstrap_uncertainty(
                        q_net, states_sample, w_cand, device=args.device
                    )

                sampler.update_distribution(gap_scores, uncertainty_scores)

                entropy = -np.sum(sampler.probabilities * np.log(sampler.probabilities + 1e-12))
                logger.log({
                    "curriculum/mean_gap": float(np.mean(gap_scores)),
                    "curriculum/max_gap": float(np.max(gap_scores)),
                    "curriculum/mean_uncertainty": float(np.mean(uncertainty_scores)),
                    "curriculum/entropy": float(entropy)
                }, step=step)

            # Periodic evaluation
            if step % args.eval_freq == 0 and step >= args.learning_starts:
                eval_metrics = evaluate_policy(
                    eval_env, q_net, args.device, reward_dim,
                    num_preferences=10, episodes_per_pref=1, seed=args.seed + step
                )
                print(f"[{step} steps] Eval HV: {eval_metrics['eval_hypervolume']:.4f}, Frontier size: {eval_metrics['eval_frontier_size']}")
                logger.log({
                    "eval/hypervolume": eval_metrics["eval_hypervolume"],
                    "eval/frontier_size": eval_metrics["eval_frontier_size"],
                    "eval/mean_norm": eval_metrics["eval_mean_return_norm"]
                }, step=step)

            # Periodic checkpoint saving
            if step % args.save_freq == 0:
                ckpt_path = os.path.join(args.output_dir, f"{args.algo}_{args.env}_step{step}.pt")
                torch.save({
                    "step": step,
                    "model_state_dict": q_net.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "archive_points": pareto_archive.get_points(),
                    "args": vars(args)
                }, ckpt_path)
                print(f"Saved checkpoint to {ckpt_path}")

        # Episode finished
        episodes += 1
        pareto_archive.add(ep_return, meta={"step": step, "preference": w_ep})
        scalarized_utility = float(np.dot(w_ep, ep_return))

        if episodes % 10 == 0:
            elapsed = time.time() - start_time
            sps = int(step / max(1e-3, elapsed))
            print(f"Episode {episodes:4d} | Step {step:6d}/{args.total_timesteps} ({sps} sps) | Return Norm: {np.linalg.norm(ep_return):.2f} | Utility: {scalarized_utility:.2f} | Archive: {len(pareto_archive)}")

        logger.log({
            "episode/length": ep_length,
            "episode/utility": scalarized_utility,
            "episode/archive_size": len(pareto_archive)
        }, step=step)

    # Save final model
    final_path = os.path.join(args.output_dir, f"{args.algo}_{args.env}_final.pt")
    torch.save({
        "step": step,
        "model_state_dict": q_net.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "archive_points": pareto_archive.get_points(),
        "args": vars(args)
    }, final_path)
    print(f"=== Training Completed! Final checkpoint saved to {final_path} ===")

    logger.finish()
    env.close()
    eval_env.close()


if __name__ == "__main__":
    main()

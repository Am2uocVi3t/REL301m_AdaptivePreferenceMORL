import argparse
import os
import torch
import numpy as np
from src.utils.logger import ExperimentLogger
from src.utils.config import load_config
from src.envs.wrapper import make_mo_env
from src.core.replay_buffer import VectorReplayBuffer
from src.core.pareto_archive import ParetoArchive
from src.models.q_network import VectorQNetwork
from src.curriculum.sampler import AdaptivePreferenceSampler
from src.curriculum.uncertainty import compute_bootstrap_uncertainty
from src.curriculum.gap import compute_conditioning_gap

def parse_args():
    parser = argparse.ArgumentParser(description="Train Adaptive Preference MORL Agent")
    parser.add_argument("--env", type=str, default="mo-lunar-lander-v2", help="Environment ID")
    parser.add_argument("--algo", type=str, default="adaptive-pcqn", choices=["adaptive-pcqn", "uniform-pcqn"])
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--total-timesteps", type=int, default=500000, help="Total environment steps")
    parser.add_argument("--wandb-project", type=str, default="REL301m-MORL", help="WandB Project Name")
    parser.add_argument("--output-dir", type=str, default="checkpoints", help="Output directory for checkpoints")
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu")
    return parser.parse_args()

def main():
    args = parse_args()
    print(f"=== Starting Training: {args.algo} on {args.env} (Seed: {args.seed}) on {args.device} ===")

    # Set random seeds
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    os.makedirs(args.output_dir, exist_ok=True)

    # Initialize environment
    env = make_mo_env(args.env, seed=args.seed)
    state_dim = env.observation_space.shape[0]
    action_dim = env.action_space.n
    reward_dim = env.unwrapped.reward_space.shape[0] if hasattr(env.unwrapped, "reward_space") else 4

    print(f"Environment: state_dim={state_dim}, action_dim={action_dim}, reward_dim={reward_dim}")

    # Initialize components
    q_net = VectorQNetwork(state_dim, action_dim, reward_dim).to(args.device)
    replay_buffer = VectorReplayBuffer(capacity=200000, state_dim=state_dim, action_dim=action_dim, reward_dim=reward_dim, device=args.device)
    pareto_archive = ParetoArchive(reward_dim=reward_dim)
    sampler = AdaptivePreferenceSampler(reward_dim=reward_dim, seed=args.seed)

    # Initialize logger
    exp_name = f"{args.algo}_{args.env}_seed{args.seed}"
    logger = ExperimentLogger(project_name=args.wandb_project, experiment_name=exp_name, use_wandb=bool(args.wandb_project))

    print("Baseline setup complete and ready for pair implementation.")
    logger.finish()

if __name__ == "__main__":
    main()

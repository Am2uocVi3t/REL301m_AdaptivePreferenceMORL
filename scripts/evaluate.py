import argparse
import numpy as np
import torch
from src.envs.wrapper import make_mo_env
from src.evaluation.metrics import compute_hypervolume, compute_scalarized_regret, pareto_prune
from src.models.q_network import VectorQNetwork

def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate MORL Agent on Unseen Preferences & Dynamics Shifts")
    parser.add_argument("--env", type=str, default="mo-lunar-lander-v2")
    parser.add_argument("--model-path", type=str, required=False, help="Path to .pt model weights")
    parser.add_argument("--num-unseen-preferences", type=int, default=100)
    parser.add_argument("--seed", type=int, default=1000)
    return parser.parse_args()

def main():
    args = parse_args()
    print(f"=== Evaluating on {args.env} with {args.num_unseen_preferences} unseen preferences ===")
    rng = np.random.default_rng(args.seed)
    
    # Generate unseen test preferences on simplex Delta^{d-1}
    reward_dim = 4 if "lunar" in args.env else 3
    test_preferences = rng.dirichlet(np.ones(reward_dim), size=args.num_unseen_preferences)
    print(f"Generated {len(test_preferences)} test preferences with separate seed {args.seed}.")

if __name__ == "__main__":
    main()

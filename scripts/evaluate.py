import argparse
import os
import sys
import json
import torch
import numpy as np
from typing import Dict, Any, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.envs.wrapper import make_mo_env
from src.envs.shift import apply_dynamics_shift
from src.evaluation.metrics import compute_hypervolume, compute_scalarized_regret, pareto_prune
from src.evaluation.stats import bootstrap_ci
from src.models.q_network import VectorQNetwork


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate MORL Agent on Unseen Preferences & Dynamics Shifts")
    parser.add_argument("--env", type=str, default="mo-lunar-lander-v2", help="Environment ID")
    parser.add_argument("--model-path", type=str, default=None, help="Path to trained .pt checkpoint")
    parser.add_argument("--num-unseen-preferences", type=int, default=100, help="Number of test preferences on simplex")
    parser.add_argument("--episodes-per-pref", type=int, default=1, help="Evaluation episodes per preference")
    parser.add_argument("--seed", type=int, default=1000, help="Separate evaluation seed")
    parser.add_argument("--eval-shifts", action="store_true", default=True, help="Evaluate under dynamics shifts")
    parser.add_argument("--output-file", type=str, default="results/evaluation_report.json", help="Path to save summary report")
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu")
    return parser.parse_args()


def get_default_shifts(env_id: str) -> Dict[str, Dict[str, Any]]:
    """Returns preset dynamics shifts from Section 6.2 of the proposal."""
    if "lunar" in env_id.lower():
        return {
            "nominal": {"gravity": -10.0, "enable_wind": False, "wind_power": 0.0},
            "heavy_gravity": {"gravity": -15.0, "enable_wind": False},
            "strong_wind": {"gravity": -10.0, "enable_wind": True, "wind_power": 15.0, "turbulence_power": 0.5},
            "extreme_turbulence": {"gravity": -8.0, "enable_wind": True, "wind_power": 20.0, "turbulence_power": 1.5},
        }
    else:
        return {
            "nominal": {"fuel_cost_multiplier": 1.0},
            "high_friction": {"fuel_cost_multiplier": 1.5},
            "low_ore_yield": {"ore_multiplier": 0.7},
        }


def run_evaluation_rollouts(
    env,
    q_net: Optional[VectorQNetwork],
    preferences: np.ndarray,
    episodes_per_pref: int = 1,
    device: str = "cpu"
) -> np.ndarray:
    """Runs deterministic greedy evaluation rollouts for each preference."""
    reward_dim = preferences.shape[1]
    returns_list = []

    for idx, w in enumerate(preferences):
        w_tensor = torch.as_tensor(w, dtype=torch.float32, device=device).unsqueeze(0)
        for _ in range(episodes_per_pref):
            obs, _ = env.reset()
            ep_return = np.zeros(reward_dim, dtype=np.float32)
            done = False

            while not done:
                if q_net is not None:
                    s_tensor = torch.as_tensor(obs, dtype=torch.float32, device=device).unsqueeze(0)
                    with torch.no_grad():
                        # Ensemble mean action selection
                        action, _ = q_net.predict_action(s_tensor, w_tensor, head_idx=None)
                else:
                    action = env.action_space.sample()

                obs, reward, terminated, truncated, _ = env.step(action)
                ep_return += np.asarray(reward, dtype=np.float32)
                done = terminated or truncated

            returns_list.append(ep_return)

    return np.array(returns_list, dtype=np.float32)


def main():
    args = parse_args()
    print("=" * 70)
    print(f"🎯 MORL Evaluation Pipeline — Test Preferences & Dynamics Shift")
    print(f"Environment: {args.env} | Seed: {args.seed} | Device: {args.device}")
    print("=" * 70)

    os.makedirs(os.path.dirname(args.output_file) or ".", exist_ok=True)
    rng = np.random.default_rng(args.seed)

    # Initialize environment
    env = make_mo_env(args.env, seed=args.seed)
    state_dim = env.observation_space.shape[0]
    action_dim = env.action_space.n
    reward_dim = env.unwrapped.reward_space.shape[0] if hasattr(env.unwrapped, "reward_space") else 4

    # Generate unseen test preferences on simplex Delta^{d-1} (Proposal Sec 6.2)
    test_preferences = rng.dirichlet(np.ones(reward_dim), size=args.num_unseen_preferences).astype(np.float32)
    print(f"Generated {len(test_preferences)} hold-out test preferences with separate seed {args.seed}.")

    # Load trained model if available
    q_net = None
    if args.model_path and os.path.exists(args.model_path):
        print(f"Loading checkpoint weights from: {args.model_path}")
        q_net = VectorQNetwork(state_dim, action_dim, reward_dim, num_heads=3).to(args.device)
        try:
            checkpoint = torch.load(args.model_path, map_location=args.device, weights_only=False)
        except TypeError:
            checkpoint = torch.load(args.model_path, map_location=args.device)
        if "model_state_dict" in checkpoint:
            q_net.load_state_dict(checkpoint["model_state_dict"])
        else:
            q_net.load_state_dict(checkpoint)
        q_net.eval()
    else:
        print("[Notice] No checkpoint found or provided. Running baseline heuristic / random evaluation.")

    shifts_dict = get_default_shifts(args.env)
    ref_point = np.zeros(reward_dim, dtype=np.float32) - 100.0  # conservative reference point

    results: Dict[str, Any] = {
        "env": args.env,
        "model_path": args.model_path,
        "num_unseen_preferences": args.num_unseen_preferences,
        "seed": args.seed,
        "shifts": {}
    }

    # 1. Evaluate on Nominal Condition
    print("\n--- 1. Evaluating on Nominal Dynamics ---")
    apply_dynamics_shift(env, shifts_dict["nominal"])
    nominal_returns = run_evaluation_rollouts(
        env, q_net, test_preferences, episodes_per_pref=args.episodes_per_pref, device=args.device
    )

    nominal_frontier = pareto_prune(nominal_returns)
    nominal_hv = compute_hypervolume(nominal_frontier, ref_point)
    nominal_regret = compute_scalarized_regret(nominal_returns, nominal_frontier, test_preferences)

    # Compute utilities across test preferences
    nominal_utilities = np.sum(test_preferences * nominal_returns, axis=1)
    mean_u, ci_low_u, ci_high_u = bootstrap_ci(nominal_utilities, n_boot=1000)

    results["shifts"]["nominal"] = {
        "hypervolume": nominal_hv,
        "pareto_frontier_size": len(nominal_frontier),
        "mean_utility": mean_u,
        "utility_95_ci": [ci_low_u, ci_high_u],
        "mean_regret": nominal_regret["mean_regret"],
        "worst_decile_regret": nominal_regret["worst_decile_regret"],
        "max_regret": nominal_regret["max_regret"],
    }

    print(f"Nominal HV: {nominal_hv:.4f}")
    print(f"Nominal Mean Utility: {mean_u:.2f} (95% CI: [{ci_low_u:.2f}, {ci_high_u:.2f}])")
    print(f"Nominal Worst-Decile Regret: {nominal_regret['worst_decile_regret']:.4f}")

    # 2. Evaluate under Dynamics Shifts
    if args.eval_shifts:
        print("\n--- 2. Evaluating Zero-Shot Robustness Under Dynamics Shifts ---")
        for shift_name, shift_config in shifts_dict.items():
            if shift_name == "nominal":
                continue

            print(f"Testing condition: [{shift_name}] -> {shift_config}")
            apply_dynamics_shift(env, shift_config)
            shift_returns = run_evaluation_rollouts(
                env, q_net, test_preferences, episodes_per_pref=args.episodes_per_pref, device=args.device
            )

            shift_frontier = pareto_prune(shift_returns)
            shift_hv = compute_hypervolume(shift_frontier, ref_point)
            shift_regret = compute_scalarized_regret(shift_returns, nominal_frontier, test_preferences)
            shift_utilities = np.sum(test_preferences * shift_returns, axis=1)

            # Degradation relative to nominal
            degradation = max(0.0, (nominal_hv - shift_hv) / max(1e-6, nominal_hv)) if nominal_hv > 0 else 0.0

            results["shifts"][shift_name] = {
                "hypervolume": shift_hv,
                "hv_degradation_ratio": degradation,
                "mean_utility": float(np.mean(shift_utilities)),
                "worst_decile_regret": shift_regret["worst_decile_regret"],
                "pareto_frontier_size": len(shift_frontier)
            }
            print(f"  -> Shift HV: {shift_hv:.4f} | Degradation: {degradation * 100:.2f}% | Worst-Decile Regret: {shift_regret['worst_decile_regret']:.4f}")

    # Save summary results
    with open(args.output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\n✅ Evaluation report successfully exported to: {args.output_file}")
    env.close()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.baselines.morl_baselines_runner import (
    run_envelope_baseline,
    run_gpi_ls_baseline,
)
from src.evaluation.protocol import load_protocol, resolve_reference_point


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a pinned MORL-Baselines comparator")
    parser.add_argument("--baseline", choices=("envelope", "gpi-ls"), required=True)
    parser.add_argument("--protocol", required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--total-timesteps", type=int, default=500_000)
    parser.add_argument("--eval-freq", type=int, default=25_000)
    parser.add_argument("--wandb-project", default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    protocol, _ = load_protocol(args.protocol, "validation")
    reference_point = resolve_reference_point(protocol)
    if reference_point is None:
        raise ValueError("Freeze reference_point in the protocol after the pilot before running baselines")

    runner = run_envelope_baseline if args.baseline == "envelope" else run_gpi_ls_baseline
    runner(
        env_id=protocol["env_id"],
        ref_point=reference_point,
        seed=args.seed,
        total_timesteps=args.total_timesteps,
        eval_freq=args.eval_freq,
        wandb_project=args.wandb_project,
    )


if __name__ == "__main__":
    main()

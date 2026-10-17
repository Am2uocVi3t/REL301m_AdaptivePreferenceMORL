#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.baselines.morl_baselines_runner import (
    run_envelope_baseline,
    run_gpi_ls_baseline,
)
from src.evaluation.protocol import load_protocol, resolve_reference_point, resolve_reward_scale
from src.utils.provenance import collect_provenance, write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a pinned MORL-Baselines comparator")
    parser.add_argument("--baseline", choices=("envelope", "gpi-ls"), required=True)
    parser.add_argument("--protocol", required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--total-timesteps", type=int, default=500_000)
    parser.add_argument("--eval-freq", type=int, default=25_000)
    parser.add_argument("--wandb-project", default=None)
    parser.add_argument("--output-dir", default="artifacts/baselines")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    protocol, _ = load_protocol(args.protocol, "validation")
    reference_point = resolve_reference_point(protocol)
    reward_scale = resolve_reward_scale(protocol)
    if reference_point is None:
        raise ValueError("Freeze reference_point in the protocol after the pilot before running baselines")

    runner = run_envelope_baseline if args.baseline == "envelope" else run_gpi_ls_baseline
    agent = runner(
        env_id=protocol["env_id"],
        ref_point=reference_point,
        seed=args.seed,
        total_timesteps=args.total_timesteps,
        eval_freq=args.eval_freq,
        wandb_project=args.wandb_project,
        reward_scale=reward_scale,
    )
    output_dir = Path(args.output_dir) / f"{args.baseline}_{protocol['env_id']}_seed{args.seed}"
    output_dir.mkdir(parents=True, exist_ok=True)
    agent.save(save_replay_buffer=False, save_dir=str(output_dir), filename="final")
    summary = getattr(agent, "rel301m_run_summary", {"global_step": int(agent.global_step)})
    write_json(
        output_dir / "run_manifest.json",
        {
            "schema_version": 1,
            "baseline": args.baseline,
            "protocol": protocol,
            "summary": summary,
            "final_artifact": str(output_dir / "final.tar"),
            "provenance": collect_provenance(vars(args)),
        },
    )
    print(f"Baseline training complete: {(output_dir / 'final.tar').resolve()}")


if __name__ == "__main__":
    main()

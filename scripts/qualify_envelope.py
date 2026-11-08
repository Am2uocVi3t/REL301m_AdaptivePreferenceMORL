#!/usr/bin/env python3
from __future__ import annotations

import argparse
import platform
import sys
from importlib import metadata
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.baselines.morl_baselines_runner import run_envelope_baseline
from src.evaluation.protocol import load_protocol, protocol_hash, resolve_reference_point, resolve_reward_scale
from src.utils.provenance import collect_provenance, write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run bounded behavioral Envelope qualification smokes")
    parser.add_argument(
        "--protocols",
        nargs="+",
        default=(
            "configs/protocols/course_mo_lunar_lander_v3.json",
            "configs/protocols/course_minecart_v0.json",
        ),
    )
    parser.add_argument("--total-timesteps", type=int, default=200)
    parser.add_argument("--seed", type=int, default=20263011)
    parser.add_argument("--output", default="research/qualification/envelope_python311_smoke.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if sys.version_info[:2] != (3, 11):
        raise RuntimeError(f"Envelope qualification requires Python 3.11, got {platform.python_version()}")
    if args.total_timesteps <= 64:
        raise ValueError("total-timesteps must exceed the smoke learning-start threshold of 64")

    root = Path(__file__).resolve().parents[1]
    results: list[dict[str, Any]] = []
    for index, relative_protocol in enumerate(args.protocols):
        protocol, _ = load_protocol(root / relative_protocol, "validation")
        reference_point = resolve_reference_point(protocol)
        if reference_point is None:
            raise ValueError(f"Protocol reference point is not frozen: {relative_protocol}")
        agent = run_envelope_baseline(
            env_id=protocol["env_id"],
            ref_point=reference_point,
            seed=args.seed + index,
            total_timesteps=args.total_timesteps,
            eval_freq=args.total_timesteps + 1,
            reward_scale=resolve_reward_scale(protocol),
            agent_kwargs={
                "learning_starts": 64,
                "batch_size": 32,
                "gradient_updates": 1,
                "buffer_size": 2_000,
                "net_arch": [64, 64],
                "num_sample_w": 2,
                "device": "cpu",
            },
        )
        summary = dict(agent.rel301m_run_summary)
        passed = (
            summary["global_step"] == args.total_timesteps
            and summary["replay_size"] == args.total_timesteps
            and summary["parameters_changed"] is True
        )
        results.append(
            {
                "env_id": protocol["env_id"],
                "protocol": relative_protocol,
                "protocol_sha256": protocol_hash(protocol),
                "seed": args.seed + index,
                "passed": passed,
                **summary,
            }
        )

    payload = {
        "schema_version": 1,
        "qualification": "envelope-behavioral-smoke",
        "python_requirement": "3.11",
        "python": platform.python_version(),
        "dependencies": {
            "morl-baselines": metadata.version("morl-baselines"),
            "mo-gymnasium": metadata.version("mo-gymnasium"),
        },
        "bounded_smoke_only": True,
        "establishes_comparative_performance": False,
        "passed": all(result["passed"] for result in results),
        "results": results,
        "provenance": collect_provenance(vars(args)),
    }
    write_json(root / args.output, payload)
    print(f"Wrote Envelope qualification to {args.output}; passed={payload['passed']}")
    if not payload["passed"]:
        raise RuntimeError("Envelope behavioral qualification failed")


if __name__ == "__main__":
    main()

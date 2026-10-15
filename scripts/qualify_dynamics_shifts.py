#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.envs.wrapper import make_mo_env
from src.utils.config import load_config
from src.utils.provenance import collect_provenance, write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Behaviorally qualify every enabled dynamics shift")
    parser.add_argument("--shift-file", default="configs/shifts/dynamics_shifts.yaml")
    parser.add_argument("--seeds", nargs="+", type=int, default=(20264001, 20264002, 20264003))
    parser.add_argument("--steps", type=int, default=300)
    parser.add_argument("--output", default="research/qualification/dynamics_shifts_v1.json")
    return parser.parse_args()


def rollout(env_id: str, shift: dict[str, Any], seed: int, actions: list[int]) -> dict[str, Any]:
    env = make_mo_env(env_id, seed=seed, dynamics_shift_config=shift)
    observation, _ = env.reset(seed=seed)
    observations = [np.asarray(observation, dtype=np.float64)]
    rewards: list[np.ndarray] = []
    endings: list[tuple[bool, bool]] = []
    for action in actions:
        observation, reward, terminated, truncated, _ = env.step(action)
        observations.append(np.asarray(observation, dtype=np.float64))
        rewards.append(np.asarray(reward, dtype=np.float64))
        endings.append((bool(terminated), bool(truncated)))
        if terminated or truncated:
            break
    attributes = {
        name: getattr(env.unwrapped, name)
        for name in ("gravity", "enable_wind", "wind_power", "turbulence_power")
        if hasattr(env.unwrapped, name)
    }
    env.close()
    return {"observations": observations, "rewards": rewards, "endings": endings, "attributes": attributes}


def compare_rollouts(nominal: dict[str, Any], shifted: dict[str, Any]) -> dict[str, Any]:
    common_observations = min(len(nominal["observations"]), len(shifted["observations"]))
    common_rewards = min(len(nominal["rewards"]), len(shifted["rewards"]))
    observation_delta = max(
        np.linalg.norm(nominal["observations"][index] - shifted["observations"][index])
        for index in range(common_observations)
    )
    reward_delta = max(
        (np.linalg.norm(nominal["rewards"][index] - shifted["rewards"][index]) for index in range(common_rewards)),
        default=0.0,
    )
    termination_changed = nominal["endings"] != shifted["endings"]
    changed = observation_delta > 1e-8 or reward_delta > 1e-8 or termination_changed
    return {
        "changed": changed,
        "max_observation_l2_delta": float(observation_delta),
        "max_reward_l2_delta": float(reward_delta),
        "termination_trace_changed": termination_changed,
        "nominal_steps": len(nominal["rewards"]),
        "shifted_steps": len(shifted["rewards"]),
        "nominal_attributes": nominal["attributes"],
        "shifted_attributes": shifted["attributes"],
    }


def configuration_applied(attributes: dict[str, Any], shift_config: dict[str, Any]) -> bool:
    requested = dict(shift_config.get("constructor_kwargs", {})) | dict(shift_config.get("attribute_overrides", {}))
    return all(name in attributes and attributes[name] == value for name, value in requested.items())


def main() -> None:
    args = parse_args()
    root = Path(__file__).resolve().parents[1]
    shift_path = root / args.shift_file
    config = load_config(str(shift_path))
    results: list[dict[str, Any]] = []

    for env_id, env_shifts in config.items():
        if not isinstance(env_shifts, dict) or "nominal" not in env_shifts:
            raise ValueError(f"Every environment must declare nominal dynamics: {env_id}")
        enabled = {name: value for name, value in env_shifts.items() if not name.startswith("_")}
        nominal_config = enabled.pop("nominal")
        for shift_name, shift_config in enabled.items():
            seed_results = []
            for seed in args.seeds:
                probe = make_mo_env(env_id, seed=seed)
                action_count_value = getattr(probe.action_space, "n", None)
                if action_count_value is None:
                    raise ValueError(f"Shift qualification requires a discrete action space: {env_id}")
                action_count = int(action_count_value)
                probe.close()
                actions = [index % action_count for index in range(args.steps)]
                nominal = rollout(env_id, nominal_config, seed, actions)
                shifted = rollout(env_id, shift_config, seed, actions)
                comparison = compare_rollouts(nominal, shifted)
                comparison["nominal_configuration_applied"] = configuration_applied(
                    nominal["attributes"], nominal_config
                )
                comparison["shift_configuration_applied"] = configuration_applied(shifted["attributes"], shift_config)
                seed_results.append({"seed": seed, **comparison})
            results.append(
                {
                    "env_id": env_id,
                    "shift": shift_name,
                    "declared_shift": shift_config,
                    "passed": all(
                        result["changed"]
                        and result["nominal_configuration_applied"]
                        and result["shift_configuration_applied"]
                        for result in seed_results
                    ),
                    "seeds": seed_results,
                }
            )

    payload = {
        "schema_version": 1,
        "qualification": "enabled-dynamics-shifts",
        "shift_file": args.shift_file,
        "shift_file_sha256": hashlib.sha256(shift_path.read_bytes()).hexdigest(),
        "controlled_action_trace": "cyclic discrete actions shared by nominal and shifted rollouts",
        "bounded_behavioral_test_only": True,
        "establishes_robustness": False,
        "passed": bool(results) and all(result["passed"] for result in results),
        "results": results,
        "disabled_entries": {
            env_id: {name: value for name, value in env_shifts.items() if name.startswith("_")}
            for env_id, env_shifts in config.items()
        },
        "provenance": collect_provenance(vars(args)),
    }
    write_json(root / args.output, payload)
    print(json.dumps({"output": args.output, "enabled_shifts": len(results), "passed": payload["passed"]}))
    if not payload["passed"]:
        raise RuntimeError("At least one enabled shift failed behavioral qualification")


if __name__ == "__main__":
    main()

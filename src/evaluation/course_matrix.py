from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from src.evaluation.protocol import load_protocol, protocol_hash

SIGNAL_KEYS = ("gap", "uncertainty", "coverage_recency", "progress", "geometry")


def load_course_study(path: str | Path) -> dict[str, Any]:
    config_path = Path(path)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    validate_course_study(config, config_path.parents[2])
    return config


def validate_course_study(config: dict[str, Any], root: Path) -> None:
    if config.get("schema_version") != 1 or config.get("status") != "frozen":
        raise ValueError("Course study must use schema_version 1 and status='frozen'")
    seeds = config.get("paired_seeds", [])
    if len(seeds) < 2 or len(seeds) != len(set(seeds)):
        raise ValueError("paired_seeds must contain at least two unique seeds")

    budget = config.get("budget", {})
    if int(budget.get("training_interactions", 0)) <= int(budget.get("learning_starts", -1)):
        raise ValueError("training_interactions must exceed learning_starts")
    if int(budget.get("final_episodes_per_preference", 0)) <= 0:
        raise ValueError("final_episodes_per_preference must be positive")

    environments = config.get("environments", [])
    if not environments:
        raise ValueError("At least one environment is required")
    for environment in environments:
        protocol_path = root / environment["protocol"]
        protocol, _ = load_protocol(protocol_path, "validation")
        if protocol["env_id"] != environment["env_id"]:
            raise ValueError(f"Protocol environment mismatch for {environment['env_id']}")
        if protocol.get("reference_point_status") != "frozen_from_source_aware_calibration_v2":
            raise ValueError(f"Protocol is not frozen for {environment['env_id']}")

    arms = config.get("pcqn_arms", [])
    arm_ids = [arm.get("id") for arm in arms]
    if not arms or len(arm_ids) != len(set(arm_ids)):
        raise ValueError("pcqn_arms must have unique IDs")
    for arm in arms:
        weights = arm.get("signal_weights", {})
        if set(weights) != set(SIGNAL_KEYS):
            raise ValueError(f"Arm {arm.get('id')} must define exactly {SIGNAL_KEYS}")
        if any(float(value) < 0.0 for value in weights.values()):
            raise ValueError(f"Arm {arm.get('id')} has a negative signal weight")
        if arm.get("algo") == "adaptive-pcqn" and sum(float(value) for value in weights.values()) <= 0.0:
            raise ValueError(f"Adaptive arm {arm.get('id')} needs a positive signal weight")

    primary = config.get("analysis", {}).get("primary_contrast", {})
    if {primary.get("treatment"), primary.get("control")} - set(arm_ids):
        raise ValueError("Primary contrast references an unknown PCQN arm")
    if config.get("checkpoint_selection", {}).get("split") != "validation":
        raise ValueError("Checkpoint selection must use validation only")
    if config.get("final_evaluation", {}).get("split") != "test_once_after_lock":
        raise ValueError("Final evaluation must be a one-time post-lock test")


def build_course_manifest(config: dict[str, Any], root: Path) -> dict[str, Any]:
    validate_course_study(config, root)
    config_hash = _canonical_hash(config)
    budget = config["budget"]
    jobs: list[dict[str, Any]] = []
    protocols: dict[str, str] = {}

    for environment in config["environments"]:
        env_id = environment["env_id"]
        protocol_path = environment["protocol"]
        protocol, _ = load_protocol(root / protocol_path, "validation")
        protocols[protocol_path] = protocol_hash(protocol)
        for arm in config["pcqn_arms"]:
            for seed in config["paired_seeds"]:
                output_root = f"artifacts/{config['id']}/{env_id}/{arm['id']}"
                jobs.append(
                    {
                        "job_id": f"{env_id}__{arm['id']}__seed{seed}",
                        "family": "pcqn",
                        "environment": env_id,
                        "arm": arm["id"],
                        "seed": seed,
                        "status": "planned",
                        "output_root": output_root,
                        "final_artifact": (f"{output_root}/{arm['algo']}_{env_id}_seed{seed}/final.pt"),
                        "command": _pcqn_command(environment, arm, seed, budget, output_root),
                    }
                )

        for comparator in config.get("comparators", []):
            for seed in config["paired_seeds"]:
                output_root = f"artifacts/{config['id']}/{env_id}/{comparator['id']}"
                jobs.append(
                    {
                        "job_id": f"{env_id}__{comparator['id']}__seed{seed}",
                        "family": "morl_baseline",
                        "environment": env_id,
                        "arm": comparator["id"],
                        "seed": seed,
                        "status": "blocked_pending_qualification",
                        "qualification_gate": comparator["qualification_gate"],
                        "output_root": output_root,
                        "final_artifact": f"{output_root}/{comparator['runner']}_{env_id}_seed{seed}/final.tar",
                        "command": _baseline_command(environment, comparator, seed, budget, output_root),
                    }
                )

    return {
        "schema_version": 1,
        "study_id": config["id"],
        "study_config_sha256": config_hash,
        "protocol_sha256": protocols,
        "execution_authorized": False,
        "job_count": len(jobs),
        "paired_seeds": config["paired_seeds"],
        "jobs": jobs,
    }


def _pcqn_command(
    environment: dict[str, Any],
    arm: dict[str, Any],
    seed: int,
    budget: dict[str, Any],
    output_root: str,
) -> list[str]:
    weights = arm["signal_weights"]
    return [
        "python",
        "scripts/train.py",
        "--env",
        environment["env_id"],
        "--protocol",
        environment["protocol"],
        "--algo",
        arm["algo"],
        "--allocation-target",
        arm["allocation_target"],
        "--seed",
        str(seed),
        "--total-timesteps",
        str(budget["training_interactions"]),
        "--learning-starts",
        str(budget["learning_starts"]),
        "--train-freq",
        str(budget["train_frequency"]),
        "--curriculum-update-freq",
        str(budget["curriculum_update_frequency"]),
        "--curriculum-eval-episodes",
        str(budget["curriculum_episodes_per_preference"]),
        "--eval-freq",
        str(budget["validation_frequency"]),
        "--eval-episodes",
        str(budget["validation_episodes_per_preference"]),
        "--gap-weight",
        str(weights["gap"]),
        "--uncertainty-weight",
        str(weights["uncertainty"]),
        "--coverage-weight",
        str(weights["coverage_recency"]),
        "--progress-weight",
        str(weights["progress"]),
        "--geometry-weight",
        str(weights["geometry"]),
        "--output-dir",
        output_root,
    ]


def _baseline_command(
    environment: dict[str, Any],
    comparator: dict[str, Any],
    seed: int,
    budget: dict[str, Any],
    output_root: str,
) -> list[str]:
    return [
        "python",
        "scripts/train_baseline.py",
        "--baseline",
        comparator["runner"],
        "--protocol",
        environment["protocol"],
        "--seed",
        str(seed),
        "--total-timesteps",
        str(budget["training_interactions"]),
        "--eval-freq",
        str(budget["validation_frequency"]),
        "--output-dir",
        output_root,
    ]


def _canonical_hash(value: dict[str, Any]) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()

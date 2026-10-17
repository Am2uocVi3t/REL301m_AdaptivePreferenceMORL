from __future__ import annotations

from pathlib import Path
from typing import Any

from src.evaluation.calibration import calibration_plan_hash, calibration_source_type, validate_calibration_plan


def build_pilot_jobs(
    plan: dict[str, Any],
    *,
    output_dir: str | Path,
    python_executable: str,
    device: str,
    smoke: bool,
) -> list[dict[str, Any]]:
    validate_calibration_plan(plan)
    root = Path(output_dir)
    training = plan["training"]
    evaluation = plan["evaluation"]
    seeds = plan["seeds"][:1] if smoke else plan["seeds"]
    total_timesteps = int(plan["smoke"]["total_timesteps"] if smoke else training["total_timesteps"])
    learning_starts = int(plan["smoke"]["learning_starts"] if smoke else training["learning_starts"])
    episodes = int(plan["smoke"]["episodes_per_preference"] if smoke else evaluation["episodes_per_preference"])

    jobs: list[dict[str, Any]] = []
    for environment_index, environment in enumerate(plan["environments"]):
        if calibration_source_type(environment) != "validation_pilot":
            continue
        env_id = str(environment["env_id"])
        protocol = str(environment["protocol"])
        training_root = root / "training" / env_id
        for seed_index, seed in enumerate(seeds):
            checkpoint = training_root / f"uniform-pcqn_{env_id}_seed{seed}" / "final.pt"
            evaluation_seed = int(evaluation["seed_base"]) + environment_index * 100_000 + seed_index * 10_000
            evaluation_output = root / "evaluations" / f"{env_id}_seed{seed}.json"
            train_command = [
                python_executable,
                "scripts/train.py",
                "--env",
                env_id,
                "--protocol",
                protocol,
                "--algo",
                "uniform-pcqn",
                "--allocation-target",
                "rollout_and_update",
                "--seed",
                str(seed),
                "--total-timesteps",
                str(total_timesteps),
                "--learning-starts",
                str(learning_starts),
                "--train-freq",
                str(training["train_freq"]),
                "--batch-size",
                str(training["batch_size"]),
                "--buffer-capacity",
                str(training["buffer_capacity"]),
                "--curriculum-update-freq",
                str(total_timesteps + 1),
                "--eval-freq",
                str(total_timesteps + 1),
                "--save-freq",
                str(total_timesteps),
                "--output-dir",
                str(training_root),
                "--device",
                device,
            ]
            evaluation_command = [
                python_executable,
                "scripts/evaluate.py",
                "--model-path",
                str(checkpoint),
                "--protocol",
                protocol,
                "--split",
                "validation",
                "--episodes-per-preference",
                str(episodes),
                "--seed",
                str(evaluation_seed),
                "--shift",
                "nominal",
                "--output",
                str(evaluation_output),
                "--device",
                device,
            ]
            jobs.append(
                {
                    "env_id": env_id,
                    "protocol": protocol,
                    "training_seed": seed,
                    "evaluation_seed": evaluation_seed,
                    "training_interaction_budget": total_timesteps,
                    "validation_episodes_per_preference": episodes,
                    "checkpoint": str(checkpoint),
                    "evaluation_output": str(evaluation_output),
                    "train_command": train_command,
                    "evaluation_command": evaluation_command,
                    "status": "planned",
                }
            )
    return jobs


def pilot_manifest(
    plan: dict[str, Any],
    jobs: list[dict[str, Any]],
    *,
    plan_path: str,
    smoke: bool,
    provenance: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "kind": "pilot_calibration_manifest",
        "mode": "smoke" if smoke else "pilot",
        "eligible_for_freeze_evidence": False,
        "plan": plan_path,
        "plan_sha256": calibration_plan_hash(plan),
        "provenance": provenance,
        "jobs": jobs,
    }

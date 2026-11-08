#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.evaluation.calibration import (
    calibration_plan_hash,
    calibration_source_type,
    load_calibration_plan,
    propose_calibration,
    validate_calibration_artifact,
    validate_reference_front_artifact,
)
from src.evaluation.protocol import protocol_hash
from src.utils.provenance import collect_provenance, write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Propose pilot-derived MORL reward scales and HV reference points")
    parser.add_argument("--plan", default="configs/pilots/calibration_v1.json")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return value


def main() -> None:
    args = parse_args()
    plan = load_calibration_plan(args.plan)
    manifest = load_json(args.manifest)
    if manifest.get("kind") != "pilot_calibration_manifest":
        raise ValueError("Manifest is not a pilot calibration manifest")
    if manifest.get("plan_sha256") != calibration_plan_hash(plan):
        raise ValueError("Pilot manifest does not match the supplied calibration plan")
    if any(job.get("status") != "complete" for job in manifest.get("jobs", [])):
        raise ValueError("Every pilot job must be complete before calibration")

    mode = manifest.get("mode")
    if mode not in {"pilot", "smoke"}:
        raise ValueError("Pilot manifest mode must be 'pilot' or 'smoke'")
    expected_seeds = plan["seeds"] if mode == "pilot" else plan["seeds"][:1]
    expected_training_budget = int(
        plan["training"]["total_timesteps"] if mode == "pilot" else plan["smoke"]["total_timesteps"]
    )
    expected_episode_budget = int(
        plan["evaluation"]["episodes_per_preference"] if mode == "pilot" else plan["smoke"]["episodes_per_preference"]
    )
    jobs = manifest["jobs"]
    pilot_environments = [
        environment
        for environment in plan["environments"]
        if calibration_source_type(environment) == "validation_pilot"
    ]
    expected_job_count = len(pilot_environments) * len(expected_seeds)
    if len(jobs) != expected_job_count:
        raise ValueError(f"Expected {expected_job_count} jobs for {mode} calibration, found {len(jobs)}")

    environment_proposals: dict[str, Any] = {}
    source_artifacts: list[dict[str, Any]] = []
    seen_jobs: set[tuple[str, int]] = set()
    for environment in plan["environments"]:
        env_id = str(environment["env_id"])
        protocol_path = Path(environment["protocol"])
        protocol = load_json(protocol_path)
        expected_protocol_hash = protocol_hash(protocol)
        source_type = calibration_source_type(environment)
        environment_returns: list[np.ndarray] = []
        if source_type == "validation_pilot":
            environment_jobs = [job for job in jobs if job.get("env_id") == env_id]
            if len(environment_jobs) != len(expected_seeds):
                raise ValueError(f"Environment {env_id} does not have the predeclared seed count")

            for job in environment_jobs:
                training_seed = int(job["training_seed"])
                if training_seed not in expected_seeds or (env_id, training_seed) in seen_jobs:
                    raise ValueError(f"Unexpected or duplicate job for {env_id} seed {training_seed}")
                seen_jobs.add((env_id, training_seed))
                if job.get("protocol") != str(protocol_path):
                    raise ValueError(f"Pilot job protocol does not match the plan for {env_id}")
                if int(job.get("training_interaction_budget", -1)) != expected_training_budget:
                    raise ValueError(f"Pilot job training budget does not match the plan for {env_id}")
                if int(job.get("validation_episodes_per_preference", -1)) != expected_episode_budget:
                    raise ValueError(f"Pilot job evaluation budget does not match the plan for {env_id}")
                artifact_path = Path(job["evaluation_output"])
                artifact = load_json(artifact_path)
                returns = validate_calibration_artifact(
                    artifact,
                    expected_env_id=env_id,
                    expected_protocol_sha256=expected_protocol_hash,
                    expected_seed=int(job["evaluation_seed"]),
                    return_field=str(plan["calibration_rule"]["return_field"]),
                    expected_checkpoint=str(job["checkpoint"]),
                    expected_episodes_per_preference=expected_episode_budget,
                )
                environment_returns.append(returns)
                source_artifacts.append(
                    {
                        "source_type": source_type,
                        "env_id": env_id,
                        "training_seed": training_seed,
                        "evaluation_seed": int(job["evaluation_seed"]),
                        "path": str(artifact_path),
                        "sha256": file_sha256(artifact_path),
                    }
                )
        else:
            source = environment["calibration_source"]
            artifact_path = Path(source["artifact"])
            artifact = load_json(artifact_path)
            return_definition = protocol.get("return_definition", {})
            reward_dim = int(protocol["reward_dim"])
            reward_scale = np.asarray(protocol.get("reward_scale"), dtype=np.float64)
            if reward_scale.shape != (reward_dim,) or not np.allclose(reward_scale, 1.0):
                raise ValueError("Reference-front calibration requires an unfrozen identity reward scale")
            values = validate_reference_front_artifact(
                artifact,
                expected_env_id=env_id,
                expected_reward_dim=reward_dim,
                expected_gamma=float(return_definition.get("gamma", -1.0)),
                expected_plan_sha256=calibration_plan_hash(plan),
                expected_protocol_sha256=expected_protocol_hash,
                expected_source=source,
            )
            environment_returns.append(values)
            source_artifacts.append(
                {
                    "source_type": source_type,
                    "env_id": env_id,
                    "path": str(artifact_path),
                    "sha256": file_sha256(artifact_path),
                }
            )

        proposal = propose_calibration(
            np.concatenate(environment_returns),
            plan["calibration_rule"],
            allow_degenerate=mode == "smoke",
        )
        proposal["protocol"] = str(protocol_path)
        proposal["protocol_sha256"] = expected_protocol_hash
        proposal["source_type"] = source_type
        proposal["proposed_protocol_patch"] = {
            "reward_scale": proposal["proposed_reward_scale"],
            "reference_point": proposal["proposed_reference_point"],
            "reference_point_status": "pilot_proposal_requires_review",
        }
        environment_proposals[env_id] = proposal

    if len(seen_jobs) != len(jobs):
        raise ValueError("Pilot manifest contains jobs not declared by a validation-pilot source")

    is_pilot = mode == "pilot"
    eligible_for_review = bool(is_pilot and manifest.get("eligible_for_freeze_evidence"))
    output = {
        "schema_version": 1,
        "kind": "pilot_calibration_proposal",
        "status": "review_required" if eligible_for_review else "smoke_only_not_freezable",
        "eligible_for_freeze_review": eligible_for_review,
        "automatic_protocol_mutation": False,
        "plan": args.plan,
        "plan_sha256": calibration_plan_hash(plan),
        "manifest": args.manifest,
        "manifest_sha256": file_sha256(args.manifest),
        "source_artifacts": source_artifacts,
        "environments": environment_proposals,
        "provenance": collect_provenance(vars(args)),
    }
    write_json(args.output, output)
    print(f"Wrote {output['status']} calibration proposal to {Path(args.output).resolve()}")


if __name__ == "__main__":
    main()

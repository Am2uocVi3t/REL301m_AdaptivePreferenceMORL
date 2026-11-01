#!/usr/bin/env python3
"""Recompute embedded historical validation evidence without checkpoints or rollouts."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.evaluation.course_validation import ValidationExpectation, validate_validation_artifact
from src.evaluation.protocol import load_protocol, protocol_hash
from src.utils.provenance import write_json


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reaudit(root: Path, aggregate_path: Path | None = None) -> dict[str, Any]:
    aggregate_path = aggregate_path or root / "research/evidence/course_primary_validation_v1.json"
    audit_path = root / "research/evidence/course_primary_execution_audit_v1.json"
    aggregate, audit = read_json(aggregate_path), read_json(audit_path)
    if aggregate["source_audit_sha256"] != digest(audit_path) or audit["passed"] is not True:
        raise ValueError("Recovered aggregate is not bound to the passed historical source audit")
    frozen = audit["frozen_inputs"]
    for key in ("study_config", "matrix_manifest", "qualification_gates"):
        reference = frozen[key]
        if digest(root / reference["path"]) != reference["sha256"]:
            raise ValueError(f"Frozen input hash mismatch: {key}")
    study = read_json(root / frozen["study_config"]["path"])
    expected_jobs = {
        f"{env['env_id']}__{arm}__seed{seed}"
        for env in study["environments"]
        for arm in ("uniform", "matched-random", "full")
        for seed in study["paired_seeds"]
    }
    if len(aggregate["runs"]) != len(expected_jobs) or {r["job_id"] for r in aggregate["runs"]} != expected_jobs:
        raise ValueError("Recovered primary job set is incomplete or duplicated")
    audited = {job["job_id"]: job for job in audit["jobs"]}
    rows, missing, checkpoint_count, episode_count, evaluation_steps = [], [], 0, 0, 0
    minecart_ore_positive_counts = np.zeros(2, dtype=np.int64)
    for run in aggregate["runs"]:
        job = audited[run["job_id"]]
        sources = {record["step"]: record for record in job["checkpoint_candidates"]}
        if len(run["candidates"]) != len(sources) or {c["checkpoint"]["step"] for c in run["candidates"]} != set(
            sources
        ):
            raise ValueError(f"Recovered checkpoint set mismatch: {run['job_id']}")
        protocol_path = next(e["protocol"] for e in study["environments"] if e["env_id"] == job["environment"])
        protocol, preferences = load_protocol(root / protocol_path, "validation")
        frozen_protocol = frozen["protocols"][protocol_path]
        if (
            protocol_hash(protocol) != frozen_protocol["canonical_sha256"]
            or digest(root / protocol_path) != frozen_protocol["file_sha256"]
        ):
            raise ValueError(f"Frozen protocol mismatch: {protocol_path}")
        for candidate in run["candidates"]:
            source = sources[candidate["checkpoint"]["step"]]
            expected = ValidationExpectation(
                study_id=study["id"],
                job_id=job["job_id"],
                environment=job["environment"],
                arm=job["arm"],
                training_seed=job["training_seed"],
                checkpoint_step=source["step"],
                checkpoint_path=source["path"],
                checkpoint_sha256=source["sha256"],
                protocol_path=protocol_path,
                protocol_sha256=protocol_hash(protocol),
                preference_sha256=hashlib.sha256(np.ascontiguousarray(preferences).tobytes()).hexdigest(),
                discount_factor=protocol["return_definition"]["gamma"],
                reward_scale=tuple(protocol["reward_scale"]),
                reference_point=tuple(protocol["reference_point"]),
                reward_dim=protocol["reward_dim"],
                preference_count=len(preferences),
                episodes_per_preference=study["budget"]["validation_episodes_per_preference"],
                evaluation_seed=20_000,
                training_interaction_budget=study["budget"]["training_interactions"],
                expected_counters=source["counters"],
            )
            validate_validation_artifact(candidate, expected)
            if candidate["training_log_metrics"] != source["training_log_metrics"]:
                raise ValueError("Recovered training-log metrics differ from the historical source audit")
            if not (root / source["path"]).is_file():
                missing.append(source["path"])
            checkpoint_count += 1
            episode_count += len(preferences) * expected.episodes_per_preference
            evaluation_steps += candidate["evaluation"]["evaluation_steps"]
            if job["environment"] == "minecart-v0":
                raw_returns = np.asarray(candidate["raw_episode_returns"])
                minecart_ore_positive_counts += (raw_returns[:, :, :2] > 0).sum(axis=(0, 1))
        final = max(run["candidates"], key=lambda candidate: candidate["checkpoint"]["step"])
        raw = np.asarray(final["raw_episode_returns"])
        rows.append(
            {
                "job_id": job["job_id"],
                "environment": job["environment"],
                "arm": job["arm"],
                "training_seed": job["training_seed"],
                "checkpoint_step": final["checkpoint"]["step"],
                "hypervolume": final["metrics"]["hypervolume"],
                "expected_utility": final["metrics"]["expected_utility"],
                "ore_positive_episodes": (
                    (raw[:, :, :2] > 0).sum(axis=(0, 1)).tolist() if job["environment"] == "minecart-v0" else None
                ),
            }
        )
    return {
        "schema_version": 1,
        "kind": "recovered_embedded_validation_reaudit",
        "aggregate_sha256": digest(aggregate_path),
        "source_audit_sha256": digest(audit_path),
        "numeric_and_metadata_validation": "passed",
        "runs": len(rows),
        "checkpoints": checkpoint_count,
        "episodes": episode_count,
        "historical_evaluation_steps": evaluation_steps,
        "minecart_ore_positive_counts_across_checkpoints": minecart_ore_positive_counts.tolist(),
        "raw_return_units": "undiscounted protocol-scaled vector returns",
        "missing_checkpoint_files": missing,
        "checkpoint_files_reverified": False,
        "new_environment_steps": 0,
        "final_test_accessed": False,
        "unlocks_final_test": False,
        "historical_study_status": aggregate["status"],
        "interpretation": "Descriptive validation evidence only; failed qualification and scientific gates unchanged.",
        "fixed_final_checkpoint_diagnostics": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="artifacts/recovery-validation-reaudit-20261101.json")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    result = reaudit(root)
    write_json(root / args.output, result)
    print(f"Verified {result['checkpoints']} embedded checkpoints / {result['episodes']} episodes; no rollouts")


if __name__ == "__main__":
    main()

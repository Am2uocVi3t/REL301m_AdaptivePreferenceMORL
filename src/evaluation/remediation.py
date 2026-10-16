from __future__ import annotations

import hashlib
import json
import subprocess
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from functools import partial
from pathlib import Path
from typing import Any

import numpy as np

from src.evaluation.course_validation import (
    CHECKPOINT_PATTERN,
    ValidationCandidate,
    ValidationExpectation,
    _load_checkpoint,
    _load_validation_scalars,
    _validate_checkpoint_metadata,
    evaluate_candidate,
    evaluate_or_reuse,
    select_checkpoint,
)
from src.evaluation.protocol import load_protocol, protocol_hash


class RemediationError(RuntimeError):
    """Raised when Minecart remediation evidence violates its frozen contract."""


CommandRunner = Callable[[list[str], Path], None]


def build_qualification_jobs(plan: Mapping[str, Any]) -> list[dict[str, Any]]:
    qualification = _mapping(plan.get("qualification"), "qualification")
    template = qualification.get("command_template")
    seeds = qualification.get("seeds")
    if not isinstance(template, list) or not all(isinstance(part, str) for part in template):
        raise RemediationError("Qualification command template is malformed")
    if template.count("<qualification-seed>") != 1:
        raise RemediationError("Qualification command template must contain one seed placeholder")
    if template[:2] != ["python", "scripts/train.py"]:
        raise RemediationError("Qualification command is not allowlisted")
    if "--split" in template or any(part.lower() == "test" for part in template):
        raise RemediationError("Qualification command attempts to access the test split")
    if not isinstance(seeds, list) or not seeds or not all(isinstance(seed, int) for seed in seeds):
        raise RemediationError("Qualification seeds are malformed")
    if len(set(seeds)) != len(seeds):
        raise RemediationError("Qualification seeds must be unique")

    environment = _mapping(plan.get("environment"), "environment")
    env_id = str(environment.get("env_id", ""))
    output_root = str(qualification.get("output_root", ""))
    _validate_relative_path(output_root, "qualification output root")
    jobs = []
    for seed in seeds:
        command = [str(seed) if part == "<qualification-seed>" else part for part in template]
        jobs.append(
            {
                "job_id": f"{env_id}__uniform-backbone__seed{seed}",
                "seed": seed,
                "environment": env_id,
                "command": command,
                "final_artifact": f"{output_root}/uniform-pcqn_{env_id}_seed{seed}/final.pt",
            }
        )
    return jobs


def load_qualification_plan(root: Path, plan_path: Path) -> tuple[dict[str, Any], str]:
    plan = _load_json(plan_path)
    if plan.get("schema_version") != 1 or plan.get("status") != "predeclared_not_executed":
        raise RemediationError("Unsupported or mutable remediation plan")
    if plan.get("execution_authorized") is not False:
        raise RemediationError("The frozen plan must not embed execution authorization")
    firewall = _mapping(plan.get("data_firewall"), "data firewall")
    if (
        firewall.get("evaluation_split") != "validation"
        or firewall.get("forbidden_split") != "test"
        or firewall.get("shift") != "nominal"
        or firewall.get("final_test_access_permitted") is not False
    ):
        raise RemediationError("Remediation data firewall is not validation-only")
    environment = _mapping(plan.get("environment"), "environment")
    protocol_path = _resolve_relative(root, str(environment.get("protocol", "")), "protocol")
    protocol = _load_json(protocol_path)
    if protocol_hash(protocol) != environment.get("protocol_canonical_sha256"):
        raise RemediationError("Remediation protocol canonical hash mismatch")
    diagnosis_path = _resolve_relative(root, str(plan.get("diagnosis_artifact", "")), "diagnosis artifact")
    diagnosis_hash = plan.get("diagnosis_sha256")
    if not isinstance(diagnosis_hash, str) or sha256_file(diagnosis_path) != diagnosis_hash:
        raise RemediationError("Remediation diagnosis artifact hash mismatch")
    build_qualification_jobs(plan)
    return plan, sha256_file(plan_path)


def select_qualification_jobs(jobs: Sequence[dict[str, Any]], seeds: set[int] | None) -> list[dict[str, Any]]:
    return [job for job in jobs if not seeds or job["seed"] in seeds]


def authorize_qualification(
    plan: Mapping[str, Any],
    jobs: Sequence[dict[str, Any]],
    *,
    execute: bool,
    acknowledgement: str | None,
    max_seeds: int | None,
    selectors_used: bool,
) -> bool:
    if not execute:
        return False
    plan_id = plan.get("id")
    if acknowledgement != plan_id:
        raise RemediationError(f"Execution requires exact plan acknowledgement: {plan_id}")
    if plan.get("execution_authorized") is not False:
        raise RemediationError("The frozen plan must not embed execution authorization")
    if not selectors_used:
        raise RemediationError("Execution requires an explicit seed selector")
    if not jobs:
        raise RemediationError("Qualification selection is empty")
    if max_seeds is None or max_seeds <= 0:
        raise RemediationError("Execution requires an explicit positive --max-seeds")
    if len(jobs) > max_seeds:
        raise RemediationError(f"Selected {len(jobs)} seeds, exceeding --max-seeds={max_seeds}")
    return True


def run_qualification_jobs(
    *,
    root: Path,
    plan: Mapping[str, Any],
    plan_sha256: str,
    jobs: Sequence[dict[str, Any]],
    status_path: Path,
    run_command: CommandRunner,
    retry_failed: bool,
    execution_git_commit: str,
    python_executable: str,
) -> dict[str, Any]:
    status = _load_or_initialize_status(
        status_path,
        plan_id=str(plan.get("id")),
        plan_sha256=plan_sha256,
        execution_git_commit=execution_git_commit,
        python_executable=python_executable,
    )
    records = _mapping(status.get("jobs"), "execution status jobs")
    for job in jobs:
        job_id = str(job["job_id"])
        record = records.setdefault(job_id, {"status": "planned", "attempts": 0})
        if record["status"] == "complete":
            _verify_completed_artifact(root, job, record)
            continue
        if record["status"] in {"failed", "running"} and not retry_failed:
            raise RemediationError(f"Job {job_id} is {record['status']}; use --retry-failed to retry")

        artifact_path = _resolve_artifact(root, str(job["final_artifact"]))
        if artifact_path.exists():
            raise RemediationError(f"Job {job_id} has an untracked final artifact: {artifact_path}")
        record.update(
            {
                "status": "running",
                "attempts": int(record.get("attempts", 0)) + 1,
                "started_at": _utc_now(),
                "command": job["command"],
                "final_artifact": job["final_artifact"],
            }
        )
        _write_json_atomic(status_path, status)
        try:
            run_command(list(job["command"]), root)
            if not artifact_path.is_file():
                raise RemediationError(f"Job {job_id} completed without final artifact: {artifact_path}")
            record.update(
                {
                    "status": "complete",
                    "completed_at": _utc_now(),
                    "artifact_sha256": sha256_file(artifact_path),
                }
            )
            record.pop("error", None)
            _write_json_atomic(status_path, status)
        except Exception as error:
            record.update({"status": "failed", "completed_at": _utc_now(), "error": str(error)})
            _write_json_atomic(status_path, status)
            if isinstance(error, RemediationError):
                raise
            raise RemediationError(f"Job {job_id} failed: {error}") from error
    return status


def repository_snapshot(root: Path) -> tuple[str, bool]:
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        dirty = bool(
            subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        )
    except (OSError, subprocess.CalledProcessError) as error:
        raise RemediationError(f"Cannot inspect Git state: {error}") from error
    if not commit:
        raise RemediationError("Cannot determine execution Git commit")
    return commit, dirty


def audit_qualification_sources(
    root: Path,
    *,
    plan_path: Path,
    plan: Mapping[str, Any],
    plan_sha256: str,
    status_path: Path,
) -> tuple[dict[str, Any], dict[int, list[ValidationCandidate]]]:
    status = _load_json(status_path)
    if (
        status.get("schema_version") != 1
        or status.get("kind") != "minecart_backbone_qualification_execution"
        or status.get("plan_id") != plan.get("id")
        or status.get("plan_sha256") != plan_sha256
    ):
        raise RemediationError("Qualification execution status does not match the frozen plan")
    execution_commit = status.get("execution_git_commit")
    if not isinstance(execution_commit, str) or not execution_commit:
        raise RemediationError("Qualification execution Git commit is missing")
    status_jobs = _mapping(status.get("jobs"), "execution status jobs")
    jobs = build_qualification_jobs(plan)
    if set(status_jobs) != {job["job_id"] for job in jobs}:
        raise RemediationError("Execution status does not contain exactly the predeclared seeds")

    qualification = _mapping(plan.get("qualification"), "qualification")
    environment = _mapping(plan.get("environment"), "environment")
    protocol_relative = str(environment["protocol"])
    protocol_path = _resolve_relative(root, protocol_relative, "protocol")
    protocol, preferences = load_protocol(protocol_path, "validation")
    canonical_protocol_hash = protocol_hash(protocol)
    if canonical_protocol_hash != environment.get("protocol_canonical_sha256"):
        raise RemediationError("Qualification protocol hash mismatch")

    audit_jobs = []
    candidates_by_seed: dict[int, list[ValidationCandidate]] = {}
    for job in jobs:
        record = _mapping(status_jobs.get(job["job_id"]), f"status for {job['job_id']}")
        job_audit, candidates = _audit_qualification_job(
            root,
            plan,
            job,
            record,
            protocol_relative,
            protocol,
            preferences,
            canonical_protocol_hash,
            execution_commit,
        )
        audit_jobs.append(job_audit)
        candidates_by_seed[int(job["seed"])] = candidates

    return (
        {
            "schema_version": 1,
            "kind": "minecart_backbone_qualification_source_audit",
            "plan": {
                "path": str(plan_path.relative_to(root)),
                "sha256": plan_sha256,
                "id": plan["id"],
            },
            "execution_status": {
                "path": str(status_path.relative_to(root)),
                "sha256": sha256_file(status_path),
            },
            "execution_git_commit": execution_commit,
            "data_firewall": plan["data_firewall"],
            "protocol": {"path": protocol_relative, "canonical_sha256": canonical_protocol_hash},
            "expected_seed_count": len(qualification["seeds"]),
            "checkpoint_count": sum(len(candidates) for candidates in candidates_by_seed.values()),
            "jobs": audit_jobs,
            "passed": True,
        },
        candidates_by_seed,
    )


def evaluate_qualification_candidates(
    root: Path,
    *,
    candidates_by_seed: Mapping[int, Sequence[ValidationCandidate]],
    evidence_root: Path,
    device: str,
) -> dict[int, list[tuple[dict[str, Any], str, str]]]:
    evaluated: dict[int, list[tuple[dict[str, Any], str, str]]] = {}
    for seed, candidates in candidates_by_seed.items():
        seed_evidence = []
        for candidate in candidates:
            expectation = candidate.expectation
            destination = evidence_root / f"seed{seed}" / f"checkpoint_step{expectation.checkpoint_step}.json"
            artifact, artifact_hash, _ = evaluate_or_reuse(
                destination,
                expectation,
                partial(
                    evaluate_candidate,
                    candidate,
                    root,
                    device,
                    verify_training_metrics=False,
                ),
            )
            seed_evidence.append((artifact, artifact_hash, str(destination.relative_to(root))))
        evaluated[seed] = seed_evidence
    return evaluated


def build_qualification_decision(
    root: Path,
    *,
    plan_path: Path,
    plan: Mapping[str, Any],
    plan_sha256: str,
    audit_path: Path,
    evaluated: Mapping[int, Sequence[tuple[Mapping[str, Any], str, str]]],
) -> dict[str, Any]:
    qualification = _mapping(plan.get("qualification"), "qualification")
    expected_seeds = qualification.get("seeds")
    if not isinstance(expected_seeds, list) or set(evaluated) != set(expected_seeds):
        raise RemediationError("Qualification evidence does not contain exactly the predeclared seeds")
    expected_steps = qualification.get("evaluation", {}).get("checkpoint_steps")
    if not isinstance(expected_steps, list) or not expected_steps:
        raise RemediationError("Qualification checkpoint steps are malformed")

    seed_decisions = []
    evaluation_steps = 0
    for seed in expected_seeds:
        records = evaluated[seed]
        if len(records) != len(expected_steps):
            raise RemediationError(f"Seed {seed} has an incomplete checkpoint evaluation set")
        candidates = []
        for artifact, artifact_hash, relative_path in records:
            checkpoint = _mapping(artifact.get("checkpoint"), "validation checkpoint")
            metrics = _mapping(artifact.get("metrics"), "validation metrics")
            evaluation = _mapping(artifact.get("evaluation"), "validation evaluation")
            evaluation_steps += int(evaluation["evaluation_steps"])
            candidates.append(
                {
                    "step": checkpoint["step"],
                    "hypervolume": metrics["hypervolume"],
                    "expected_utility": metrics["expected_utility"],
                    "discounted_episode_returns": artifact["discounted_episode_returns"],
                    "artifact": {"path": relative_path, "sha256": artifact_hash},
                }
            )
        if sorted(candidate["step"] for candidate in candidates) != expected_steps:
            raise RemediationError(f"Seed {seed} checkpoint steps do not match the frozen plan")
        seed_decisions.append(qualify_seed(seed, candidates, qualification["pass_rule"]))

    all_passed = all(decision["passed"] for decision in seed_decisions)
    return {
        "schema_version": 1,
        "kind": "minecart_pcqn_backbone_qualification",
        "status": "passed" if all_passed else "failed",
        "passed": all_passed,
        "evidence_role": qualification["evidence_role"],
        "plan": {
            "path": str(plan_path.relative_to(root)),
            "sha256": plan_sha256,
            "id": plan["id"],
        },
        "source_audit": {
            "path": str(audit_path.relative_to(root)),
            "sha256": sha256_file(audit_path),
        },
        "data_firewall": plan["data_firewall"],
        "pass_rule": qualification["pass_rule"],
        "seed_decisions": seed_decisions,
        "evaluation_summary": {
            "checkpoint_evaluations": len(expected_steps) * len(expected_seeds),
            "episodes": len(expected_steps)
            * len(expected_seeds)
            * int(qualification["evaluation"]["episode_count_per_checkpoint"]),
            "environment_steps": evaluation_steps,
        },
        "unlocks_new_course_study_design": all_passed,
        "unlocks_matrix_v1": False,
        "unlocks_final_test": False,
        "continuation": (
            "Freeze a new course study ID and separately qualify comparator fairness."
            if all_passed
            else qualification["failure_rule"]
        ),
    }


def _audit_qualification_job(
    root: Path,
    plan: Mapping[str, Any],
    job: Mapping[str, Any],
    status_record: Mapping[str, Any],
    protocol_path: str,
    protocol: dict[str, Any],
    preferences: np.ndarray,
    canonical_protocol_hash: str,
    execution_commit: str,
) -> tuple[dict[str, Any], list[ValidationCandidate]]:
    job_id = str(job["job_id"])
    if status_record.get("status") != "complete" or int(status_record.get("attempts", 0)) < 1:
        raise RemediationError(f"Qualification job is not complete: {job_id}")
    if status_record.get("command") != job.get("command"):
        raise RemediationError(f"Qualification command drift: {job_id}")
    if status_record.get("final_artifact") != job.get("final_artifact"):
        raise RemediationError(f"Qualification final artifact path drift: {job_id}")
    final_path = _resolve_artifact(root, str(job["final_artifact"]))
    final_hash = sha256_file(final_path)
    if status_record.get("artifact_sha256") != final_hash:
        raise RemediationError(f"Qualification final checkpoint hash mismatch: {job_id}")

    run_dir = final_path.parent
    run_manifest_path = run_dir / "run_manifest.json"
    run_manifest = _load_json(run_manifest_path)
    config = _mapping(run_manifest.get("config"), "run manifest config")
    if run_manifest.get("config_sha256") != _canonical_hash(config):
        raise RemediationError(f"Run manifest config hash mismatch: {job_id}")
    if run_manifest.get("git_commit") != execution_commit or run_manifest.get("git_dirty") is not False:
        raise RemediationError(f"Qualification run was not produced from the clean execution commit: {job_id}")
    _validate_qualification_run_config(config, plan, job, protocol)

    qualification = _mapping(plan.get("qualification"), "qualification")
    evaluation = _mapping(qualification.get("evaluation"), "qualification evaluation")
    expected_steps = evaluation.get("checkpoint_steps")
    if not isinstance(expected_steps, list) or not all(isinstance(step, int) for step in expected_steps):
        raise RemediationError("Qualification checkpoint steps are malformed")
    checkpoint_by_step: dict[int, Path] = {}
    for path in run_dir.glob("checkpoint_step*.pt"):
        match = CHECKPOINT_PATTERN.fullmatch(path.name)
        if match is None:
            raise RemediationError(f"Malformed qualification checkpoint filename: {path}")
        checkpoint_by_step[int(match.group("step"))] = path
    if sorted(checkpoint_by_step) != expected_steps:
        raise RemediationError(f"Missing or unexpected qualification checkpoints: {job_id}")

    log_files = sorted((run_dir / "logs").glob("**/events.out.tfevents*"))
    scalar_curves = _load_validation_scalars(log_files)
    for metric, curve in scalar_curves.items():
        if [record["step"] for record in curve] != expected_steps:
            raise RemediationError(f"Qualification validation log {metric} steps mismatch: {job_id}")
    log_by_step = {
        metric: {record["step"]: record["value"] for record in curve} for metric, curve in scalar_curves.items()
    }

    candidates = []
    candidate_records = []
    previous_counters: dict[str, int] | None = None
    for step in expected_steps:
        path = checkpoint_by_step[step]
        checkpoint = _load_checkpoint(path, "cpu")
        try:
            counters = _validate_checkpoint_metadata(
                checkpoint,
                step=step,
                config=config,
                protocol=protocol,
                protocol_path=protocol_path,
                canonical_protocol_hash=canonical_protocol_hash,
                job_id=job_id,
            )
        except Exception as error:
            raise RemediationError(str(error)) from error
        if previous_counters is not None and any(counters[key] < previous_counters[key] for key in counters):
            raise RemediationError(f"Qualification checkpoint counters are not monotone: {job_id}")
        previous_counters = counters
        relative_path = str(path.relative_to(root))
        checkpoint_hash = sha256_file(path)
        expectation = ValidationExpectation(
            study_id=str(plan["id"]),
            job_id=job_id,
            environment=str(job["environment"]),
            arm="uniform-backbone-qualification",
            training_seed=int(job["seed"]),
            checkpoint_step=step,
            checkpoint_path=relative_path,
            checkpoint_sha256=checkpoint_hash,
            protocol_path=protocol_path,
            protocol_sha256=canonical_protocol_hash,
            preference_sha256=_array_sha256(preferences.astype(np.float32)),
            discount_factor=float(protocol["return_definition"]["gamma"]),
            reward_scale=tuple(float(value) for value in protocol["reward_scale"]),
            reference_point=tuple(float(value) for value in protocol["reference_point"]),
            reward_dim=int(protocol["reward_dim"]),
            preference_count=len(preferences),
            episodes_per_preference=int(evaluation["episodes_per_preference"]),
            evaluation_seed=int(evaluation["seed_base"]),
            training_interaction_budget=int(qualification["training"]["total_timesteps"]),
            expected_counters=counters,
        )
        training_metrics = {
            "hypervolume": log_by_step["hypervolume"][step],
            "expected_utility": log_by_step["expected_utility"][step],
        }
        candidates.append(
            ValidationCandidate(
                expectation=expectation,
                protocol=protocol,
                preferences=preferences,
                training_log_metrics=training_metrics,
            )
        )
        candidate_records.append(
            {
                "step": step,
                "path": relative_path,
                "sha256": checkpoint_hash,
                "counters": counters,
                "training_log_metrics": training_metrics,
            }
        )

    final_checkpoint = _load_checkpoint(final_path, "cpu")
    try:
        final_counters = _validate_checkpoint_metadata(
            final_checkpoint,
            step=int(qualification["training"]["total_timesteps"]),
            config=config,
            protocol=protocol,
            protocol_path=protocol_path,
            canonical_protocol_hash=canonical_protocol_hash,
            job_id=job_id,
        )
    except Exception as error:
        raise RemediationError(str(error)) from error
    if final_counters != candidate_records[-1]["counters"]:
        raise RemediationError(f"Final and last qualification checkpoint counters differ: {job_id}")
    expected_updates = int(qualification["training"]["expected_gradient_updates"])
    if final_counters["gradient_updates"] != expected_updates:
        raise RemediationError(f"Final qualification update budget mismatch: {job_id}")

    return (
        {
            "job_id": job_id,
            "training_seed": job["seed"],
            "attempts": status_record["attempts"],
            "run_manifest": _file_reference(root, run_manifest_path),
            "training_git_commit": execution_commit,
            "training_git_dirty": False,
            "validation_log_files": [_file_reference(root, path) for path in log_files],
            "final_checkpoint": {
                "path": str(final_path.relative_to(root)),
                "sha256": final_hash,
                "counters": final_counters,
            },
            "checkpoint_candidates": candidate_records,
        },
        candidates,
    )


def _validate_qualification_run_config(
    config: Mapping[str, Any],
    plan: Mapping[str, Any],
    job: Mapping[str, Any],
    protocol: Mapping[str, Any],
) -> None:
    qualification = _mapping(plan.get("qualification"), "qualification")
    training = _mapping(qualification.get("training"), "qualification training")
    evaluation = _mapping(qualification.get("evaluation"), "qualification evaluation")
    expected = {
        "env": plan["environment"]["env_id"],
        "algo": qualification["method"],
        "allocation_target": "rollout_and_update",
        "seed": job["seed"],
        "total_timesteps": training["total_timesteps"],
        "learning_starts": training["learning_starts"],
        "train_freq": training["train_frequency"],
        "batch_size": training["batch_size"],
        "buffer_capacity": training["buffer_capacity"],
        "bootstrap_probability": training["bootstrap_probability"],
        "num_heads": training["num_heads"],
        "lr": training["learning_rate"],
        "gamma": training["gamma"],
        "target_update_freq": training["target_update_frequency"],
        "curriculum_update_freq": training["curriculum_update_frequency"],
        "curriculum_eval_episodes": training["curriculum_episodes_per_preference"],
        "pool_size": int(protocol["training_preference_pool"]["count"]),
        "eps_start": training["epsilon_start"],
        "eps_end": training["epsilon_end"],
        "eps_fraction": training["epsilon_fraction"],
        "eval_freq": evaluation["checkpoint_steps"][0],
        "eval_episodes": evaluation["episodes_per_preference"],
        "eval_seed": evaluation["seed_base"],
        "save_freq": evaluation["checkpoint_steps"][0],
        "device": "cpu",
    }
    for key, expected_value in expected.items():
        actual = config.get(key)
        if isinstance(expected_value, (int, float)) and not isinstance(expected_value, bool):
            if not isinstance(actual, (int, float)) or not np.isclose(float(actual), float(expected_value)):
                raise RemediationError(f"Run config {key} mismatch for {job['job_id']}")
        elif actual != expected_value:
            raise RemediationError(f"Run config {key} mismatch for {job['job_id']}")
    if config.get("protocol") != protocol:
        raise RemediationError(f"Run manifest embedded protocol mismatch for {job['job_id']}")


def qualify_seed(
    seed: int,
    candidates: Sequence[Mapping[str, Any]],
    pass_rule: Mapping[str, Any],
) -> dict[str, Any]:
    selected = select_checkpoint(candidates)
    returns = np.asarray(selected.get("discounted_episode_returns"), dtype=np.float32)
    if returns.ndim != 3 or not np.all(np.isfinite(returns)):
        raise RemediationError(f"Seed {seed} selected returns are malformed or non-finite")
    objective_indices = pass_rule.get("ore_objective_indices")
    if not isinstance(objective_indices, list) or not objective_indices:
        raise RemediationError("Pass rule ore objectives are malformed")
    minimum_positive = _positive_int(
        pass_rule.get("minimum_positive_episodes_per_objective"),
        "minimum positive episodes",
    )
    minimum_distinct = _positive_int(
        pass_rule.get("minimum_distinct_positive_values_per_objective"),
        "minimum distinct positive values",
    )

    objective_decisions: dict[str, dict[str, Any]] = {}
    passed = True
    for objective in objective_indices:
        if not isinstance(objective, int) or objective < 0 or objective >= returns.shape[2]:
            raise RemediationError(f"Pass rule has invalid ore objective index: {objective!r}")
        values = returns[:, :, objective].reshape(-1)
        positive = values[values > 0.0]
        count = int(positive.size)
        distinct = int(np.unique(positive).size)
        objective_passed = count >= minimum_positive and distinct >= minimum_distinct
        passed = passed and objective_passed
        objective_decisions[str(objective)] = {
            "positive_episode_count": count,
            "positive_episode_fraction": count / int(values.size),
            "distinct_positive_values": distinct,
            "passed": objective_passed,
        }

    artifact = _mapping(selected.get("artifact"), "selected validation artifact")
    return {
        "training_seed": seed,
        "passed": passed,
        "selected_checkpoint": {
            "step": int(selected["step"]),
            "hypervolume": float(selected["hypervolume"]),
            "expected_utility": float(selected["expected_utility"]),
            "validation_artifact": artifact,
        },
        "ore_objectives": objective_decisions,
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_or_initialize_status(
    path: Path,
    *,
    plan_id: str,
    plan_sha256: str,
    execution_git_commit: str,
    python_executable: str,
) -> dict[str, Any]:
    if path.exists():
        status = _load_json(path)
        if status.get("plan_sha256") != plan_sha256 or status.get("plan_id") != plan_id:
            raise RemediationError("Execution status belongs to a different remediation plan")
        if status.get("execution_git_commit") != execution_git_commit:
            raise RemediationError("Execution status belongs to a different Git commit")
        return status
    status = {
        "schema_version": 1,
        "kind": "minecart_backbone_qualification_execution",
        "plan_id": plan_id,
        "plan_sha256": plan_sha256,
        "execution_git_commit": execution_git_commit,
        "python_executable": python_executable,
        "created_at": _utc_now(),
        "jobs": {},
    }
    _write_json_atomic(path, status)
    return status


def _verify_completed_artifact(root: Path, job: Mapping[str, Any], record: Mapping[str, Any]) -> None:
    artifact_path = _resolve_artifact(root, str(job["final_artifact"]))
    expected_hash = record.get("artifact_sha256")
    if not artifact_path.is_file() or not isinstance(expected_hash, str) or sha256_file(artifact_path) != expected_hash:
        raise RemediationError(f"Job {job['job_id']} completed artifact hash mismatch")


def _resolve_artifact(root: Path, relative_path: str) -> Path:
    _validate_relative_path(relative_path, "artifact")
    resolved = (root / relative_path).resolve()
    if root.resolve() not in resolved.parents:
        raise RemediationError("Artifact path escapes the repository root")
    return resolved


def _resolve_relative(root: Path, relative_path: str, label: str) -> Path:
    _validate_relative_path(relative_path, label)
    resolved = (root / relative_path).resolve()
    if root.resolve() not in resolved.parents:
        raise RemediationError(f"{label.capitalize()} path escapes the repository root")
    if not resolved.is_file():
        raise RemediationError(f"Missing {label}: {resolved}")
    return resolved


def _validate_relative_path(value: str, label: str) -> None:
    path = Path(value)
    if not value or path.is_absolute() or ".." in path.parts:
        raise RemediationError(f"Invalid relative {label} path: {value!r}")


def _positive_int(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise RemediationError(f"{label} must be a positive integer")
    return value


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RemediationError(f"{label} must be an object")
    return value


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RemediationError(f"Cannot load JSON file {path}: {error}") from error
    return _mapping(value, f"JSON document {path}")


def _write_json_atomic(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def write_json_atomic(path: Path, payload: Mapping[str, Any]) -> None:
    _write_json_atomic(path, payload)


def _canonical_hash(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _array_sha256(value: np.ndarray) -> str:
    contiguous = np.ascontiguousarray(value)
    return hashlib.sha256(contiguous.tobytes()).hexdigest()


def _file_reference(root: Path, path: Path) -> dict[str, str]:
    return {"path": str(path.relative_to(root)), "sha256": sha256_file(path)}


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()

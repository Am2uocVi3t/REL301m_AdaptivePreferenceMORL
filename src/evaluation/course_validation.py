from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch

from src.envs.wrapper import make_mo_env
from src.evaluation.course_executor import (
    load_verified_execution_inputs,
    select_jobs,
    verify_manifest_matches_study,
)
from src.evaluation.course_matrix import load_course_study
from src.evaluation.metrics import (
    compute_expected_utility,
    compute_hypervolume,
    compute_per_objective_controllability,
    compute_sparsity,
    pareto_prune,
)
from src.evaluation.protocol import (
    load_protocol,
    protocol_hash,
    resolve_reference_point,
    resolve_reward_scale,
)
from src.evaluation.rollout import evaluate_preferences
from src.models.q_network import VectorQNetwork

PRIMARY_ARMS = frozenset({"uniform", "matched-random", "full"})
CHECKPOINT_PATTERN = re.compile(r"checkpoint_step(?P<step>[1-9][0-9]*)[.]pt$")


class CourseValidationError(RuntimeError):
    """Raised when course validation evidence violates a frozen contract."""


@dataclass(frozen=True)
class ValidationExpectation:
    study_id: str
    job_id: str
    environment: str
    arm: str
    training_seed: int
    checkpoint_step: int
    checkpoint_path: str
    checkpoint_sha256: str
    protocol_path: str
    protocol_sha256: str
    preference_sha256: str
    discount_factor: float
    reward_scale: tuple[float, ...]
    reference_point: tuple[float, ...]
    reward_dim: int
    preference_count: int
    episodes_per_preference: int
    evaluation_seed: int
    training_interaction_budget: int
    expected_counters: dict[str, int]


@dataclass(frozen=True)
class ValidationCandidate:
    expectation: ValidationExpectation
    protocol: dict[str, Any]
    preferences: np.ndarray
    training_log_metrics: dict[str, float]


def select_checkpoint(candidates: Sequence[Mapping[str, Any]]) -> Mapping[str, Any]:
    """Apply the frozen HV, expected-utility, then earlier-step selection rule."""
    if not candidates:
        raise CourseValidationError("Checkpoint selection requires at least one candidate")
    for candidate in candidates:
        for key in ("step", "hypervolume", "expected_utility"):
            value = candidate.get(key)
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)):
                raise CourseValidationError(f"Checkpoint candidate has invalid {key}: {value!r}")
    return max(
        candidates,
        key=lambda candidate: (
            float(candidate["hypervolume"]),
            float(candidate["expected_utility"]),
            -int(candidate["step"]),
        ),
    )


def validate_validation_artifact(
    artifact: Mapping[str, Any],
    expectation: ValidationExpectation,
    *,
    require_non_degenerate: bool = False,
) -> None:
    if artifact.get("schema_version") != 1 or artifact.get("kind") != "course_validation_checkpoint_evidence":
        raise CourseValidationError("Unsupported validation evidence schema")
    expected_identity = {
        "study_id": expectation.study_id,
        "job_id": expectation.job_id,
        "environment": expectation.environment,
        "arm": expectation.arm,
        "training_seed": expectation.training_seed,
    }
    for key, expected in expected_identity.items():
        if artifact.get(key) != expected:
            raise CourseValidationError(f"Validation evidence {key} mismatch")

    checkpoint = _mapping(artifact.get("checkpoint"), "checkpoint")
    if checkpoint.get("path") != expectation.checkpoint_path or checkpoint.get("step") != expectation.checkpoint_step:
        raise CourseValidationError("Validation evidence checkpoint identity mismatch")
    if checkpoint.get("sha256") != expectation.checkpoint_sha256:
        raise CourseValidationError("Validation evidence checkpoint hash mismatch")

    protocol = _mapping(artifact.get("protocol"), "protocol")
    if protocol.get("path") != expectation.protocol_path or protocol.get("sha256") != expectation.protocol_sha256:
        raise CourseValidationError("Validation evidence protocol hash or path mismatch")
    return_definition = _mapping(protocol.get("return_definition"), "protocol return definition")
    if return_definition.get("type") != "discounted":
        raise CourseValidationError("Validation evidence must use discounted returns")
    gamma = _finite_float(return_definition.get("gamma"), "discount factor")
    if not 0.0 < gamma <= 1.0 or not np.isclose(gamma, expectation.discount_factor):
        raise CourseValidationError("Validation evidence discount factor mismatch")
    reward_scale = _finite_array(protocol.get("reward_scale"), "reward scale", (expectation.reward_dim,))
    if np.any(reward_scale <= 0.0) or not np.array_equal(
        reward_scale.astype(np.float32), np.asarray(expectation.reward_scale, dtype=np.float32)
    ):
        raise CourseValidationError("Validation evidence reward scale mismatch")
    reference_point = _finite_array(protocol.get("reference_point"), "reference point", (expectation.reward_dim,))
    if not np.array_equal(
        reference_point.astype(np.float32), np.asarray(expectation.reference_point, dtype=np.float32)
    ):
        raise CourseValidationError("Validation evidence reference point mismatch")

    evaluation = _mapping(artifact.get("evaluation"), "evaluation")
    if evaluation.get("split") != "validation":
        raise CourseValidationError("Course evidence must use the validation split")
    if evaluation.get("shift") != "nominal":
        raise CourseValidationError("Course checkpoint locking requires the nominal shift")
    if evaluation.get("seed") != expectation.evaluation_seed:
        raise CourseValidationError("Validation evaluation seed mismatch")
    if evaluation.get("episodes_per_preference") != expectation.episodes_per_preference:
        raise CourseValidationError("Validation episode budget mismatch")

    budget = _mapping(artifact.get("budget"), "budget")
    if budget.get("training_interaction_budget") != expectation.training_interaction_budget:
        raise CourseValidationError("Validation evidence training budget mismatch")
    if expectation.checkpoint_step > expectation.training_interaction_budget:
        raise CourseValidationError("Checkpoint exceeds the frozen training budget")
    counters = _mapping(budget.get("checkpoint_counters"), "checkpoint counters")
    if counters != expectation.expected_counters:
        raise CourseValidationError("Validation evidence checkpoint counters mismatch")

    preferences = _validate_preference_records(artifact.get("preferences"), expectation)
    if _array_sha256(preferences.astype(np.float32)) != expectation.preference_sha256:
        raise CourseValidationError("Validation evidence preference matrix hash mismatch")
    expected_shape = (
        expectation.preference_count,
        expectation.episodes_per_preference,
        expectation.reward_dim,
    )
    discounted = _finite_array(artifact.get("discounted_episode_returns"), "discounted returns", expected_shape)
    raw = _finite_array(artifact.get("raw_episode_returns"), "raw returns", expected_shape)
    lengths = np.asarray(artifact.get("episode_lengths"))
    if lengths.shape != expected_shape[:2] or not np.issubdtype(lengths.dtype, np.integer) or np.any(lengths <= 0):
        raise CourseValidationError("Validation evidence episode lengths are malformed")
    if evaluation.get("evaluation_steps") != int(lengths.sum()):
        raise CourseValidationError("Validation evidence evaluation step count mismatch")

    metrics = _mapping(artifact.get("metrics"), "metrics")
    hypervolume = _finite_float(metrics.get("hypervolume"), "hypervolume")
    expected_utility = _finite_float(metrics.get("expected_utility"), "expected utility")
    mean_returns = discounted.mean(axis=1)
    recomputed_utility = compute_expected_utility(mean_returns, preferences)
    if not np.isclose(expected_utility, recomputed_utility, rtol=1e-7, atol=1e-8):
        raise CourseValidationError("Validation evidence expected utility does not match return tensors")
    if hypervolume < 0.0:
        raise CourseValidationError("Validation evidence hypervolume cannot be negative")
    recomputed_hypervolume = compute_hypervolume(pareto_prune(mean_returns), reference_point)
    if not np.isclose(hypervolume, recomputed_hypervolume, rtol=1e-7, atol=1e-8):
        raise CourseValidationError("Validation evidence hypervolume does not match return tensors")

    diagnostics = _mapping(artifact.get("diagnostics"), "diagnostics")
    if diagnostics.get("missing_values") != 0 or diagnostics.get("non_finite_values") != 0:
        raise CourseValidationError("Validation evidence reports missing or non-finite values")
    actual_degenerate = _degenerate_objectives(discounted)
    if diagnostics.get("degenerate_objectives") != actual_degenerate:
        raise CourseValidationError("Validation evidence degeneracy diagnostics mismatch")
    if require_non_degenerate and actual_degenerate:
        raise CourseValidationError(f"Selected checkpoint has degenerate objectives: {actual_degenerate}")
    if raw.shape != discounted.shape:
        raise CourseValidationError("Raw and discounted return tensors must have the same shape")


def evaluate_or_reuse(
    destination: Path,
    expectation: ValidationExpectation,
    evaluator: Callable[[], dict[str, Any]],
) -> tuple[dict[str, Any], str, bool]:
    """Return a valid deterministic artifact, reusing a completed one when possible."""
    if destination.exists():
        artifact = _load_json(destination)
        validate_validation_artifact(artifact, expectation)
        return artifact, sha256_file(destination), True

    artifact = evaluator()
    validate_validation_artifact(artifact, expectation)
    _write_json_atomic(destination, artifact)
    reloaded = _load_json(destination)
    validate_validation_artifact(reloaded, expectation)
    return reloaded, sha256_file(destination), False


def audit_primary_sources(
    root: Path,
    *,
    study_path: Path,
    manifest_path: Path,
    gates_path: Path,
    execution_status_path: Path,
) -> tuple[dict[str, Any], list[ValidationCandidate]]:
    """Verify frozen inputs and all source files before evaluating checkpoints."""
    root = root.resolve()
    study = load_course_study(study_path)
    manifest, gates = load_verified_execution_inputs(root, manifest_path, gates_path)
    verify_manifest_matches_study(manifest, study, root)
    status = _load_json(execution_status_path)
    _validate_execution_status(status, manifest, gates)

    primary_jobs = select_jobs(manifest, arms=set(PRIMARY_ARMS), families={"pcqn"})
    expected_job_count = len(study["environments"]) * len(PRIMARY_ARMS) * len(study["paired_seeds"])
    if len(primary_jobs) != expected_job_count or expected_job_count != 30:
        raise CourseValidationError(f"Expected exactly 30 primary PCQN jobs, found {len(primary_jobs)}")
    if set(status["jobs"]) != {str(job["job_id"]) for job in primary_jobs}:
        raise CourseValidationError("Atomic execution status does not contain exactly the primary 30-job block")

    study_by_environment = {item["env_id"]: item for item in study["environments"]}
    arm_by_id = {item["id"]: item for item in study["pcqn_arms"]}
    protocol_cache: dict[str, tuple[dict[str, Any], np.ndarray, str]] = {}
    protocol_audit: dict[str, Any] = {}
    for environment in study["environments"]:
        relative_path = str(environment["protocol"])
        protocol, preferences = load_protocol(root / relative_path, "validation")
        canonical_hash = protocol_hash(protocol)
        if manifest["protocol_sha256"].get(relative_path) != canonical_hash:
            raise CourseValidationError(f"Frozen manifest protocol hash mismatch: {relative_path}")
        if protocol.get("env_id") != environment["env_id"]:
            raise CourseValidationError(f"Protocol environment mismatch: {relative_path}")
        protocol_cache[relative_path] = (protocol, preferences, canonical_hash)
        protocol_audit[relative_path] = {
            "file_sha256": sha256_file(root / relative_path),
            "canonical_sha256": canonical_hash,
            "validation_preference_count": len(preferences),
            "reward_dim": int(protocol["reward_dim"]),
        }

    jobs_audit: list[dict[str, Any]] = []
    candidates: list[ValidationCandidate] = []
    save_frequencies: set[int] = set()
    for job in sorted(primary_jobs, key=lambda item: str(item["job_id"])):
        environment = str(job["environment"])
        arm = str(job["arm"])
        environment_spec = study_by_environment[environment]
        arm_spec = arm_by_id[arm]
        protocol_path = str(environment_spec["protocol"])
        protocol, preferences, canonical_protocol_hash = protocol_cache[protocol_path]
        job_audit, job_candidates, save_frequency = _audit_job(
            root,
            study,
            job,
            status["jobs"][job["job_id"]],
            arm_spec,
            protocol_path,
            protocol,
            preferences,
            canonical_protocol_hash,
        )
        jobs_audit.append(job_audit)
        candidates.extend(job_candidates)
        save_frequencies.add(save_frequency)

    if len(save_frequencies) != 1:
        raise CourseValidationError(
            f"Primary runs used inconsistent checkpoint frequencies: {sorted(save_frequencies)}"
        )
    expected_candidate_count = expected_job_count * (study["budget"]["training_interactions"] // save_frequencies.pop())
    if len(candidates) != expected_candidate_count or expected_candidate_count != 300:
        raise CourseValidationError(f"Expected exactly 300 checkpoint candidates, found {len(candidates)}")

    audit = {
        "schema_version": 1,
        "kind": "course_primary_execution_audit",
        "study_id": study["id"],
        "scope": {"arms": sorted(PRIMARY_ARMS), "job_count": len(primary_jobs), "checkpoint_count": len(candidates)},
        "passed": True,
        "final_test_accessed": False,
        "shifted_environment_accessed": False,
        "frozen_inputs": {
            "study_config": _file_reference(root, study_path),
            "study_config_canonical_sha256": manifest["study_config_sha256"],
            "matrix_manifest": _file_reference(root, manifest_path),
            "qualification_gates": _file_reference(root, gates_path),
            "execution_status": _file_reference(root, execution_status_path),
            "protocols": protocol_audit,
        },
        "jobs": jobs_audit,
        "diagnostics": {
            "missing_jobs": [],
            "missing_final_checkpoints": [],
            "missing_candidate_checkpoints": [],
            "malformed_run_manifests": [],
            "hash_mismatches": [],
            "budget_mismatches": [],
            "validation_log_mismatches": [],
            "dirty_training_worktrees": [job["job_id"] for job in jobs_audit if job["training_git_dirty"] is True],
        },
    }
    return audit, candidates


def evaluate_candidate(
    candidate: ValidationCandidate,
    root: Path,
    device: str = "cpu",
    *,
    verify_training_metrics: bool = True,
) -> dict[str, Any]:
    expectation = candidate.expectation
    checkpoint_path = root / expectation.checkpoint_path
    if sha256_file(checkpoint_path) != expectation.checkpoint_sha256:
        raise CourseValidationError(f"Checkpoint changed after source audit: {expectation.checkpoint_path}")
    checkpoint = _load_checkpoint(checkpoint_path, device)
    protocol = candidate.protocol
    return_definition = _mapping(protocol.get("return_definition"), "protocol return definition")
    gamma = _finite_float(return_definition.get("gamma"), "protocol gamma")
    reward_scale = resolve_reward_scale(protocol)
    env = make_mo_env(
        expectation.environment,
        seed=expectation.evaluation_seed,
        reward_scale=reward_scale,
    )
    try:
        observation_shape = env.observation_space.shape
        action_count = getattr(env.action_space, "n", None)
        if observation_shape is None or len(observation_shape) != 1 or action_count is None:
            raise CourseValidationError("Validation requires flat observations and a discrete action space")
        network = _load_network(
            checkpoint,
            state_dim=int(observation_shape[0]),
            action_dim=int(action_count),
            reward_dim=expectation.reward_dim,
            device=device,
        )
        rollout = evaluate_preferences(
            env,
            network,
            candidate.preferences,
            episodes_per_preference=expectation.episodes_per_preference,
            device=device,
            seed=expectation.evaluation_seed,
            discount_factor=gamma,
        )
    finally:
        env.close()

    discounted = np.asarray(rollout["episode_returns"], dtype=np.float32)
    raw = np.asarray(rollout["raw_episode_returns"], dtype=np.float32)
    mean_returns = discounted.mean(axis=1)
    frontier = pareto_prune(mean_returns)
    reference_point = resolve_reference_point(protocol)
    if reference_point is None:
        raise CourseValidationError("Frozen course protocol is missing a hypervolume reference point")
    metrics: dict[str, Any] = {
        "hypervolume": compute_hypervolume(frontier, reference_point),
        "expected_utility": compute_expected_utility(mean_returns, candidate.preferences),
        "frontier_size": len(frontier),
        "sparsity": compute_sparsity(frontier),
        "controllability": compute_per_objective_controllability(mean_returns, candidate.preferences),
    }
    metric_deltas = {
        metric: float(metrics[metric]) - candidate.training_log_metrics[metric]
        for metric in ("hypervolume", "expected_utility")
    }
    if verify_training_metrics:
        for metric, delta in metric_deltas.items():
            if not np.isclose(delta, 0.0, rtol=1e-5, atol=1e-6):
                raise CourseValidationError(
                    f"Reproduced {metric} disagrees with training validation log for {expectation.job_id} "
                    f"step {expectation.checkpoint_step}: {metrics[metric]} != "
                    f"{candidate.training_log_metrics[metric]}"
                )

    return {
        "schema_version": 1,
        "kind": "course_validation_checkpoint_evidence",
        "study_id": expectation.study_id,
        "job_id": expectation.job_id,
        "environment": expectation.environment,
        "arm": expectation.arm,
        "training_seed": expectation.training_seed,
        "checkpoint": {
            "path": expectation.checkpoint_path,
            "step": expectation.checkpoint_step,
            "sha256": expectation.checkpoint_sha256,
        },
        "protocol": {
            "path": expectation.protocol_path,
            "sha256": expectation.protocol_sha256,
            "return_definition": protocol["return_definition"],
            "reward_scale": protocol["reward_scale"],
            "reference_point": protocol["reference_point"],
        },
        "evaluation": {
            "split": "validation",
            "shift": "nominal",
            "seed": expectation.evaluation_seed,
            "episodes_per_preference": expectation.episodes_per_preference,
            "evaluation_steps": int(rollout["evaluation_steps"]),
        },
        "budget": {
            "training_interaction_budget": expectation.training_interaction_budget,
            "checkpoint_counters": expectation.expected_counters,
        },
        "preferences": [
            {"id": f"validation-{index:03d}", "weights": value.tolist()}
            for index, value in enumerate(candidate.preferences)
        ],
        "discounted_episode_returns": discounted.tolist(),
        "raw_episode_returns": raw.tolist(),
        "episode_lengths": np.asarray(rollout["episode_lengths"], dtype=np.int32).tolist(),
        "metrics": metrics,
        "training_log_metrics": candidate.training_log_metrics,
        "training_log_metric_deltas": metric_deltas,
        "diagnostics": {
            "missing_values": 0,
            "non_finite_values": int(np.size(discounted) - np.count_nonzero(np.isfinite(discounted)))
            + int(np.size(raw) - np.count_nonzero(np.isfinite(raw))),
            "degenerate_objectives": _degenerate_objectives(discounted),
        },
    }


def aggregate_and_lock(
    candidates: Sequence[ValidationCandidate],
    evaluated: Sequence[tuple[dict[str, Any], str, str]],
    *,
    study_id: str,
    audit_sha256: str,
    audit: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    if len(candidates) != len(evaluated) or len(candidates) != 300:
        raise CourseValidationError("Aggregation requires all 300 audited checkpoint evaluations")
    grouped: dict[str, list[tuple[dict[str, Any], str, str]]] = {}
    for candidate, item in zip(candidates, evaluated, strict=True):
        artifact, artifact_hash, relative_path = item
        validate_validation_artifact(artifact, candidate.expectation)
        grouped.setdefault(candidate.expectation.job_id, []).append((artifact, artifact_hash, relative_path))
    if len(grouped) != 30:
        raise CourseValidationError("Aggregation requires exactly 30 complete primary runs")

    aggregate_runs: list[dict[str, Any]] = []
    proposed_locks: list[dict[str, Any]] = []
    blocked_runs: list[dict[str, Any]] = []
    degenerate_candidates: list[dict[str, Any]] = []
    for job_id in sorted(grouped):
        records = sorted(grouped[job_id], key=lambda item: int(item[0]["checkpoint"]["step"]))
        candidate_summaries: list[dict[str, Any]] = []
        all_discounted: list[np.ndarray] = []
        for artifact, artifact_hash, relative_path in records:
            diagnostics = artifact["diagnostics"]
            if diagnostics["degenerate_objectives"]:
                degenerate_candidates.append(
                    {
                        "job_id": job_id,
                        "step": artifact["checkpoint"]["step"],
                        "objectives": diagnostics["degenerate_objectives"],
                    }
                )
            all_discounted.append(np.asarray(artifact["discounted_episode_returns"], dtype=np.float32))
            candidate_summaries.append(
                {
                    "step": artifact["checkpoint"]["step"],
                    "hypervolume": artifact["metrics"]["hypervolume"],
                    "expected_utility": artifact["metrics"]["expected_utility"],
                    "evidence_path": relative_path,
                    "evidence_sha256": artifact_hash,
                    "checkpoint_path": artifact["checkpoint"]["path"],
                    "checkpoint_sha256": artifact["checkpoint"]["sha256"],
                    "degenerate_objectives": diagnostics["degenerate_objectives"],
                }
            )
        trajectory_degenerate = _degenerate_objectives(np.concatenate(all_discounted, axis=0))
        selected = select_checkpoint(candidate_summaries)
        selected_artifact = next(item[0] for item in records if item[0]["checkpoint"]["step"] == selected["step"])
        expectation = next(candidate.expectation for candidate in candidates if candidate.expectation.job_id == job_id)
        selected_expectation = next(
            candidate.expectation
            for candidate in candidates
            if candidate.expectation.job_id == job_id and candidate.expectation.checkpoint_step == selected["step"]
        )
        validate_validation_artifact(selected_artifact, selected_expectation)
        selected_degenerate = list(selected_artifact["diagnostics"]["degenerate_objectives"])
        eligible_for_lock = not trajectory_degenerate and not selected_degenerate
        if not eligible_for_lock:
            blocked_runs.append(
                {
                    "job_id": job_id,
                    "trajectory_degenerate_objectives": trajectory_degenerate,
                    "selected_degenerate_objectives": selected_degenerate,
                }
            )
        audit_jobs = audit.get("jobs")
        if not isinstance(audit_jobs, list):
            raise CourseValidationError("Source audit jobs are malformed")
        full_log_curve = next(job["validation_log"] for job in audit_jobs if job["job_id"] == job_id)
        aggregate_runs.append(
            {
                "job_id": job_id,
                "environment": expectation.environment,
                "arm": expectation.arm,
                "training_seed": expectation.training_seed,
                "validation_log_curve": full_log_curve,
                "validation_hypervolume_auc": _normalized_auc(full_log_curve["hypervolume"]),
                "validation_expected_utility_auc": _normalized_auc(full_log_curve["expected_utility"]),
                "candidates": [item[0] for item in records],
                "selected_step": selected["step"],
                "eligible_for_lock": eligible_for_lock,
                "trajectory_degenerate_objectives": trajectory_degenerate,
            }
        )
        proposed_locks.append(
            {
                "job_id": job_id,
                "environment": expectation.environment,
                "arm": expectation.arm,
                "training_seed": expectation.training_seed,
                "checkpoint_step": selected["step"],
                "checkpoint_path": selected["checkpoint_path"],
                "checkpoint_sha256": selected["checkpoint_sha256"],
                "validation_hypervolume": selected["hypervolume"],
                "validation_expected_utility": selected["expected_utility"],
                "validation_evidence_path": selected["evidence_path"],
                "validation_evidence_sha256": selected["evidence_sha256"],
                "eligible_for_lock": eligible_for_lock,
            }
        )

    aggregate = {
        "schema_version": 1,
        "kind": "course_primary_validation_aggregate",
        "study_id": study_id,
        "scope": "primary_pcqn_30_job_block",
        "source_audit_sha256": audit_sha256,
        "split": "validation",
        "shift": "nominal",
        "return_fields": ["discounted_episode_returns", "raw_episode_returns"],
        "status": "failed_degenerate" if blocked_runs else "passed",
        "passed": not blocked_runs,
        "runs": aggregate_runs,
        "diagnostics": {
            "missing_runs": [],
            "missing_checkpoints": [],
            "non_finite_values": 0,
            "degenerate_candidates": degenerate_candidates,
            "blocked_runs": blocked_runs,
        },
    }
    lock = build_checkpoint_lock_decision(study_id, proposed_locks, blocked_runs)
    return aggregate, lock


def build_checkpoint_lock_decision(
    study_id: str,
    proposed_locks: Sequence[Mapping[str, Any]],
    blocked_runs: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    blocked = bool(blocked_runs)
    decision = {
        "schema_version": 1,
        "kind": "course_primary_checkpoint_lock",
        "study_id": study_id,
        "scope": "primary_pcqn_30_job_block",
        "status": "blocked" if blocked else "locked",
        "selection_split": "validation",
        "selection_shift": "nominal",
        "selection_rule": (
            "maximum protocol-scaled hypervolume; break exact ties by expected utility, then earlier checkpoint"
        ),
        "final_test_accessed": False,
        "unlocks_final_test": False,
        "lock_count": 0 if blocked else len(proposed_locks),
        "locks": [] if blocked else list(proposed_locks),
        "diagnostic_selections": list(proposed_locks) if blocked else [],
        "blockers": list(blocked_runs),
    }
    return decision


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json_atomic(path: Path, payload: Mapping[str, Any], *, compact: bool = False) -> None:
    _write_json_atomic(path, payload, compact=compact)


def _audit_job(
    root: Path,
    study: dict[str, Any],
    job: dict[str, Any],
    status_record: dict[str, Any],
    arm_spec: dict[str, Any],
    protocol_path: str,
    protocol: dict[str, Any],
    preferences: np.ndarray,
    canonical_protocol_hash: str,
) -> tuple[dict[str, Any], list[ValidationCandidate], int]:
    job_id = str(job["job_id"])
    if status_record.get("status") != "complete" or status_record.get("attempts") != 1:
        raise CourseValidationError(f"Job is not atomically complete with one attempt: {job_id}")
    if status_record.get("final_artifact") != job.get("final_artifact"):
        raise CourseValidationError(f"Execution status final artifact mismatch: {job_id}")
    final_path = root / str(job["final_artifact"])
    if not final_path.is_file():
        raise CourseValidationError(f"Missing final checkpoint: {final_path}")
    final_hash = sha256_file(final_path)
    if status_record.get("artifact_sha256") != final_hash:
        raise CourseValidationError(f"Final checkpoint hash mismatch: {job_id}")

    run_dir = final_path.parent
    run_manifest_path = run_dir / "run_manifest.json"
    run_manifest = _load_json(run_manifest_path)
    config = _mapping(run_manifest.get("config"), "run manifest config")
    if run_manifest.get("config_sha256") != _canonical_hash(config):
        raise CourseValidationError(f"Run manifest config hash mismatch: {job_id}")
    _validate_run_config(config, job, study, arm_spec, protocol_path, protocol)
    if not isinstance(run_manifest.get("git_commit"), str) or not run_manifest["git_commit"]:
        raise CourseValidationError(f"Run manifest Git commit is missing: {job_id}")
    if not isinstance(run_manifest.get("git_dirty"), bool):
        raise CourseValidationError(f"Run manifest Git dirty flag is malformed: {job_id}")
    save_frequency = _positive_int(config.get("save_freq"), "save frequency")
    training_budget = int(study["budget"]["training_interactions"])
    validation_frequency = int(study["budget"]["validation_frequency"])
    if training_budget % save_frequency or save_frequency % validation_frequency:
        raise CourseValidationError(f"Checkpoint cadence is incompatible with validation cadence: {job_id}")
    expected_steps = list(range(save_frequency, training_budget + 1, save_frequency))
    checkpoint_by_step: dict[int, Path] = {}
    for path in run_dir.glob("checkpoint_step*.pt"):
        match = CHECKPOINT_PATTERN.fullmatch(path.name)
        if match is None:
            raise CourseValidationError(f"Malformed checkpoint filename: {path}")
        checkpoint_by_step[int(match.group("step"))] = path
    if sorted(checkpoint_by_step) != expected_steps:
        raise CourseValidationError(f"Missing or unexpected checkpoint steps for {job_id}")

    log_files = sorted((run_dir / "logs").glob("**/events.out.tfevents*"))
    scalar_curves = _load_validation_scalars(log_files)
    expected_log_steps = list(range(validation_frequency, training_budget + 1, validation_frequency))
    for metric, curve in scalar_curves.items():
        if [record["step"] for record in curve] != expected_log_steps:
            raise CourseValidationError(f"Validation log {metric} steps mismatch: {job_id}")
    log_by_step = {
        metric: {record["step"]: record["value"] for record in curve} for metric, curve in scalar_curves.items()
    }

    candidate_records: list[dict[str, Any]] = []
    candidates: list[ValidationCandidate] = []
    previous_counters: dict[str, int] | None = None
    for step in expected_steps:
        path = checkpoint_by_step[step]
        checkpoint = _load_checkpoint(path, "cpu")
        counters = _validate_checkpoint_metadata(
            checkpoint,
            step=step,
            config=config,
            protocol=protocol,
            protocol_path=protocol_path,
            canonical_protocol_hash=canonical_protocol_hash,
            job_id=job_id,
        )
        if previous_counters is not None and any(counters[key] < previous_counters[key] for key in counters):
            raise CourseValidationError(f"Checkpoint counters are not monotone: {job_id} step {step}")
        previous_counters = counters
        relative_path = str(path.relative_to(root))
        checkpoint_hash = sha256_file(path)
        expectation = ValidationExpectation(
            study_id=str(study["id"]),
            job_id=job_id,
            environment=str(job["environment"]),
            arm=str(job["arm"]),
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
            episodes_per_preference=int(study["budget"]["validation_episodes_per_preference"]),
            evaluation_seed=int(config["eval_seed"]),
            training_interaction_budget=training_budget,
            expected_counters=counters,
        )
        training_log_metrics = {
            "hypervolume": log_by_step["hypervolume"][step],
            "expected_utility": log_by_step["expected_utility"][step],
        }
        candidates.append(
            ValidationCandidate(
                expectation=expectation,
                protocol=protocol,
                preferences=preferences,
                training_log_metrics=training_log_metrics,
            )
        )
        candidate_records.append(
            {
                "step": step,
                "path": relative_path,
                "sha256": checkpoint_hash,
                "counters": counters,
                "training_log_metrics": training_log_metrics,
            }
        )

    final_checkpoint = _load_checkpoint(final_path, "cpu")
    final_counters = _validate_checkpoint_metadata(
        final_checkpoint,
        step=training_budget,
        config=config,
        protocol=protocol,
        protocol_path=protocol_path,
        canonical_protocol_hash=canonical_protocol_hash,
        job_id=job_id,
    )
    if final_counters != candidate_records[-1]["counters"]:
        raise CourseValidationError(f"Final and last periodic checkpoint counters differ: {job_id}")
    return (
        {
            "job_id": job_id,
            "environment": job["environment"],
            "arm": job["arm"],
            "training_seed": job["seed"],
            "execution_status": "complete",
            "run_manifest": _file_reference(root, run_manifest_path),
            "training_git_commit": run_manifest.get("git_commit"),
            "training_git_dirty": run_manifest.get("git_dirty"),
            "validation_log_files": [_file_reference(root, path) for path in log_files],
            "validation_log": scalar_curves,
            "final_checkpoint": {
                "path": str(final_path.relative_to(root)),
                "sha256": final_hash,
                "counters": final_counters,
            },
            "checkpoint_candidates": candidate_records,
        },
        candidates,
        save_frequency,
    )


def _validate_execution_status(
    status: Mapping[str, Any], manifest: Mapping[str, Any], gates: Mapping[str, Any]
) -> None:
    if status.get("schema_version") != 1 or status.get("study_id") != manifest.get("study_id"):
        raise CourseValidationError("Execution status schema or study mismatch")
    if status.get("manifest_sha256") != gates.get("matrix_manifest_sha256"):
        raise CourseValidationError("Execution status manifest hash mismatch")
    if status.get("smoke_only") is not False or status.get("course_evidence") is not True:
        raise CourseValidationError("Execution status is not eligible course evidence")
    if not isinstance(status.get("jobs"), dict):
        raise CourseValidationError("Execution status jobs are malformed")


def _validate_run_config(
    config: Mapping[str, Any],
    job: Mapping[str, Any],
    study: Mapping[str, Any],
    arm_spec: Mapping[str, Any],
    protocol_path: str,
    protocol: Mapping[str, Any],
) -> None:
    budget = study["budget"]
    expected = {
        "env": job["environment"],
        "algo": arm_spec["algo"],
        "allocation_target": arm_spec["allocation_target"],
        "seed": job["seed"],
        "total_timesteps": budget["training_interactions"],
        "learning_starts": budget["learning_starts"],
        "train_freq": budget["train_frequency"],
        "curriculum_update_freq": budget["curriculum_update_frequency"],
        "curriculum_eval_episodes": budget["curriculum_episodes_per_preference"],
        "eval_freq": budget["validation_frequency"],
        "eval_episodes": budget["validation_episodes_per_preference"],
        "gap_weight": arm_spec["signal_weights"]["gap"],
        "uncertainty_weight": arm_spec["signal_weights"]["uncertainty"],
        "coverage_weight": arm_spec["signal_weights"]["coverage_recency"],
        "progress_weight": arm_spec["signal_weights"]["progress"],
        "geometry_weight": arm_spec["signal_weights"]["geometry"],
    }
    for key, value in expected.items():
        actual = config.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if not isinstance(actual, (int, float)) or not np.isclose(float(actual), float(value)):
                raise CourseValidationError(f"Run config {key} mismatch for {job['job_id']}")
        elif actual != value:
            raise CourseValidationError(f"Run config {key} mismatch for {job['job_id']}")
    if config.get("protocol") != protocol:
        raise CourseValidationError(f"Run manifest embedded protocol mismatch for {job['job_id']}")
    command = list(job["command"])
    if _command_flag(command, "--protocol") != protocol_path:
        raise CourseValidationError(f"Frozen job protocol path mismatch for {job['job_id']}")
    if "--split" in command or any(str(part).lower() == "test" for part in command):
        raise CourseValidationError(f"Frozen training command accesses a test split: {job['job_id']}")


def _validate_checkpoint_metadata(
    checkpoint: Mapping[str, Any],
    *,
    step: int,
    config: Mapping[str, Any],
    protocol: Mapping[str, Any],
    protocol_path: str,
    canonical_protocol_hash: str,
    job_id: str,
) -> dict[str, int]:
    if checkpoint.get("schema_version") != 2 or checkpoint.get("step") != step:
        raise CourseValidationError(f"Checkpoint schema or step mismatch: {job_id} step {step}")
    if checkpoint.get("protocol") != protocol or checkpoint.get("protocol_sha256") != canonical_protocol_hash:
        raise CourseValidationError(f"Checkpoint protocol hash mismatch: {job_id} step {step}")
    actual_args = _mapping(checkpoint.get("args"), "checkpoint args")
    expected_args_without_protocol = dict(config)
    expected_args_without_protocol.pop("protocol", None)
    actual_args_without_protocol = dict(actual_args)
    actual_protocol_path = actual_args_without_protocol.pop("protocol", None)
    if actual_args_without_protocol != expected_args_without_protocol:
        raise CourseValidationError(f"Checkpoint arguments mismatch: {job_id} step {step}")
    if actual_protocol_path != protocol_path:
        raise CourseValidationError(f"Checkpoint protocol path mismatch: {job_id} step {step}")
    gamma = float(protocol["return_definition"]["gamma"])
    if not np.isclose(float(actual_args.get("gamma", math.nan)), gamma):
        raise CourseValidationError(f"Checkpoint gamma mismatch: {job_id} step {step}")

    counters_raw = _mapping(checkpoint.get("counters"), "checkpoint counters")
    required = {
        "training_interactions",
        "gradient_updates",
        "curriculum_evaluation_steps",
        "validation_evaluation_steps",
    }
    if set(counters_raw) != required:
        raise CourseValidationError(f"Checkpoint counters are malformed: {job_id} step {step}")
    counters = {key: _nonnegative_int(counters_raw[key], f"checkpoint counter {key}") for key in required}
    if counters["training_interactions"] != step:
        raise CourseValidationError(f"Checkpoint training interaction counter mismatch: {job_id} step {step}")
    expected_updates = _expected_gradient_updates(
        step,
        int(actual_args["learning_starts"]),
        int(actual_args["train_freq"]),
    )
    if counters["gradient_updates"] != expected_updates:
        raise CourseValidationError(f"Checkpoint gradient update counter mismatch: {job_id} step {step}")
    if step >= int(actual_args["eval_freq"]) and counters["validation_evaluation_steps"] <= 0:
        raise CourseValidationError(f"Checkpoint lacks validation budget evidence: {job_id} step {step}")
    if step >= int(actual_args["curriculum_update_freq"]) and counters["curriculum_evaluation_steps"] <= 0:
        raise CourseValidationError(f"Checkpoint lacks curriculum budget evidence: {job_id} step {step}")
    return counters


def _load_validation_scalars(paths: Sequence[Path]) -> dict[str, list[dict[str, float | int]]]:
    if len(paths) != 1:
        raise CourseValidationError(f"Expected exactly one TensorBoard validation log, found {len(paths)}")
    try:
        from tensorboard.backend.event_processing.event_accumulator import EventAccumulator
    except ImportError as error:
        raise CourseValidationError("TensorBoard is required to audit validation logs") from error
    accumulator = EventAccumulator(str(paths[0]), size_guidance={"scalars": 0})
    accumulator.Reload()
    output: dict[str, list[dict[str, float | int]]] = {}
    for output_name, tag in (
        ("hypervolume", "eval/hypervolume"),
        ("expected_utility", "eval/expected_utility"),
    ):
        try:
            scalars = accumulator.Scalars(tag)
        except KeyError as error:
            raise CourseValidationError(f"Validation log is missing scalar tag {tag}") from error
        curve = [{"step": int(item.step), "value": float(item.value)} for item in scalars]
        if not curve or len({item["step"] for item in curve}) != len(curve):
            raise CourseValidationError(f"Validation log tag {tag} is empty or has duplicate steps")
        if any(not math.isfinite(float(item["value"])) for item in curve):
            raise CourseValidationError(f"Validation log tag {tag} contains non-finite values")
        output[output_name] = curve
    return output


def _load_checkpoint(path: Path, device: str) -> dict[str, Any]:
    try:
        checkpoint = torch.load(path, map_location=device, weights_only=True)
    except (OSError, RuntimeError, ValueError) as error:
        raise CourseValidationError(f"Cannot safely load checkpoint {path}: {error}") from error
    if not isinstance(checkpoint, dict):
        raise CourseValidationError(f"Checkpoint is not a mapping: {path}")
    return checkpoint


def _load_network(
    checkpoint: Mapping[str, Any],
    *,
    state_dim: int,
    action_dim: int,
    reward_dim: int,
    device: str,
) -> VectorQNetwork:
    architecture = _mapping(checkpoint.get("architecture"), "checkpoint architecture")
    if int(architecture.get("state_dim", -1)) != state_dim:
        raise CourseValidationError("Checkpoint state dimension does not match environment")
    if int(architecture.get("action_dim", -1)) != action_dim:
        raise CourseValidationError("Checkpoint action dimension does not match environment")
    if int(architecture.get("reward_dim", -1)) != reward_dim:
        raise CourseValidationError("Checkpoint reward dimension does not match protocol")
    network = VectorQNetwork(
        state_dim=state_dim,
        action_dim=action_dim,
        reward_dim=reward_dim,
        hidden_dims=architecture.get("hidden_dims", (256, 256)),
        num_heads=int(architecture.get("num_heads", 3)),
    ).to(device)
    try:
        network.load_state_dict(checkpoint["model_state_dict"])
    except (KeyError, RuntimeError, TypeError) as error:
        raise CourseValidationError(f"Checkpoint model state is malformed: {error}") from error
    network.eval()
    return network


def _validate_preference_records(value: Any, expectation: ValidationExpectation) -> np.ndarray:
    if not isinstance(value, list) or len(value) != expectation.preference_count:
        raise CourseValidationError("Validation preference records are missing or malformed")
    weights: list[Any] = []
    for index, record in enumerate(value):
        mapping = _mapping(record, "preference record")
        if mapping.get("id") != f"validation-{index:03d}":
            raise CourseValidationError("Validation preference identifier mismatch")
        weights.append(mapping.get("weights"))
    array = _finite_array(weights, "validation preferences", (expectation.preference_count, expectation.reward_dim))
    if np.any(array < 0.0) or not np.allclose(array.sum(axis=1), 1.0, atol=1e-5):
        raise CourseValidationError("Validation preferences are not on the simplex")
    return array


def _degenerate_objectives(returns: np.ndarray) -> list[int]:
    flattened = np.asarray(returns, dtype=np.float64).reshape(-1, returns.shape[-1])
    return [index for index in range(flattened.shape[1]) if np.ptp(flattened[:, index]) <= 1e-12]


def _normalized_auc(curve: Sequence[Mapping[str, Any]]) -> float:
    steps = np.asarray([record["step"] for record in curve], dtype=np.float64)
    values = np.asarray([record["value"] for record in curve], dtype=np.float64)
    if len(steps) < 2 or np.any(np.diff(steps) <= 0.0) or not np.all(np.isfinite(values)):
        raise CourseValidationError("Validation curve is malformed for AUC")
    return float(np.trapezoid(values, steps) / (steps[-1] - steps[0]))


def _expected_gradient_updates(step: int, learning_starts: int, train_frequency: int) -> int:
    first_update = ((learning_starts + train_frequency - 1) // train_frequency) * train_frequency
    if step < first_update:
        return 0
    return (step - first_update) // train_frequency + 1


def _command_flag(command: Sequence[str], flag: str) -> str:
    try:
        index = command.index(flag)
        return command[index + 1]
    except (ValueError, IndexError) as error:
        raise CourseValidationError(f"Frozen command is missing {flag}") from error


def _file_reference(root: Path, path: Path) -> dict[str, str]:
    return {"path": str(path.resolve().relative_to(root)), "sha256": sha256_file(path)}


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CourseValidationError(f"{label.capitalize()} must be an object")
    return value


def _finite_array(value: Any, label: str, shape: tuple[int, ...]) -> np.ndarray:
    try:
        array = np.asarray(value, dtype=np.float64)
    except (TypeError, ValueError) as error:
        raise CourseValidationError(f"{label.capitalize()} are malformed") from error
    if array.shape != shape:
        raise CourseValidationError(f"{label.capitalize()} shape mismatch: {array.shape} != {shape}")
    if not np.all(np.isfinite(array)):
        raise CourseValidationError(f"{label.capitalize()} must be finite")
    return array


def _finite_float(value: Any, label: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)):
        raise CourseValidationError(f"{label.capitalize()} must be finite")
    return float(value)


def _positive_int(value: Any, label: str) -> int:
    result = _nonnegative_int(value, label)
    if result <= 0:
        raise CourseValidationError(f"{label.capitalize()} must be positive")
    return result


def _nonnegative_int(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise CourseValidationError(f"{label.capitalize()} must be a non-negative integer")
    return value


def _canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _array_sha256(value: np.ndarray) -> str:
    array = np.ascontiguousarray(value)
    return hashlib.sha256(array.tobytes(order="C")).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise CourseValidationError(f"Cannot load JSON file {path}: {error}") from error
    if not isinstance(value, dict):
        raise CourseValidationError(f"Expected JSON object: {path}")
    return value


def _write_json_atomic(path: Path, payload: Mapping[str, Any], *, compact: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    try:
        if compact:
            serialized = json.dumps(
                payload,
                sort_keys=True,
                allow_nan=False,
                separators=(",", ":"),
            )
        else:
            serialized = json.dumps(payload, indent=2, sort_keys=True, allow_nan=False)
        temporary.write_text(serialized + "\n", encoding="utf-8")
        temporary.replace(path)
    except (OSError, TypeError, ValueError) as error:
        raise CourseValidationError(f"Cannot atomically write JSON file {path}: {error}") from error


def expectation_as_dict(expectation: ValidationExpectation) -> dict[str, Any]:
    return asdict(expectation)

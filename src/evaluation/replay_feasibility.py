from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence
from functools import partial
from pathlib import Path
from typing import Any

import numpy as np

from src.evaluation.course_validation import _load_checkpoint, evaluate_candidate, evaluate_or_reuse
from src.evaluation.protocol import load_protocol, protocol_hash
from src.evaluation.remediation import (
    RemediationError,
    _audit_qualification_job,
    _file_reference,
    _load_json,
    _mapping,
    _resolve_relative,
    _validate_qualification_run_config,
    _validate_relative_path,
    sha256_file,
)


def load_f1_plan(root: Path, plan_path: Path) -> tuple[dict[str, Any], str]:
    plan = _load_json(plan_path)
    if plan.get("schema_version") != 1 or plan.get("status") != "predeclared_not_executed":
        raise RemediationError("Unsupported or mutable F1 replay plan")
    if plan.get("execution_authorized") is not False:
        raise RemediationError("The frozen F1 plan must not embed execution authorization")
    authority = _mapping(plan.get("authority"), "F1 authority reference")
    policy = _load_json(_resolve_relative(root, str(authority.get("policy", "")), "ARIS policy"))
    active = _mapping(policy.get("authorization"), "active ARIS authorization")
    if active.get("status") != "active" or active.get("id") != authority.get("authorization_id"):
        raise RemediationError("F1 plan does not bind the active ARIS authorization")
    required_actions = {"scope-change", "protocol-change", "training"}
    if not required_actions.issubset(set(active.get("authorized_actions", []))):
        raise RemediationError("Active ARIS authorization does not cover F1 actions")
    firewall = _mapping(plan.get("data_firewall"), "F1 data firewall")
    if (
        firewall.get("evaluation_split") != "validation"
        or firewall.get("forbidden_split") != "test"
        or firewall.get("shift") != "nominal"
        or firewall.get("final_test_access_permitted") is not False
    ):
        raise RemediationError("F1 data firewall is not validation-only")
    environment = _mapping(plan.get("environment"), "F1 environment")
    protocol_path = _resolve_relative(root, str(environment.get("protocol", "")), "F1 protocol")
    protocol = _load_json(protocol_path)
    if protocol_hash(protocol) != environment.get("protocol_canonical_sha256"):
        raise RemediationError("F1 protocol canonical hash mismatch")
    expected_sources = {"failed_v2_qualification", "failure_investigation"}
    sources = _mapping(plan.get("sources"), "F1 sources")
    if set(sources) != expected_sources:
        raise RemediationError("F1 predecessor sources are incomplete or unexpected")
    for name, raw_reference in sources.items():
        reference = _mapping(raw_reference, f"F1 source {name}")
        path = _resolve_relative(root, str(reference.get("path", "")), f"F1 source {name}")
        if sha256_file(path) != reference.get("sha256"):
            raise RemediationError(f"F1 source hash mismatch: {name}")
    intervention = _mapping(plan.get("intervention"), "F1 intervention")
    if intervention.get("name") != "successful_episode_stratified_hindsight_preference_replay":
        raise RemediationError("Unsupported F1 replay intervention")
    batch_contract = _mapping(intervention.get("batch_contract"), "F1 batch contract")
    if batch_contract != {
        "batch_size": 64,
        "success_positions": 32,
        "uniform_positions": 32,
        "with_replacement": True,
    }:
        raise RemediationError("F1 batch contract drift")
    jobs = build_f1_jobs(plan)
    if len(jobs) != 6:
        raise RemediationError("F1 must contain exactly six paired jobs")
    validate_f1_commands(plan, jobs, protocol)
    return plan, sha256_file(plan_path)


def validate_f1_commands(
    plan: Mapping[str, Any], jobs: Sequence[Mapping[str, Any]], protocol: Mapping[str, Any]
) -> None:
    from scripts.train import parse_args as parse_train_args

    qualification = _mapping(plan.get("qualification"), "F1 qualification")
    training = _mapping(qualification.get("training"), "F1 training")
    if (training.get("total_timesteps"), training.get("expected_gradient_updates"), training.get("batch_size")) != (
        1_000_000,
        995_001,
        64,
    ):
        raise RemediationError("F1 fixed interaction/update/batch budget drift")
    if qualification.get("seeds") != [20264021, 20264022, 20264023]:
        raise RemediationError("F1 fresh paired seed drift")
    for job in jobs:
        arguments = list(job["command"])[2:]
        flags = [part for part in arguments if part.startswith("--")]
        if len(set(flags)) != len(flags):
            raise RemediationError("F1 command contains duplicate flags")
        try:
            config = vars(parse_train_args(arguments))
        except SystemExit as error:
            raise RemediationError("F1 command cannot be parsed") from error
        if config["protocol"] != plan["environment"]["protocol"]:
            raise RemediationError("F1 command protocol path drift")
        config["protocol"] = protocol
        _validate_qualification_run_config(config, plan, job, protocol)


def build_f1_jobs(plan: Mapping[str, Any]) -> list[dict[str, Any]]:
    qualification = _mapping(plan.get("qualification"), "F1 qualification")
    template = qualification.get("base_command_template")
    if not isinstance(template, list) or not all(isinstance(part, str) for part in template):
        raise RemediationError("F1 command template is malformed")
    if template.count("<qualification-seed>") != 1 or template.count("<cell-output-root>") != 1:
        raise RemediationError("F1 command template placeholders are malformed")
    if template[:2] != ["python", "scripts/train.py"]:
        raise RemediationError("F1 command is not allowlisted")
    if "--split" in template or any(part.lower() == "test" for part in template):
        raise RemediationError("F1 command attempts to access the test split")
    seeds = qualification.get("seeds")
    if seeds != [20264021, 20264022, 20264023]:
        raise RemediationError("F1 seeds are malformed")
    cells = _mapping(qualification.get("cells"), "F1 cells")
    if cells != {
        "A0R0": {"stratification": False, "relabel": False},
        "A1R1": {"stratification": True, "relabel": True},
    }:
        raise RemediationError("F1 cells must be the frozen A0R0/A1R1 pair")
    output_root = str(qualification.get("output_root", ""))
    _validate_relative_path(output_root, "F1 output root")
    env_id = str(_mapping(plan.get("environment"), "F1 environment").get("env_id", ""))
    jobs = []
    for seed in seeds:
        for cell, contract in cells.items():
            cell_root = f"{output_root}/{cell}"
            command = [
                str(seed) if part == "<qualification-seed>" else cell_root if part == "<cell-output-root>" else part
                for part in template
            ]
            if contract["stratification"]:
                command.append("--successful-replay-stratification")
            if contract["relabel"]:
                command.append("--successful-replay-relabel")
            jobs.append(
                {
                    "job_id": f"{env_id}__{cell.lower()}__seed{seed}",
                    "cell": cell,
                    "seed": seed,
                    "environment": env_id,
                    "command": command,
                    "final_artifact": f"{cell_root}/uniform-pcqn_{env_id}_seed{seed}/final.pt",
                }
            )
    return jobs


def verify_f1_implementation(root: Path, plan_sha256: str) -> None:
    record = _load_json(root / "research/qualification/minecart_pcqn_replay_f1_implementation.json")
    if record.get("passed") is not True or record.get("training_authorized_after_this_record") is not True:
        raise RemediationError("F1 implementation qualification and review must pass before execution")
    if _mapping(record.get("plan"), "qualified plan").get("sha256") != plan_sha256:
        raise RemediationError("F1 implementation qualification belongs to another plan")
    review = _mapping(record.get("review"), "F1 implementation review")
    if review.get("verdict") != "PASS" or not review.get("trace"):
        raise RemediationError("F1 implementation review evidence is missing")
    _resolve_relative(root, str(review["trace"]), "implementation review").read_text(encoding="utf-8")
    for relative, expected_hash in _mapping(record.get("source_hashes"), "qualified sources").items():
        if sha256_file(_resolve_relative(root, relative, "qualified source")) != expected_hash:
            raise RemediationError(f"F1 qualified source changed: {relative}")


def select_f1_jobs(
    jobs: Sequence[dict[str, Any]], seeds: set[int] | None, cells: set[str] | None
) -> list[dict[str, Any]]:
    return [
        job for job in jobs if (not seeds or int(job["seed"]) in seeds) and (not cells or str(job["cell"]) in cells)
    ]


def audit_f1_sources(
    root: Path,
    *,
    plan_path: Path,
    plan: Mapping[str, Any],
    plan_sha256: str,
    status_path: Path,
) -> tuple[dict[str, Any], dict[tuple[str, int], list[Any]]]:
    status = _load_json(status_path)
    if (
        status.get("schema_version") != 1
        or status.get("kind") != "minecart_backbone_qualification_execution"
        or status.get("plan_id") != plan.get("id")
        or status.get("plan_sha256") != plan_sha256
    ):
        raise RemediationError("F1 execution status does not match the frozen plan")
    execution_commit = status.get("execution_git_commit")
    if not isinstance(execution_commit, str) or not execution_commit:
        raise RemediationError("F1 execution Git commit is missing")
    jobs = build_f1_jobs(plan)
    records = _mapping(status.get("jobs"), "F1 execution status jobs")
    if set(records) != {job["job_id"] for job in jobs}:
        raise RemediationError("F1 status does not contain exactly the six frozen jobs")
    environment = _mapping(plan.get("environment"), "F1 environment")
    protocol_relative = str(environment["protocol"])
    protocol_path = _resolve_relative(root, protocol_relative, "F1 protocol")
    protocol, preferences = load_protocol(protocol_path, "validation")
    canonical_protocol_hash = protocol_hash(protocol)
    audit_jobs = []
    candidates: dict[tuple[str, int], list[Any]] = {}
    for job in jobs:
        record = _mapping(records.get(job["job_id"]), f"F1 status {job['job_id']}")
        job_audit, job_candidates = _audit_qualification_job(
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
        final_path = _resolve_relative(root, str(job["final_artifact"]), "F1 final checkpoint")
        checkpoint = _load_checkpoint(final_path, "cpu")
        replay_audit = _mapping(checkpoint.get("replay_audit"), "F1 replay audit")
        _validate_replay_manipulation(plan, job, replay_audit)
        trajectory_path = final_path.parent / "trajectory_metadata.jsonl"
        trajectories = [json.loads(line) for line in trajectory_path.read_text(encoding="utf-8").splitlines()]
        eligible = [entry for entry in trajectories if entry["eligible"]]
        if (len(trajectories), len(eligible), sum(entry["transition_count"] for entry in eligible)) != (
            replay_audit["completed_trajectories"],
            replay_audit["eligible_trajectories"],
            replay_audit["eligible_transitions"],
        ):
            raise RemediationError("F1 trajectory metadata and replay counters disagree")
        if len({entry["trajectory_id"] for entry in trajectories}) != len(trajectories):
            raise RemediationError("F1 trajectory metadata contains duplicate episodes")
        if str(job["cell"]) == "A1R1":
            training = plan["qualification"]["training"]
            first_eligible = min((entry["step"] for entry in eligible), default=training["total_timesteps"] + 1)
            fallback_updates = max(0, first_eligible - training["learning_starts"])
            if replay_audit["fallback_positions"] != fallback_updates * 32:
                raise RemediationError("F1 success-stratum fallback does not match acquisition timing")
        histogram_path = final_path.parent / "replay_histograms.json"
        histograms = _load_json(histogram_path)
        if sum(histograms["projected_episode_label_counts"].values()) != len(eligible):
            raise RemediationError("F1 projected-label histogram does not match eligible episodes")
        if sum(histograms["effective_relabel_position_counts"].values()) != replay_audit["relabel_attempt_positions"]:
            raise RemediationError("F1 effective-label histogram does not match relabel attempts")
        resource_path = final_path.parent / "resource_usage.json"
        resources = _load_json(resource_path)
        _validate_resources(resources, job)
        job_audit["cell"] = job["cell"]
        job_audit["replay_audit"] = replay_audit
        job_audit["trajectory_metadata"] = _file_reference(root, trajectory_path)
        job_audit["replay_histograms"] = _file_reference(root, histogram_path) | histograms
        job_audit["resource_usage"] = _file_reference(root, resource_path) | {
            "wall_seconds": resources["wall_seconds"],
            "peak_rss_kib": resources["peak_rss_kib"],
            "final_checkpoint_bytes": resources["final_checkpoint_bytes"],
        }
        audit_jobs.append(job_audit)
        candidates[(str(job["cell"]), int(job["seed"]))] = job_candidates
    audit = {
        "schema_version": 1,
        "kind": "minecart_pcqn_replay_f1_source_audit",
        "passed": True,
        "plan": {"path": str(plan_path.relative_to(root)), "sha256": plan_sha256, "id": plan["id"]},
        "execution_status": {"path": str(status_path.relative_to(root)), "sha256": sha256_file(status_path)},
        "execution_git_commit": execution_commit,
        "data_firewall": plan["data_firewall"],
        "protocol": {"path": protocol_relative, "canonical_sha256": canonical_protocol_hash},
        "job_count": len(audit_jobs),
        "checkpoint_count": sum(len(value) for value in candidates.values()),
        "jobs": audit_jobs,
    }
    return audit, candidates


def evaluate_f1_candidates(
    root: Path,
    *,
    candidates: Mapping[tuple[str, int], Sequence[Any]],
    evidence_root: Path,
    device: str,
) -> dict[tuple[str, int], list[tuple[dict[str, Any], str, str]]]:
    evaluated = {}
    for (cell, seed), cell_candidates in candidates.items():
        records = []
        for candidate in cell_candidates:
            expectation = candidate.expectation
            destination = evidence_root / cell / f"seed{seed}" / f"checkpoint_step{expectation.checkpoint_step}.json"
            artifact, artifact_hash, _ = evaluate_or_reuse(
                destination,
                expectation,
                partial(evaluate_candidate, candidate, root, device, verify_training_metrics=True),
            )
            records.append((artifact, artifact_hash, str(destination.relative_to(root))))
        evaluated[(cell, seed)] = records
    return evaluated


def build_f1_decision(
    root: Path,
    *,
    plan_path: Path,
    plan: Mapping[str, Any],
    plan_sha256: str,
    audit_path: Path,
    evaluated: Mapping[tuple[str, int], Sequence[tuple[Mapping[str, Any], str, str]]],
) -> dict[str, Any]:
    qualification = _mapping(plan.get("qualification"), "F1 qualification")
    expected_keys = {(cell, int(seed)) for cell in qualification["cells"] for seed in qualification["seeds"]}
    if set(evaluated) != expected_keys:
        raise RemediationError("F1 evaluated evidence does not contain exactly the frozen cells and seeds")
    expected_steps = qualification["evaluation"]["checkpoint_steps"]
    pass_rule = _mapping(qualification.get("pass_rule"), "F1 pass rule")
    decisions = []
    total_evaluation_steps = 0
    for cell, seed in sorted(expected_keys):
        records = evaluated[(cell, seed)]
        if len(records) != len(expected_steps):
            raise RemediationError(f"F1 evidence is incomplete for {cell} seed {seed}")
        checkpoints = []
        for artifact, artifact_hash, relative_path in records:
            checkpoint = _mapping(artifact.get("checkpoint"), "F1 validation checkpoint")
            total_evaluation_steps += int(_mapping(artifact.get("evaluation"), "F1 evaluation")["evaluation_steps"])
            checkpoints.append(
                _checkpoint_decision(
                    int(checkpoint["step"]),
                    np.asarray(artifact["discounted_episode_returns"], dtype=np.float32),
                    relative_path,
                    artifact_hash,
                    pass_rule,
                )
            )
        if [item["step"] for item in checkpoints] != expected_steps:
            raise RemediationError(f"F1 checkpoint steps drift for {cell} seed {seed}")
        retention = _retention_decision(checkpoints, pass_rule) if cell == "A1R1" else None
        decisions.append({"cell": cell, "training_seed": seed, "checkpoints": checkpoints, "retention": retention})
    a1_retention = [item["retention"] for item in decisions if item["cell"] == "A1R1"]
    passed = all(item and item["passed"] for item in a1_retention)
    return {
        "schema_version": 1,
        "kind": "minecart_pcqn_replay_f1_qualification",
        "status": "passed" if passed else "failed",
        "passed": passed,
        "evidence_role": qualification["evidence_role"],
        "plan": {"path": str(plan_path.relative_to(root)), "sha256": plan_sha256, "id": plan["id"]},
        "source_audit": {"path": str(audit_path.relative_to(root)), "sha256": sha256_file(audit_path)},
        "data_firewall": plan["data_firewall"],
        "pass_rule": pass_rule,
        "cell_seed_decisions": decisions,
        "evaluation_summary": {
            "checkpoint_evaluations": len(expected_steps) * len(expected_keys),
            "episodes": len(expected_steps)
            * len(expected_keys)
            * qualification["evaluation"]["episode_count_per_checkpoint"],
            "environment_steps": total_evaluation_steps,
        },
        "eligible_for_separate_f2_authorization": passed,
        "unlocks_f2": False,
        "unlocks_matrix_v1": False,
        "unlocks_checkpoint_lock": False,
        "unlocks_final_test": False,
        "continuation": (
            "F1 passed; request and record the separate conditional F2 authorization before any F2 run."
            if passed
            else qualification["failure_rule"]
        ),
    }


def _checkpoint_decision(
    step: int,
    returns: np.ndarray,
    path: str,
    artifact_hash: str,
    pass_rule: Mapping[str, Any],
) -> dict[str, Any]:
    if returns.ndim != 3 or not np.all(np.isfinite(returns)):
        raise RemediationError("F1 validation return tensor is malformed or non-finite")
    objective_decisions = {}
    passed = True
    for objective in pass_rule["ore_objective_indices"]:
        values = returns[:, :, int(objective)].reshape(-1)
        positive = values[values > 0.0]
        objective_passed = (
            positive.size >= pass_rule["minimum_positive_episodes_per_objective"]
            and np.unique(positive).size >= pass_rule["minimum_distinct_positive_values_per_objective"]
        )
        passed = passed and objective_passed
        objective_decisions[str(objective)] = {
            "positive_episode_count": int(positive.size),
            "distinct_positive_values": int(np.unique(positive).size),
            "passed": bool(objective_passed),
        }
    return {
        "step": step,
        "passed": bool(passed),
        "ore_objectives": objective_decisions,
        "validation_artifact": {"path": path, "sha256": artifact_hash},
    }


def _retention_decision(checkpoints: Sequence[Mapping[str, Any]], pass_rule: Mapping[str, Any]) -> dict[str, Any]:
    passing_indices = [index for index, checkpoint in enumerate(checkpoints) if checkpoint["passed"]]
    if not passing_indices:
        return {"status": "never_expressed", "passed": False, "first_pass_step": None}
    first_index = passing_indices[0]
    first_step = int(checkpoints[first_index]["step"])
    if first_step > int(pass_rule["first_pass_no_later_than_step"]):
        return {"status": pass_rule["late_first_pass_status"], "passed": False, "first_pass_step": first_step}
    required = int(pass_rule["required_consecutive_pass_checkpoints"])
    window = checkpoints[first_index : first_index + required]
    passed = len(window) == required and all(checkpoint["passed"] for checkpoint in window)
    return {
        "status": "retained" if passed else "retention_failed",
        "passed": passed,
        "first_pass_step": first_step,
        "required_steps": [int(checkpoint["step"]) for checkpoint in window],
    }


def _validate_replay_manipulation(
    plan: Mapping[str, Any], job: Mapping[str, Any], replay_audit: Mapping[str, Any]
) -> None:
    qualification = _mapping(plan.get("qualification"), "F1 qualification")
    updates = int(qualification["training"]["expected_gradient_updates"])
    cell = str(job["cell"])
    integer_fields = [
        "completed_trajectories",
        "eligible_trajectories",
        "eligible_transitions",
        "success_positions_requested",
        "success_positions_sampled",
        "uniform_positions_sampled",
        "fallback_positions",
        "relabel_attempt_positions",
        "relabel_changed_positions",
        "live_eligible_trajectory_count",
    ]
    if any(not isinstance(replay_audit.get(field), int) or replay_audit[field] < 0 for field in integer_fields):
        raise RemediationError(f"F1 replay counters are malformed for {job['job_id']}")
    if cell == "A0R0":
        for field in (
            "success_positions_requested",
            "success_positions_sampled",
            "fallback_positions",
            "relabel_attempt_positions",
            "relabel_changed_positions",
        ):
            if replay_audit[field] != 0:
                raise RemediationError(f"A0R0 replay counter {field} must be zero")
        if replay_audit["uniform_positions_sampled"] != updates * 64:
            raise RemediationError("A0R0 uniform sampled-position budget mismatch")
    elif cell == "A1R1":
        requested = updates * 32
        if replay_audit["success_positions_requested"] != requested:
            raise RemediationError("A1R1 requested success-position budget mismatch")
        if replay_audit["success_positions_sampled"] + replay_audit["fallback_positions"] != requested:
            raise RemediationError("A1R1 success/fallback accounting mismatch")
        if replay_audit["uniform_positions_sampled"] != updates * 32 + replay_audit["fallback_positions"]:
            raise RemediationError("A1R1 uniform sampled-position budget mismatch")
        if replay_audit["eligible_trajectories"] > 0 and replay_audit["success_positions_sampled"] == 0:
            raise RemediationError("A1R1 created eligible trajectories but never sampled the success stratum")
        if replay_audit["relabel_changed_positions"] > replay_audit["relabel_attempt_positions"]:
            raise RemediationError("A1R1 changed relabel count exceeds attempts")
        if replay_audit["relabel_attempt_positions"] < replay_audit["success_positions_sampled"]:
            raise RemediationError("A1R1 relabel attempts omit success-branch positions")
        if replay_audit["relabel_attempt_positions"] > updates * 64:
            raise RemediationError("A1R1 relabel attempts exceed all sampled positions")
    else:
        raise RemediationError(f"Unexpected F1 cell: {cell}")


def _validate_resources(resources: Mapping[str, Any], job: Mapping[str, Any]) -> None:
    for field in ("wall_seconds", "peak_rss_kib", "final_checkpoint_bytes"):
        value = resources.get(field)
        if not isinstance(value, (int, float)) or not math.isfinite(float(value)) or float(value) <= 0:
            raise RemediationError(f"F1 resource field {field} is invalid for {job['job_id']}")

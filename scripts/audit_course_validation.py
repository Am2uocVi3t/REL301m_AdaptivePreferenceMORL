#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from functools import partial
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.evaluation.course_validation import (
    CourseValidationError,
    aggregate_and_lock,
    audit_primary_sources,
    evaluate_candidate,
    evaluate_or_reuse,
    sha256_file,
    write_json_atomic,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit primary PCQN validation evidence and lock checkpoints without test access"
    )
    parser.add_argument("--study", default="configs/experiments/course_paired_matrix_v1.json")
    parser.add_argument("--manifest", default="research/experiments/course_paired_matrix_v1_manifest.json")
    parser.add_argument("--gates", default="research/qualification/course_matrix_gates_v1.json")
    parser.add_argument(
        "--execution-status",
        default="artifacts/course-paired-matrix-v1/execution_status.json",
    )
    parser.add_argument(
        "--evidence-dir",
        default="artifacts/course-paired-matrix-v1/validation-evidence-v1",
    )
    parser.add_argument(
        "--audit-output",
        default="research/evidence/course_primary_execution_audit_v1.json",
    )
    parser.add_argument(
        "--aggregate-output",
        default="research/evidence/course_primary_validation_v1.json",
    )
    parser.add_argument(
        "--lock-output",
        default="research/evidence/course_primary_checkpoint_lock_v1.json",
    )
    parser.add_argument("--device", default="cpu")
    parser.add_argument(
        "--max-new-evaluations",
        type=int,
        help="Stop after this many new checkpoint evaluations; verified existing evidence is still reused",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.max_new_evaluations is not None and args.max_new_evaluations <= 0:
        raise CourseValidationError("--max-new-evaluations must be positive")
    root = Path(__file__).resolve().parents[1]
    study_path = _resolve(root, args.study)
    manifest_path = _resolve(root, args.manifest)
    gates_path = _resolve(root, args.gates)
    execution_status_path = _resolve(root, args.execution_status)
    evidence_dir = _resolve(root, args.evidence_dir)
    audit_output = _resolve(root, args.audit_output)
    aggregate_output = _resolve(root, args.aggregate_output)
    lock_output = _resolve(root, args.lock_output)

    print("Auditing frozen study, manifest, protocols, execution status, logs, and checkpoints...", flush=True)
    audit, candidates = audit_primary_sources(
        root,
        study_path=study_path,
        manifest_path=manifest_path,
        gates_path=gates_path,
        execution_status_path=execution_status_path,
    )
    write_json_atomic(audit_output, audit)
    audit_hash = sha256_file(audit_output)
    print(f"Source audit passed: {len(audit['jobs'])} jobs, {len(candidates)} checkpoints", flush=True)

    evaluated: list[tuple[dict, str, str]] = []
    new_evaluations = 0
    for index, candidate in enumerate(candidates, start=1):
        expectation = candidate.expectation
        destination = evidence_dir / expectation.job_id / f"checkpoint_step{expectation.checkpoint_step}.json"
        if (
            not destination.exists()
            and args.max_new_evaluations is not None
            and new_evaluations >= args.max_new_evaluations
        ):
            print(
                f"Paused after {new_evaluations} new evaluations; rerun the same command to resume.",
                flush=True,
            )
            return
        artifact, artifact_hash, reused = evaluate_or_reuse(
            destination,
            expectation,
            partial(evaluate_candidate, candidate, root, args.device),
        )
        if not reused:
            new_evaluations += 1
        relative_path = str(destination.relative_to(root))
        evaluated.append((artifact, artifact_hash, relative_path))
        action = "reused" if reused else "evaluated"
        print(
            f"[{index:03d}/{len(candidates)}] {action} {expectation.job_id} step={expectation.checkpoint_step}",
            flush=True,
        )

    aggregate, lock = aggregate_and_lock(
        candidates,
        evaluated,
        study_id=str(audit["study_id"]),
        audit_sha256=audit_hash,
        audit=audit,
    )
    write_json_atomic(aggregate_output, aggregate, compact=True)
    aggregate_hash = sha256_file(aggregate_output)
    lock["source_audit"] = {"path": str(audit_output.relative_to(root)), "sha256": audit_hash}
    lock["validation_aggregate"] = {
        "path": str(aggregate_output.relative_to(root)),
        "sha256": aggregate_hash,
    }
    write_json_atomic(lock_output, lock)
    if lock["status"] == "blocked":
        print(
            f"Checkpoint lock blocked for {len(lock['blockers'])} degenerate runs; "
            "zero checkpoints locked and final test remains locked.",
            flush=True,
        )
        raise SystemExit(2)
    print(f"Locked {lock['lock_count']} checkpoints; final test remains locked.", flush=True)


def _resolve(root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


if __name__ == "__main__":
    main()

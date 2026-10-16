#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.evaluation.course_executor import (
    CourseExecutionError,
    authorize_execution,
    load_verified_execution_inputs,
    prepare_smoke_job,
    run_selected_jobs,
    select_jobs,
    verify_manifest_matches_study,
    verify_post_validation_execution_gate,
)
from src.evaluation.course_matrix import load_course_study


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Safely dry-run or execute bounded jobs from the frozen course matrix")
    parser.add_argument("--config", default="configs/experiments/course_paired_matrix_v1.json")
    parser.add_argument("--manifest", default="research/experiments/course_paired_matrix_v1_manifest.json")
    parser.add_argument("--gates", default="research/qualification/course_matrix_gates_v1.json")
    parser.add_argument(
        "--post-validation-gate",
        default="research/qualification/course_matrix_post_validation_gate_v1.json",
    )
    parser.add_argument("--status", default=None)
    parser.add_argument("--arm", action="append", dest="arms")
    parser.add_argument("--environment", action="append", dest="environments")
    parser.add_argument("--seed", action="append", type=int, dest="seeds")
    parser.add_argument("--job-id", action="append", dest="job_ids")
    parser.add_argument("--family", action="append", dest="families")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--acknowledge-study-id")
    parser.add_argument("--max-jobs", type=int)
    parser.add_argument("--retry-failed", action="store_true")
    parser.add_argument(
        "--smoke-only",
        action="store_true",
        help="Execute one isolated 20-step PCQN smoke job; never counts as course evidence",
    )
    parser.add_argument(
        "--smoke-output-root",
        default="artifacts/course-executor-smoke",
        help="Repository-relative output root used only with --smoke-only",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(__file__).resolve().parents[1]
    manifest_path = root / args.manifest
    gates_path = root / args.gates
    manifest, gates = load_verified_execution_inputs(root, manifest_path, gates_path)
    study = load_course_study(root / args.config)
    verify_manifest_matches_study(manifest, study, root)

    selected = select_jobs(
        manifest,
        arms=set(args.arms or ()),
        environments=set(args.environments or ()),
        seeds=set(args.seeds or ()),
        job_ids=set(args.job_ids or ()),
        families=set(args.families or ()),
    )
    selectors_used = any((args.arms, args.environments, args.seeds, args.job_ids, args.families))
    authorized = authorize_execution(
        manifest,
        selected,
        execute=args.execute,
        acknowledgement=args.acknowledge_study_id,
        max_jobs=args.max_jobs,
        selectors_used=selectors_used,
        smoke_only=args.smoke_only,
    )

    preview = {
        "study_id": manifest["study_id"],
        "mode": "smoke" if args.smoke_only else "course",
        "execute": authorized,
        "selected_jobs": len(selected),
        "job_ids": [job["job_id"] for job in selected],
    }
    print(json.dumps(preview, indent=2))
    if not authorized:
        return

    verify_post_validation_execution_gate(
        root,
        root / args.post_validation_gate,
        str(manifest["study_id"]),
        smoke_only=args.smoke_only,
    )

    if sys.version_info[:2] != (3, 11):
        raise CourseExecutionError(
            f"Execution requires Python 3.11, found {sys.version_info.major}.{sys.version_info.minor}"
        )

    execution_jobs = selected
    if args.smoke_only:
        execution_jobs = [prepare_smoke_job(selected[0], args.smoke_output_root)]
    default_status = (
        "artifacts/course-executor-smoke/execution_status.json"
        if args.smoke_only
        else f"artifacts/{manifest['study_id']}/execution_status.json"
    )
    status_path = root / (args.status or default_status)

    def run_command(command: list[str], cwd: Path) -> None:
        runtime_command = [sys.executable, *command[1:]]
        subprocess.run(runtime_command, cwd=cwd, check=True)

    status = run_selected_jobs(
        root=root,
        manifest=manifest,
        gates=gates,
        jobs=execution_jobs,
        status_path=status_path,
        run_command=run_command,
        retry_failed=args.retry_failed,
        smoke_only=args.smoke_only,
    )
    completed = sum(record.get("status") == "complete" for record in status["jobs"].values())
    print(json.dumps({"status": str(status_path.relative_to(root)), "completed": completed}))


if __name__ == "__main__":
    try:
        main()
    except CourseExecutionError as error:
        raise SystemExit(f"course executor refused: {error}") from error

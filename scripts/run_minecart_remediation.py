#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.evaluation.remediation import (
    RemediationError,
    audit_qualification_sources,
    authorize_qualification,
    build_qualification_decision,
    build_qualification_jobs,
    evaluate_qualification_candidates,
    load_qualification_plan,
    repository_snapshot,
    run_qualification_jobs,
    select_qualification_jobs,
    write_json_atomic,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run and audit the predeclared validation-only Minecart backbone qualification"
    )
    parser.add_argument("--plan", default="configs/remediations/minecart_pcqn_backbone_v2.json")
    parser.add_argument("--seed", action="append", type=int, dest="seeds")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--acknowledge-plan-id")
    parser.add_argument("--max-seeds", type=int)
    parser.add_argument("--retry-failed", action="store_true")
    parser.add_argument("--audit", action="store_true")
    parser.add_argument("--status")
    parser.add_argument("--evidence-dir")
    parser.add_argument("--audit-output")
    parser.add_argument("--qualification-output")
    parser.add_argument("--device", default="cpu")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(__file__).resolve().parents[1]
    plan_path = _resolve(root, args.plan)
    plan, plan_sha256 = load_qualification_plan(root, plan_path)
    qualification = plan["qualification"]
    all_jobs = build_qualification_jobs(plan)
    selected = select_qualification_jobs(all_jobs, set(args.seeds) if args.seeds else None)
    unknown_seeds = set(args.seeds or ()) - {int(job["seed"]) for job in all_jobs}
    if unknown_seeds:
        raise RemediationError(f"Unknown qualification seeds: {sorted(unknown_seeds)}")

    authorized = authorize_qualification(
        plan,
        selected,
        execute=args.execute,
        acknowledgement=args.acknowledge_plan_id,
        max_seeds=args.max_seeds,
        selectors_used=bool(args.seeds),
    )
    print(
        json.dumps(
            {
                "plan_id": plan["id"],
                "plan_sha256": plan_sha256,
                "selected_seeds": [job["seed"] for job in selected],
                "execute": authorized,
                "audit": args.audit,
                "final_test_access": False,
            },
            indent=2,
        ),
        flush=True,
    )

    status_path = _resolve(root, args.status or qualification["execution_status"])
    if authorized:
        if sys.version_info[:2] != (3, 11):
            raise RemediationError("Qualification execution requires Python 3.11")
        execution_commit, dirty = repository_snapshot(root)
        if dirty:
            raise RemediationError("Qualification execution requires a clean committed worktree")

        def run_command(command: list[str], cwd: Path) -> None:
            subprocess.run([sys.executable, *command[1:]], cwd=cwd, check=True)

        run_qualification_jobs(
            root=root,
            plan=plan,
            plan_sha256=plan_sha256,
            jobs=selected,
            status_path=status_path,
            run_command=run_command,
            retry_failed=args.retry_failed,
            execution_git_commit=execution_commit,
            python_executable=sys.executable,
        )

    if not args.audit:
        return
    audit_path = _resolve(root, args.audit_output or qualification["source_audit_output"])
    evidence_root = _resolve(root, args.evidence_dir or qualification["validation_evidence_root"])
    qualification_path = _resolve(root, args.qualification_output or qualification["qualification_output"])
    audit, candidates_by_seed = audit_qualification_sources(
        root,
        plan_path=plan_path,
        plan=plan,
        plan_sha256=plan_sha256,
        status_path=status_path,
    )
    write_json_atomic(audit_path, audit)
    print(f"Source audit passed: {audit['checkpoint_count']} checkpoints", flush=True)
    evaluated = evaluate_qualification_candidates(
        root,
        candidates_by_seed=candidates_by_seed,
        evidence_root=evidence_root,
        device=args.device,
    )
    decision = build_qualification_decision(
        root,
        plan_path=plan_path,
        plan=plan,
        plan_sha256=plan_sha256,
        audit_path=audit_path,
        evaluated=evaluated,
    )
    write_json_atomic(qualification_path, decision)
    print(
        f"Qualification {decision['status']}: {qualification_path.relative_to(root)}; final test remains locked.",
        flush=True,
    )
    if not decision["passed"]:
        raise SystemExit(2)


def _resolve(root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


if __name__ == "__main__":
    try:
        main()
    except RemediationError as error:
        raise SystemExit(f"Minecart remediation refused: {error}") from error

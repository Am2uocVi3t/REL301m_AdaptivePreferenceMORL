#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fcntl
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.evaluation.remediation import (
    RemediationError,
    authorize_qualification,
    repository_snapshot,
    run_qualification_jobs,
    write_json_atomic,
)
from src.evaluation.replay_feasibility import (
    audit_f1_sources,
    build_f1_decision,
    build_f1_jobs,
    evaluate_f1_candidates,
    load_f1_plan,
    select_f1_jobs,
    verify_f1_implementation,
)
from src.research_harness.aris import preflight


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run and audit the frozen Minecart successful-replay F1 screen")
    parser.add_argument("--plan", default="configs/remediations/minecart_pcqn_replay_f1.json")
    parser.add_argument("--seed", action="append", type=int, dest="seeds")
    parser.add_argument("--cell", action="append", choices=("A0R0", "A1R1"), dest="cells")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--acknowledge-plan-id")
    parser.add_argument("--max-jobs", type=int)
    parser.add_argument("--retry-failed", action="store_true")
    parser.add_argument("--audit", action="store_true")
    parser.add_argument("--status")
    parser.add_argument("--evidence-dir")
    parser.add_argument("--audit-output")
    parser.add_argument("--qualification-output")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--remaining-percent", type=float)
    parser.add_argument("--quota-observed-at")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(__file__).resolve().parents[1]
    plan_path = _resolve(root, args.plan)
    plan, plan_sha256 = load_f1_plan(root, plan_path)
    qualification = plan["qualification"]
    all_jobs = build_f1_jobs(plan)
    selected = select_f1_jobs(
        all_jobs, set(args.seeds) if args.seeds else None, set(args.cells) if args.cells else None
    )
    known_seeds = {int(job["seed"]) for job in all_jobs}
    if set(args.seeds or ()) - known_seeds:
        raise RemediationError("Unknown F1 seed selector")
    authorized = authorize_qualification(
        plan,
        selected,
        execute=args.execute,
        acknowledgement=args.acknowledge_plan_id,
        max_seeds=args.max_jobs,
        selectors_used=bool(args.seeds) and bool(args.cells),
    )
    print(
        json.dumps(
            {
                "plan_id": plan["id"],
                "plan_sha256": plan_sha256,
                "selected_jobs": [{"cell": job["cell"], "seed": job["seed"]} for job in selected],
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
        verify_f1_implementation(root, plan_sha256)
        report = preflight(root, "training", args.remaining_percent, args.quota_observed_at)
        if report["status"] != "PASS":
            raise RemediationError("F1 preflight blocked: " + "; ".join(report["blockers"]))
        if args.retry_failed:
            raise RemediationError("F1 retries require preserving and auditing the interrupted attempt first")
        if sys.version_info[:2] != (3, 11):
            raise RemediationError("F1 execution requires Python 3.11")
        execution_commit, dirty = repository_snapshot(root)
        if dirty:
            raise RemediationError("F1 execution requires a clean committed worktree")

        def run_command(command: list[str], cwd: Path) -> None:
            live_commit, live_dirty = repository_snapshot(cwd)
            if live_dirty or live_commit != execution_commit:
                raise RemediationError("F1 source tree changed during the bounded batch")
            output_root = Path(command[command.index("--output-dir") + 1])
            seed = command[command.index("--seed") + 1]
            run_directory = cwd / output_root / f"uniform-pcqn_minecart-v0_seed{seed}"
            if run_directory.exists():
                raise RemediationError("F1 destination exists; preserve and audit the previous attempt before retry")
            log_path = cwd / output_root / f"seed{seed}.log"
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with log_path.open("x", encoding="utf-8") as log_file:
                subprocess.run(
                    [sys.executable, "-u", *command[1:]], cwd=cwd, check=True, stdout=log_file, stderr=subprocess.STDOUT
                )

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
    audit, candidates = audit_f1_sources(
        root,
        plan_path=plan_path,
        plan=plan,
        plan_sha256=plan_sha256,
        status_path=status_path,
    )
    write_json_atomic(audit_path, audit)
    evaluated = evaluate_f1_candidates(root, candidates=candidates, evidence_root=evidence_root, device=args.device)
    decision = build_f1_decision(
        root,
        plan_path=plan_path,
        plan=plan,
        plan_sha256=plan_sha256,
        audit_path=audit_path,
        evaluated=evaluated,
    )
    write_json_atomic(qualification_path, decision)
    print(
        f"F1 qualification {decision['status']}: {qualification_path.relative_to(root)}; final test remains locked.",
        flush=True,
    )
    if not decision["passed"]:
        raise SystemExit(2)


def _resolve(root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


if __name__ == "__main__":
    try:
        lock_path = Path(__file__).resolve().parents[1] / ".aris" / "minecart-f1-executor.lock"
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        with lock_path.open("a") as executor_lock:
            try:
                fcntl.flock(executor_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise RemediationError("Another F1 executor is active") from error
            main()
    except RemediationError as error:
        raise SystemExit(f"Minecart F1 refused: {error}") from error

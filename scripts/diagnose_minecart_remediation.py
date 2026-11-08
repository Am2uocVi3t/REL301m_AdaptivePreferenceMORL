#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import platform
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.evaluation.minecart_diagnosis import (
    MinecartDiagnosisError,
    build_mechanism_assessment,
    evaluate_checkpoint_behavior,
    load_diagnosis_plan,
)
from src.evaluation.remediation import repository_snapshot
from src.utils.provenance import collect_provenance, write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Diagnose remediation-v1 Minecart behavior on validation only")
    parser.add_argument(
        "--plan",
        default="configs/diagnostics/minecart_remediation_v1_behavior.json",
        help="Predeclared validation-only diagnosis plan",
    )
    parser.add_argument("--execute", action="store_true", help="Run the predeclared checkpoint probe")
    parser.add_argument("--acknowledge-plan-id", help="Exact plan ID required for execution")
    parser.add_argument("--device", default="cpu")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(__file__).resolve().parents[1]
    plan_path = (root / args.plan).resolve()
    plan, plan_sha256 = load_diagnosis_plan(root, plan_path)
    checkpoints = plan["evaluation"]["checkpoints"]
    if not args.execute:
        print(f"Plan: {plan['id']}")
        print(f"Checkpoints: {len(checkpoints)}")
        print(f"Episodes: {len(checkpoints) * plan['evaluation']['episode_count_per_checkpoint']}")
        print(f"Output: {plan['output']}")
        print("Preview only; no environments were evaluated.")
        return

    if args.acknowledge_plan_id != plan["id"]:
        raise MinecartDiagnosisError(f"Execution requires exact plan acknowledgement: {plan['id']}")
    if platform.python_version_tuple()[:2] != ("3", "11"):
        raise MinecartDiagnosisError("Diagnosis execution requires Python 3.11")
    git_commit, git_dirty = repository_snapshot(root)
    if git_dirty:
        raise MinecartDiagnosisError("Diagnosis execution requires a clean committed worktree")

    records = []
    for index, checkpoint in enumerate(checkpoints, start=1):
        print(
            f"[{index}/{len(checkpoints)}] seed={checkpoint['training_seed']} "
            f"step={checkpoint['step']} role={checkpoint['role']}",
            flush=True,
        )
        records.append(evaluate_checkpoint_behavior(root, plan, checkpoint, device=args.device))

    output = {
        "schema_version": 1,
        "kind": "minecart_remediation_v1_behavior_diagnosis",
        "status": "complete_validation_only",
        "plan": {
            "path": str(plan_path.relative_to(root)),
            "sha256": plan_sha256,
            "id": plan["id"],
        },
        "sources": plan["sources"],
        "data_firewall": plan["data_firewall"],
        "environment": plan["environment"],
        "evaluation": {
            "policy_mode": plan["evaluation"]["policy_mode"],
            "preference_count": plan["evaluation"]["preference_count"],
            "episodes_per_preference": plan["evaluation"]["episodes_per_preference"],
            "seed_base": plan["evaluation"]["seed_base"],
            "checkpoint_count": len(records),
            "episode_count": sum(int(record["episodes"]) for record in records),
            "environment_steps": sum(int(record["environment_steps"]) for record in records),
        },
        "checkpoints": records,
        "mechanism_assessment": build_mechanism_assessment(records),
        "unlocks_matrix_v1": False,
        "unlocks_final_test": False,
        "provenance": collect_provenance(
            {
                "plan_sha256": plan_sha256,
                "git_commit": git_commit,
                "device": args.device,
            }
        ),
    }
    output_path = root / plan["output"]
    write_json(output_path, output)
    print(f"Wrote behavior diagnosis to {output_path}")
    print(f"Leading v2 mechanism: {output['mechanism_assessment']['leading_v2_mechanism']}")


if __name__ == "__main__":
    main()

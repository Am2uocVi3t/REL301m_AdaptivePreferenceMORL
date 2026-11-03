"""Deterministic current-report inputs, citations and bounded-result checks.

This is not independent semantic review or full-text citation-context review.
It reads retained evidence; no training, rollouts or final-test split access.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.utils.training_recovery import atomic_json

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper/REL301m"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def current_inputs(path: Path, seen: set[Path] | None = None) -> list[Path]:
    seen = set() if seen is None else seen
    path = path.resolve()
    if path in seen:
        return []
    if not path.is_relative_to(PAPER) or not path.is_file():
        raise ValueError(f"Missing or out-of-scope report input: {path}")
    seen.add(path)
    result = [path]
    for name in re.findall(r"\\input\{([^}]+)\}", path.read_text(encoding="utf-8")):
        child = PAPER / (name if name.endswith(".tex") else name + ".tex")
        result.extend(current_inputs(child, seen))
    return result


def audit() -> dict[str, Any]:
    files = current_inputs(PAPER / "main.tex")
    text = "\n".join(p.read_text(encoding="utf-8") for p in files)
    bibliography = ROOT / "research/literature/library.bib"
    keys = re.findall(r"@\w+\s*\{\s*([^,]+),", bibliography.read_text(encoding="utf-8"))
    if len(keys) != len(set(keys)):
        raise ValueError("Duplicate bibliography keys")
    cited = sorted({key.strip() for group in re.findall(r"\\cite\w*\{([^}]+)\}", text) for key in group.split(",")})
    papers = {p["id"]: p for p in json.loads((ROOT / "research/literature/index.json").read_text())["papers"]}
    for key in cited:
        if key not in keys or key not in papers:
            raise ValueError(f"Unregistered or undefined citation: {key}")
    paths = sorted(set(re.findall(r"\\(?:evidence|path)\{([^}]+)\}", text)))
    paths = [name for name in paths if not re.fullmatch(r"#\d", name)]
    for name in paths:
        if not (ROOT / name).exists():
            raise ValueError(f"Missing cited repository artifact: {name}")
    graphics = re.findall(r"\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}", text)
    for name in graphics:
        if not (PAPER / name).is_file():
            raise ValueError(f"Missing report graphic: {name}")
    evidence_path = ROOT / "research/evidence/minecart_onpolicy_confirmation_v1.json"
    g = json.loads(evidence_path.read_text())
    if not g["all_seed_both_mode_both_profile_gate_pass"] or g["final_test_steps"] != 0:
        raise ValueError("Confirmation scope/gate differs from report")
    for name, expected in g["source_sha256"].items():
        if digest(ROOT / name) != expected:
            raise ValueError(f"Confirmation source changed: {name}")
    chapter = (PAPER / "Chapters/OnpolicyResults.tex").read_text()
    for job in g["jobs"]:
        gates = job["final_gates"]
        counts = [p["deliveries"] for mode in ["sampled", "argmax"] for p in gates[mode]["profiles"]]
        if counts != [10, 10, 10, 10] or f"{job['seed']} &10/10&10/10&10/10&10/10" not in chapter:
            raise ValueError("Report task table differs from raw final gates")
    for statistic in g["statistics"]:
        if statistic["kind"] == "validation":
            for field in ["eu_mean", "eu_sample_sd"]:
                if f"{statistic[field]:.5f}" not in chapter:
                    raise ValueError(f"Report EU summary differs: {statistic['mode']}/{field}")
    for value in [g["development_episodes"], g["development_steps"], g["task_trace_count"]]:
        if f"{value:,}" not in chapter:
            raise ValueError("Report confirmation budget differs")
    if g["training_interactions"] != 12000000 or len(g["jobs"]) != 3:
        raise ValueError("Confirmation training scope differs")
    lunar_plan = json.loads((ROOT / "configs/experiments/lunar_onpolicy_specialist_v1.json").read_text())
    lunar_complete = (
        ROOT / "artifacts/lunar-onpolicy-specialist-v1/runs/mo-lunar-lander-v3_L_seed20265311/complete.json"
    )
    # The paragraph is deliberately explicit about pending results; a completed
    # run requires a new evidence-based editorial pass, never automatic success.
    if lunar_complete.exists():
        lunar_evidence = ROOT / "research/evidence/lunar_onpolicy_specialist_v1.json"
        if not lunar_evidence.exists():
            raise ValueError("Lunar completed: audit and editorial update required")
        lunar = json.loads(lunar_evidence.read_text())
        if not lunar["final_specialist_gate_pass"] or lunar["training_interactions"] != 4000000:
            raise ValueError("Lunar final evidence differs from current positive report wording")
        if lunar["audit"] != "source_numeric_budget_and_physics_trace_replay_pass":
            raise ValueError("Lunar physical/numeric audit required")
        for name, expected in lunar["source_sha256"].items():
            if digest(ROOT / name) != expected:
                raise ValueError(f"Lunar source changed: {name}")
        body = (PAPER / "Chapters/Final.tex").read_text()
        for mode in ["sampled", "argmax"]:
            primary = next(r for r in lunar["milestones"][-1]["task"] if r["mode"] == mode and r["profile"] == 0)
            if primary["pad_successes"] != 10 or f"{primary['mean_utility']:.5f}" not in body:
                raise ValueError("Lunar report success/utility differs")
        readiness = "Audited single-seed Lunar outcome included; independent replication pending"
    else:
        readiness = "Lunar final outcome pending; report must retain running-only wording"
    lunar_confirmation = ROOT / "research/evidence/lunar_onpolicy_confirmation_v1.json"
    if lunar_confirmation.exists():
        confirmation = json.loads(lunar_confirmation.read_text())
        if (
            confirmation["audit"] != "source_numeric_budget_and_all_task_physics_replay_pass"
            or not confirmation["all_seed_both_mode_primary_gate_pass"]
            or confirmation["prospective_training_seeds"] != 2
            or confirmation["pilot_included"]
        ):
            raise ValueError("Prospective Lunar confirmation evidence differs")
        for name, expected in confirmation["source"].items():
            if digest(ROOT / name) != expected:
                raise ValueError(f"Lunar confirmation source changed: {name}")
        body = (PAPER / "Chapters/Final.tex").read_text()
        for job in confirmation["jobs"]:
            for cell in job["milestones"][-1]["task"]:
                if cell["profile"] == 0 and (cell["pad_successes"] != 10 or f"{cell['mean_utility']:.5f}" not in body):
                    raise ValueError("Prospective Lunar report success/utility differs")
        readiness = "Audited Lunar pilot and two prospective confirmation seeds included; pilot separate"
    return {
        "status": "deterministic_source_numeric_and_reference_checks_pass",
        "independent_semantic_review": False,
        "full_text_citation_context_audit": False,
        "source_files": {p.relative_to(ROOT).as_posix(): digest(p) for p in files},
        "cited_keys": cited,
        "citation_metadata_status": {key: papers[key]["status"] for key in cited},
        "repository_paths_checked": paths,
        "graphics_checked": graphics,
        "confirmation_evidence_sha256": digest(evidence_path),
        "confirmation_seed_count": 3,
        "lunar_training_budget_planned": lunar_plan["training_interactions"],
        "lunar_editorial_readiness": readiness,
        "final_hand_in_ready": False,
        "remaining": [
            "new final release verification",
            "lecturer rubric/deadline confirmation; independent semantic review not available",
        ],
        "training_interactions": 0,
        "final_test_steps": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--write", type=Path, default=Path("outputs/course-report-review/source-audit.json"))
    args = parser.parse_args()
    result = audit()
    args.write.parent.mkdir(parents=True, exist_ok=True)
    atomic_json(args.write, result)
    print(f"Report checks passed: {len(result['source_files'])} inputs, {len(result['cited_keys'])} citations.")
    print(result["lunar_editorial_readiness"])


if __name__ == "__main__":
    main()

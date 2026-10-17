from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.evaluation.remediation import RemediationError
from src.evaluation.replay_feasibility import (
    _retention_decision,
    _validate_replay_manipulation,
    build_f1_jobs,
    load_f1_plan,
    validate_f1_commands,
)

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "configs/remediations/minecart_pcqn_replay_f1.json"


def load_plan() -> dict:
    return json.loads(PLAN_PATH.read_text(encoding="utf-8"))


def test_f1_plan_binds_authority_sources_firewall_and_six_jobs() -> None:
    plan, plan_hash = load_f1_plan(ROOT, PLAN_PATH)
    jobs = build_f1_jobs(plan)

    assert len(plan_hash) == 64
    assert [(job["cell"], job["seed"]) for job in jobs] == [
        ("A0R0", 20264021),
        ("A1R1", 20264021),
        ("A0R0", 20264022),
        ("A1R1", 20264022),
        ("A0R0", 20264023),
        ("A1R1", 20264023),
    ]
    assert all("test" not in [part.lower() for part in job["command"]] for job in jobs)
    baseline = jobs[0]["command"]
    full = jobs[1]["command"]
    assert "--successful-replay-stratification" not in baseline
    assert "--successful-replay-relabel" not in baseline
    assert "--successful-replay-stratification" in full
    assert "--successful-replay-relabel" in full
    assert plan["conditional_continuation"]["f2_authorized"] is False
    assert plan["conditional_continuation"]["final_test_authorized"] is False


def test_retention_requires_early_pass_and_next_two_checkpoints() -> None:
    rule = load_plan()["qualification"]["pass_rule"]
    passing = [
        {"step": step, "passed": step in {600_000, 700_000, 800_000}} for step in range(100_000, 1_000_001, 100_000)
    ]
    broken = [
        {"step": step, "passed": step in {600_000, 800_000, 900_000}} for step in range(100_000, 1_000_001, 100_000)
    ]
    late = [{"step": step, "passed": step >= 900_000} for step in range(100_000, 1_000_001, 100_000)]

    assert _retention_decision(passing, rule)["status"] == "retained"
    assert _retention_decision(broken, rule)["status"] == "retention_failed"
    assert _retention_decision(late, rule)["status"] == "late_inconclusive"


def test_manipulation_audit_accepts_exact_a1r1_accounting_and_rejects_drift() -> None:
    plan = load_plan()
    updates = plan["qualification"]["training"]["expected_gradient_updates"]
    replay_audit = {
        "completed_trajectories": 10,
        "eligible_trajectories": 2,
        "eligible_transitions": 20,
        "success_positions_requested": updates * 32,
        "success_positions_sampled": updates * 32 - 64,
        "uniform_positions_sampled": updates * 32 + 64,
        "fallback_positions": 64,
        "relabel_attempt_positions": updates * 32,
        "relabel_changed_positions": 80,
        "live_eligible_trajectory_count": 2,
        "projection_distance_sum": 0.1,
        "projection_distance_max": 0.1,
    }

    _validate_replay_manipulation(plan, {"cell": "A1R1", "job_id": "job"}, replay_audit)
    replay_audit["success_positions_requested"] -= 1
    with pytest.raises(RemediationError, match="requested success-position"):
        _validate_replay_manipulation(plan, {"cell": "A1R1", "job_id": "job"}, replay_audit)


@pytest.mark.parametrize(
    "flag,value", [("--lr", "0.03"), ("--total-timesteps", "1000001"), ("--protocol", "other.json")]
)
def test_prelaunch_command_validation_rejects_drift(flag, value):
    plan = load_plan()
    jobs = build_f1_jobs(plan)
    jobs[0]["command"][jobs[0]["command"].index(flag) + 1] = value
    protocol = json.loads((ROOT / plan["environment"]["protocol"]).read_text())
    with pytest.raises(RemediationError, match=r"mismatch|drift"):
        validate_f1_commands(plan, jobs, protocol)


def test_duplicate_seed_and_baseline_intervention_are_rejected():
    plan = load_plan()
    plan["qualification"]["seeds"] = [20264021] * 3
    with pytest.raises(RemediationError, match="seeds"):
        build_f1_jobs(plan)
    plan = load_plan()
    jobs = build_f1_jobs(plan)
    jobs[0]["command"].append("--successful-replay-relabel")
    protocol = json.loads((ROOT / plan["environment"]["protocol"]).read_text())
    with pytest.raises(RemediationError, match="successful_replay_relabel"):
        validate_f1_commands(plan, jobs, protocol)

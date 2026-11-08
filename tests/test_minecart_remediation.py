from __future__ import annotations

import hashlib
import json
from pathlib import Path

from src.evaluation.protocol import protocol_hash
from src.evaluation.remediation import build_qualification_jobs, load_qualification_plan

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def sha256(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def test_remediation_is_validation_only_and_not_authorized() -> None:
    plan = load_json("configs/remediations/minecart_pcqn_backbone_v1.json")
    firewall = plan["data_firewall"]

    assert plan["status"] == "predeclared_not_executed"
    assert plan["execution_authorized"] is False
    assert firewall["evaluation_split"] == "validation"
    assert firewall["forbidden_split"] == "test"
    assert firewall["final_test_access_permitted"] is False
    assert plan["environment"]["reward_semantics_changed"] is False


def test_remediation_uses_fresh_seeds_and_a_common_fixed_bundle() -> None:
    plan = load_json("configs/remediations/minecart_pcqn_backbone_v1.json")
    study = load_json("configs/experiments/course_paired_matrix_v1.json")
    pilot_v1 = load_json("configs/pilots/calibration_v1.json")
    pilot_v2 = load_json("configs/pilots/calibration_v2.json")
    qualification = plan["qualification"]
    remediation_seeds = set(qualification["seeds"])

    assert remediation_seeds.isdisjoint(study["paired_seeds"])
    assert remediation_seeds.isdisjoint(pilot_v1["seeds"])
    assert remediation_seeds.isdisjoint(pilot_v2["seeds"])
    assert qualification["method"] == "uniform-pcqn"
    assert qualification["training"]["total_timesteps"] == 1_000_000
    assert qualification["training"]["train_frequency"] == 1
    assert qualification["training"]["buffer_capacity"] == 1_000_000
    assert qualification["training"]["epsilon_decay_steps"] == 500_000
    assert qualification["training"]["expected_gradient_updates"] == 995_001
    assert qualification["pass_rule"]["minimum_positive_episodes_per_objective"] == 8
    assert qualification["pass_rule"]["minimum_distinct_positive_values_per_objective"] == 2
    assert "test" not in qualification["command_template"]
    assert plan["course_revision_after_pass"]["minecart_pcqn_jobs_to_rerun"] == (
        len(study["pcqn_arms"]) * len(study["paired_seeds"])
    )


def test_remediation_binds_protocol_diagnosis_and_execution_block() -> None:
    plan_path = "configs/remediations/minecart_pcqn_backbone_v1.json"
    diagnosis_path = "research/evidence/minecart_validation_diagnosis_v1.json"
    plan = load_json(plan_path)
    diagnosis = load_json(diagnosis_path)
    protocol = load_json("configs/protocols/course_minecart_v0.json")
    gate = load_json("research/qualification/course_matrix_post_validation_gate_v1.json")

    assert protocol_hash(protocol) == plan["environment"]["protocol_canonical_sha256"]
    assert diagnosis["final_test_accessed"] is False
    assert diagnosis["primary_validation"]["episodes"] == 14_400
    assert diagnosis["training_archive_audit"]["selected_checkpoints_with_positive_ore"] == 15
    assert diagnosis["post_hoc_policy_probe"]["mine_action_count"] == 0
    assert plan["diagnosis_sha256"] == sha256(diagnosis_path)
    assert gate["status"] == "blocked"
    assert gate["unlocks_additional_course_execution"] is False
    assert gate["unlocks_final_test"] is False
    assert gate["diagnosis"]["sha256"] == sha256(diagnosis_path)
    assert gate["remediation"]["sha256"] == sha256(plan_path)


def test_remediation_v2_is_single_factor_and_still_fail_closed() -> None:
    plan = load_json("configs/remediations/minecart_pcqn_backbone_v2.json")
    v1 = load_json("configs/remediations/minecart_pcqn_backbone_v1.json")
    intervention = plan["intervention"]
    qualification = plan["qualification"]

    assert plan["status"] == "predeclared_not_executed"
    assert plan["execution_authorized"] is False
    assert plan["data_firewall"]["evaluation_split"] == "validation"
    assert plan["data_firewall"]["final_test_access_permitted"] is False
    assert intervention["single_factor_relative_to_v1"] is True
    assert intervention["priority_alpha"] == 0.6
    assert intervention["importance_sampling_beta_start"] == 0.4
    assert intervention["importance_sampling_beta_end"] == 1.0
    assert "Huber" in intervention["loss_weighting"]
    assert "squared-TD" not in intervention["loss_weighting"]
    assert plan["pre_execution_amendments"][0]["execution_state"].startswith("No remediation-v2")
    assert qualification["changes_from_remediation_v1"] == {
        "replay_sampling": {"from": "uniform", "to": "proportional_prioritized"}
    }
    assert qualification["training"] == v1["qualification"]["training"]
    assert qualification["evaluation"] == v1["qualification"]["evaluation"]
    assert qualification["pass_rule"] == v1["qualification"]["pass_rule"]
    assert set(qualification["seeds"]).isdisjoint(v1["qualification"]["seeds"])
    assert "--replay-sampling" in qualification["command_template"]
    assert "--priority-alpha" in qualification["command_template"]
    assert "test" not in qualification["command_template"]


def test_remediation_v2_binds_failed_v1_and_behavior_diagnosis() -> None:
    plan = load_json("configs/remediations/minecart_pcqn_backbone_v2.json")
    qualification = load_json(plan["sources"]["v1_qualification"]["path"])
    diagnosis = load_json(plan["sources"]["v1_behavior_diagnosis"]["path"])

    assert plan["sources"]["v1_qualification"]["sha256"] == sha256(plan["sources"]["v1_qualification"]["path"])
    assert plan["sources"]["v1_behavior_diagnosis"]["sha256"] == sha256(
        plan["sources"]["v1_behavior_diagnosis"]["path"]
    )
    assert qualification["passed"] is False
    assert diagnosis["mechanism_assessment"]["leading_v2_mechanism"] == "prioritized_replay"
    assert diagnosis["unlocks_matrix_v1"] is False
    assert diagnosis["unlocks_final_test"] is False


def test_remediation_v2_loads_with_bound_sources_and_exact_per_command() -> None:
    plan_path = ROOT / "configs/remediations/minecart_pcqn_backbone_v2.json"

    plan, plan_sha256 = load_qualification_plan(ROOT, plan_path)
    jobs = build_qualification_jobs(plan)

    assert plan_sha256 == sha256("configs/remediations/minecart_pcqn_backbone_v2.json")
    assert [job["seed"] for job in jobs] == [20264011, 20264012, 20264013]
    command = jobs[0]["command"]
    for flag, value in (
        ("--replay-sampling", "prioritized"),
        ("--priority-alpha", "0.6"),
        ("--priority-beta-start", "0.4"),
        ("--priority-beta-end", "1.0"),
        ("--priority-epsilon", "0.000001"),
    ):
        assert command[command.index(flag) + 1] == value

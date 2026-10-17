from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from src.evaluation.calibration import (
    calibration_plan_hash,
    calibration_source_type,
    load_calibration_plan,
    propose_calibration,
    reference_points_hash,
    validate_calibration_artifact,
    validate_calibration_plan,
    validate_reference_front_artifact,
)
from src.evaluation.pilot import build_pilot_jobs, pilot_manifest


def make_plan() -> dict:
    return {
        "schema_version": 1,
        "status": "predeclared",
        "source_split": "validation",
        "method": "uniform-pcqn",
        "seeds": [101, 102, 103],
        "training": {
            "total_timesteps": 100_000,
            "learning_starts": 5_000,
            "train_freq": 4,
            "batch_size": 64,
            "buffer_capacity": 200_000,
        },
        "evaluation": {"episodes_per_preference": 5, "seed_base": 270_000, "shift": "nominal"},
        "calibration_rule": {
            "return_field": "episode_returns",
            "scale_abs_quantile": 0.95,
            "magnitude_floor": 1e-6,
            "reference_span_quantiles": [0.05, 0.95],
            "reference_margin_fraction": 0.05,
            "reference_minimum_margin": 0.01,
        },
        "smoke": {"total_timesteps": 20, "learning_starts": 21, "episodes_per_preference": 1},
        "environments": [
            {"env_id": "env-a", "protocol": "configs/protocols/a.json"},
            {"env_id": "env-b", "protocol": "configs/protocols/b.json"},
        ],
    }


def test_repository_calibration_plan_is_valid() -> None:
    plan = load_calibration_plan("configs/pilots/calibration_v1.json")
    assert plan["source_split"] == "validation"
    assert [environment["env_id"] for environment in plan["environments"]] == [
        "mo-lunar-lander-v3",
        "minecart-v0",
    ]


def test_repository_v2_plan_uses_source_appropriate_evidence() -> None:
    plan = load_calibration_plan("configs/pilots/calibration_v2.json")

    assert plan["schema_version"] == 2
    assert [calibration_source_type(environment) for environment in plan["environments"]] == [
        "validation_pilot",
        "environment_reference_front",
    ]


def test_calibration_proposes_scales_and_strictly_dominated_reference() -> None:
    returns = np.array(
        [
            [-100.0, 2.0],
            [-50.0, 4.0],
            [25.0, 8.0],
            [100.0, 16.0],
        ]
    )
    proposal = propose_calibration(returns, make_plan()["calibration_rule"])
    scale = np.asarray(proposal["proposed_reward_scale"])
    reference = np.asarray(proposal["proposed_reference_point"])
    scaled = returns * scale

    assert np.allclose(np.quantile(np.abs(scaled), 0.95, axis=0), 1.0)
    assert np.all(scaled > reference)
    assert proposal["reference_strictly_dominated_by_all_pilot_returns"] is True


def test_calibration_plan_rejects_test_split() -> None:
    plan = make_plan()
    plan["source_split"] = "test"
    with pytest.raises(ValueError, match="validation split"):
        validate_calibration_plan(plan)


def test_degenerate_objective_blocks_pilot_but_is_recorded_for_smoke() -> None:
    returns = np.array([[0.0, -2.0], [0.0, -1.0]])
    rule = make_plan()["calibration_rule"]
    with pytest.raises(ValueError, match=r"Objectives \[0\]"):
        propose_calibration(returns, rule)

    proposal = propose_calibration(returns, rule, allow_degenerate=True)
    assert proposal["degenerate_objectives"] == [0]
    assert proposal["proposed_reward_scale"][0] == 1.0


def test_calibration_artifact_rejects_test_data_and_nonidentity_scale() -> None:
    artifact = {
        "split": "test",
        "shift": "nominal",
        "protocol": {"env_id": "env-a", "reward_dim": 2, "reward_scale": [1.0, 1.0]},
        "provenance": {"config": {"protocol_sha256": "abc", "seed": 7}},
        "episode_returns": [[[1.0, 2.0]]],
    }
    with pytest.raises(ValueError, match="never test"):
        validate_calibration_artifact(
            artifact,
            expected_env_id="env-a",
            expected_protocol_sha256="abc",
            expected_seed=7,
            return_field="episode_returns",
        )

    artifact["split"] = "validation"
    artifact["protocol"]["reward_scale"] = [0.5, 1.0]
    with pytest.raises(ValueError, match="identity reward_scale"):
        validate_calibration_artifact(
            artifact,
            expected_env_id="env-a",
            expected_protocol_sha256="abc",
            expected_seed=7,
            return_field="episode_returns",
        )


def test_pilot_jobs_match_plan_and_smoke_is_not_freeze_evidence() -> None:
    plan = make_plan()
    jobs = build_pilot_jobs(
        plan,
        output_dir="artifacts/pilot",
        python_executable="python3.11",
        device="cpu",
        smoke=False,
    )
    smoke_jobs = build_pilot_jobs(
        plan,
        output_dir="artifacts/smoke",
        python_executable="python3.11",
        device="cpu",
        smoke=True,
    )

    assert len(jobs) == 6
    assert len(smoke_jobs) == 2
    assert all(job["training_interaction_budget"] == 100_000 for job in jobs)
    assert all(job["training_interaction_budget"] == 20 for job in smoke_jobs)
    assert all("validation" in job["evaluation_command"] for job in jobs)
    assert all("test" not in job["evaluation_command"] for job in jobs)

    manifest = pilot_manifest(
        plan,
        smoke_jobs,
        plan_path="configs/pilots/calibration_v1.json",
        smoke=True,
        provenance={},
    )
    assert manifest["mode"] == "smoke"
    assert manifest["eligible_for_freeze_evidence"] is False
    assert manifest["plan_sha256"] == calibration_plan_hash(plan)


def test_v2_pilot_jobs_include_only_validation_pilot_environments() -> None:
    plan = load_calibration_plan("configs/pilots/calibration_v2.json")

    jobs = build_pilot_jobs(
        plan,
        output_dir="artifacts/pilot-v2",
        python_executable="python3.11",
        device="cpu",
        smoke=False,
    )

    assert len(jobs) == 3
    assert {job["env_id"] for job in jobs} == {"mo-lunar-lander-v3"}
    assert {job["training_seed"] for job in jobs} == set(plan["seeds"])


def test_reference_front_artifact_validates_hashes_and_rejects_tampering() -> None:
    points = np.array([[0.0, -1.0], [1.0, -2.0]])
    source = {
        "type": "environment_reference_front",
        "generator": "pareto_front",
        "gamma": 0.99,
        "symmetric": True,
        "package": {"name": "example-package", "version": "1.2.3"},
        "environment_config_sha256": "a" * 64,
        "determinism_seeds": [1, 2],
    }
    artifact = {
        "schema_version": 1,
        "kind": "environment_reference_front",
        "env_id": "env-a",
        "reward_dim": 2,
        "return_definition": {"type": "discounted", "gamma": 0.99},
        "generator": {
            "name": "pareto_front",
            "symmetric": True,
            "package": {"name": "example-package", "version": "1.2.3"},
            "environment_config_sha256": "a" * 64,
            "determinism_seeds": [1, 2],
            "deterministic_across_seeds": True,
        },
        "plan_sha256": "b" * 64,
        "protocol_sha256": "c" * 64,
        "points": points.tolist(),
        "points_sha256": reference_points_hash(points),
        "provenance": {},
    }

    validated = validate_reference_front_artifact(
        artifact,
        expected_env_id="env-a",
        expected_reward_dim=2,
        expected_gamma=0.99,
        expected_plan_sha256="b" * 64,
        expected_protocol_sha256="c" * 64,
        expected_source=source,
    )
    assert np.array_equal(validated, points)

    artifact["points"][0][0] = 0.5
    with pytest.raises(ValueError, match="points hash"):
        validate_reference_front_artifact(
            artifact,
            expected_env_id="env-a",
            expected_reward_dim=2,
            expected_gamma=0.99,
            expected_plan_sha256="b" * 64,
            expected_protocol_sha256="c" * 64,
            expected_source=source,
        )


def test_repository_minecart_front_matches_v2_plan_and_is_non_degenerate() -> None:
    plan = load_calibration_plan("configs/pilots/calibration_v2.json")
    environment = next(item for item in plan["environments"] if item["env_id"] == "minecart-v0")
    source = environment["calibration_source"]
    artifact = json.loads(Path(source["artifact"]).read_text(encoding="utf-8"))
    proposal = json.loads(Path("research/calibration/course_calibration_v2_proposal.json").read_text(encoding="utf-8"))

    points = validate_reference_front_artifact(
        artifact,
        expected_env_id="minecart-v0",
        expected_reward_dim=3,
        expected_gamma=0.99,
        expected_plan_sha256=calibration_plan_hash(plan),
        expected_protocol_sha256=proposal["environments"]["minecart-v0"]["protocol_sha256"],
        expected_source=source,
    )
    proposal = propose_calibration(points, plan["calibration_rule"])

    assert points.shape == (20, 3)
    assert proposal["degenerate_objectives"] == []


def test_frozen_course_protocols_match_the_versioned_v2_proposal() -> None:
    plan_path = "configs/pilots/calibration_v2.json"
    proposal_path = "research/calibration/course_calibration_v2_proposal.json"
    plan = load_calibration_plan(plan_path)
    proposal_bytes = Path(proposal_path).read_bytes()
    proposal_sha256 = hashlib.sha256(proposal_bytes).hexdigest()
    proposal = json.loads(proposal_bytes)

    assert proposal["status"] == "review_required"
    assert proposal["eligible_for_freeze_review"] is True
    for environment in plan["environments"]:
        env_id = environment["env_id"]
        protocol = json.loads(Path(environment["protocol"]).read_text(encoding="utf-8"))
        proposed = proposal["environments"][env_id]
        evidence = protocol["calibration_evidence"]

        assert protocol["reference_point_status"] == "frozen_from_source_aware_calibration_v2"
        assert np.allclose(protocol["reward_scale"], proposed["proposed_reward_scale"])
        assert np.allclose(protocol["reference_point"], proposed["proposed_reference_point"])
        assert evidence == {
            "plan": plan_path,
            "plan_canonical_sha256": calibration_plan_hash(plan),
            "proposal": proposal_path,
            "proposal_sha256": proposal_sha256,
            "source_type": proposed["source_type"],
        }

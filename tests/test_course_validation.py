from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.evaluation.course_validation import (
    CourseValidationError,
    ValidationExpectation,
    build_checkpoint_lock_decision,
    evaluate_or_reuse,
    select_checkpoint,
    validate_validation_artifact,
)


def make_expectation() -> ValidationExpectation:
    return ValidationExpectation(
        study_id="study-v1",
        job_id="env__full__seed7",
        environment="env",
        arm="full",
        training_seed=7,
        checkpoint_step=50,
        checkpoint_path="artifacts/run/checkpoint_step50.pt",
        checkpoint_sha256="a" * 64,
        protocol_path="configs/protocols/env.json",
        protocol_sha256="b" * 64,
        preference_sha256="a666c95f0822c64e01580063e9bb27c629d4d0534e3163a9611738599f97df2a",
        discount_factor=0.99,
        reward_scale=(1.0, 1.0),
        reference_point=(-1.0, -1.0),
        reward_dim=2,
        preference_count=2,
        episodes_per_preference=2,
        evaluation_seed=20_000,
        training_interaction_budget=100,
        expected_counters={
            "training_interactions": 50,
            "gradient_updates": 10,
            "curriculum_evaluation_steps": 12,
            "validation_evaluation_steps": 14,
        },
    )


def make_artifact() -> dict:
    return {
        "schema_version": 1,
        "kind": "course_validation_checkpoint_evidence",
        "study_id": "study-v1",
        "job_id": "env__full__seed7",
        "environment": "env",
        "arm": "full",
        "training_seed": 7,
        "checkpoint": {
            "path": "artifacts/run/checkpoint_step50.pt",
            "step": 50,
            "sha256": "a" * 64,
        },
        "protocol": {
            "path": "configs/protocols/env.json",
            "sha256": "b" * 64,
            "return_definition": {"type": "discounted", "gamma": 0.99},
            "reward_scale": [1.0, 1.0],
            "reference_point": [-1.0, -1.0],
        },
        "evaluation": {
            "split": "validation",
            "shift": "nominal",
            "seed": 20_000,
            "episodes_per_preference": 2,
            "evaluation_steps": 8,
        },
        "budget": {
            "training_interaction_budget": 100,
            "checkpoint_counters": {
                "training_interactions": 50,
                "gradient_updates": 10,
                "curriculum_evaluation_steps": 12,
                "validation_evaluation_steps": 14,
            },
        },
        "preferences": [
            {"id": "validation-000", "weights": [1.0, 0.0]},
            {"id": "validation-001", "weights": [0.0, 1.0]},
        ],
        "discounted_episode_returns": [
            [[1.0, 0.0], [2.0, 0.0]],
            [[0.0, 3.0], [0.0, 4.0]],
        ],
        "raw_episode_returns": [
            [[2.0, 0.0], [3.0, 0.0]],
            [[0.0, 4.0], [0.0, 5.0]],
        ],
        "episode_lengths": [[2, 2], [2, 2]],
        "metrics": {"hypervolume": 6.0, "expected_utility": 2.5},
        "diagnostics": {
            "missing_values": 0,
            "non_finite_values": 0,
            "degenerate_objectives": [],
        },
    }


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda value: value["evaluation"].update(split="test"), "validation split"),
        (lambda value: value["evaluation"].update(shift="heavy_gravity"), "nominal shift"),
        (
            lambda value: value["discounted_episode_returns"][0][0].__setitem__(0, float("nan")),
            "finite",
        ),
        (lambda value: value["checkpoint"].update(sha256="c" * 64), "checkpoint hash"),
        (
            lambda value: value["budget"].update(training_interaction_budget=101),
            "training budget",
        ),
        (lambda value: value["metrics"].update(hypervolume=7.0), "hypervolume"),
        (lambda value: value["preferences"][0].update(weights=[0.5, 0.5]), "preference matrix"),
    ],
)
def test_validation_artifact_fails_closed(mutation, message: str) -> None:
    artifact = make_artifact()
    mutation(artifact)

    with pytest.raises(CourseValidationError, match=message):
        validate_validation_artifact(artifact, make_expectation())


def test_checkpoint_selection_uses_frozen_lexicographic_rule() -> None:
    candidates = [
        {"step": 50, "hypervolume": 2.0, "expected_utility": 0.1},
        {"step": 100, "hypervolume": 2.0, "expected_utility": 0.2},
        {"step": 150, "hypervolume": 2.0, "expected_utility": 0.2},
        {"step": 200, "hypervolume": 1.9, "expected_utility": 100.0},
    ]

    selected = select_checkpoint(candidates)

    assert selected["step"] == 100


def test_evaluate_or_reuse_is_atomic_and_hash_validated(tmp_path: Path) -> None:
    destination = tmp_path / "evidence.json"
    calls = 0

    def evaluator() -> dict:
        nonlocal calls
        calls += 1
        return make_artifact()

    first, first_hash, reused = evaluate_or_reuse(destination, make_expectation(), evaluator)
    second, second_hash, reused_second = evaluate_or_reuse(destination, make_expectation(), evaluator)

    assert first == second
    assert first_hash == second_hash
    assert reused is False
    assert reused_second is True
    assert calls == 1
    assert not destination.with_suffix(".json.tmp").exists()

    tampered = json.loads(destination.read_text(encoding="utf-8"))
    tampered["checkpoint"]["sha256"] = "d" * 64
    destination.write_text(json.dumps(tampered), encoding="utf-8")
    with pytest.raises(CourseValidationError, match="checkpoint hash"):
        evaluate_or_reuse(destination, make_expectation(), evaluator)


def test_selected_checkpoint_cannot_be_degenerate() -> None:
    artifact = make_artifact()
    artifact["discounted_episode_returns"][0] = [[0.0, 0.0], [0.0, 0.0]]
    artifact["metrics"]["expected_utility"] = 1.75
    artifact["metrics"]["hypervolume"] = 4.5
    artifact["diagnostics"]["degenerate_objectives"] = [0]

    with pytest.raises(CourseValidationError, match="degenerate"):
        validate_validation_artifact(artifact, make_expectation(), require_non_degenerate=True)


def test_lock_decision_blocks_all_locks_when_any_run_is_degenerate() -> None:
    proposed = [
        {"job_id": "env__full__seed1", "checkpoint_step": 50, "eligible_for_lock": True},
        {"job_id": "env__full__seed2", "checkpoint_step": 100, "eligible_for_lock": False},
    ]
    blockers = [
        {
            "job_id": "env__full__seed2",
            "trajectory_degenerate_objectives": [0],
            "selected_degenerate_objectives": [0],
        }
    ]

    decision = build_checkpoint_lock_decision("study-v1", proposed, blockers)

    assert decision["status"] == "blocked"
    assert decision["lock_count"] == 0
    assert decision["locks"] == []
    assert decision["diagnostic_selections"] == proposed
    assert decision["unlocks_final_test"] is False

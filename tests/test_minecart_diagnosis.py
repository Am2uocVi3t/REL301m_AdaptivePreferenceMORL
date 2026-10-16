from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from src.evaluation.minecart_diagnosis import (
    MinecartDiagnosisError,
    aggregate_episode_summaries,
    build_mechanism_assessment,
    load_diagnosis_plan,
    summarize_episode,
)

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "configs/diagnostics/minecart_remediation_v1_behavior.json"


def test_plan_is_validation_only_and_hash_bound() -> None:
    plan, plan_hash = load_diagnosis_plan(ROOT, PLAN_PATH)

    assert len(plan_hash) == 64
    assert plan["data_firewall"]["evaluation_split"] == "validation"
    assert plan["data_firewall"]["training_permitted"] is False
    assert plan["data_firewall"]["final_test_access_permitted"] is False
    assert plan["evaluation"]["episode_count_per_checkpoint"] == 160
    assert len(plan["evaluation"]["checkpoints"]) == 7
    assert {record["training_seed"] for record in plan["evaluation"]["checkpoints"]} == {
        20264001,
        20264002,
        20264003,
    }


def test_plan_rejects_source_hash_drift(tmp_path: Path) -> None:
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    plan["sources"]["qualification"]["sha256"] = "0" * 64
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")

    with pytest.raises(MinecartDiagnosisError, match="qualification source hash mismatch"):
        load_diagnosis_plan(ROOT, plan_path)


def test_episode_summary_distinguishes_mining_from_delivery() -> None:
    rewards = np.zeros((3, 3), dtype=np.float32)
    episode = summarize_episode(
        actions=[3, 0, 2],
        departed_flags=[True, True, True],
        cargo_before=[0.0, 0.0, 0.4],
        cargo_after=[0.0, 0.4, 0.4],
        rewards=rewards,
        terminated=False,
        truncated=True,
        action_count=6,
        mine_action=0,
        ore_objective_indices=[0, 1],
    )

    assert episode["used_mine_action"] is True
    assert episode["successful_mining"] is True
    assert episode["ore_delivery"] is False
    assert episode["cargo_but_no_delivery"] is True
    assert episode["truncated"] is True


def test_aggregate_and_mechanism_assessment_detect_behavior_loss() -> None:
    positive = {
        "action_counts": [2, 0, 0, 3, 0, 0],
        "departed": True,
        "used_mine_action": True,
        "successful_mining": True,
        "ore_delivery": True,
        "cargo_but_no_delivery": False,
        "terminated_at_base": True,
        "truncated": False,
        "positive_ore_objectives": [True, True],
        "length": 5,
    }
    aggregate = aggregate_episode_summaries([positive], action_count=6, ore_objective_count=2)
    assessment = build_mechanism_assessment(
        [
            {"training_seed": 7, "step": 100, **aggregate},
            {
                "training_seed": 7,
                "step": 200,
                **{**aggregate, "episodes_with_ore_delivery": 0},
            },
        ]
    )

    assert aggregate["positive_ore_episodes_per_objective"] == [1, 1]
    assert assessment["delivery_lost_after_positive_within_seed"] is True
    assert assessment["leading_v2_mechanism"] == "prioritized_replay"

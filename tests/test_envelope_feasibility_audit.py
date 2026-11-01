from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import torch

from scripts.analyze_envelope_feasibility import audit, sha
from src.evaluation.metrics import compute_expected_utility, compute_hypervolume
from src.evaluation.protocol import protocol_hash
from src.utils.provenance import write_json


def fixture_cohort(tmp_path: Path) -> tuple[Path, Path]:
    """Synthetic audit fixture, never a scientific result or training witness."""
    protocol = {
        "env_id": "fixture",
        "reward_dim": 3,
        "return_definition": {"gamma": 0.99},
        "reference_point": [0, 0, -3],
        "preference_splits": {"validation": {"values": [[1, 0, 0], [0, 1, 0]]}},
    }
    protocol_path = tmp_path / "protocol.json"
    write_json(protocol_path, protocol)
    plan = {
        "seeds": [1],
        "protocol": str(protocol_path),
        "training_interactions": 100,
        "agent": {"learning_starts": 100, "gradient_updates": 1},
        "validation_checkpoints": [100],
        "episodes_per_preference": 1,
        "evaluation_seed": 77,
        "study_id": "synthetic-audit-fixture",
    }
    plan_path = tmp_path / "plan.json"
    write_json(plan_path, plan)
    root = tmp_path / "outputs"
    directory = root / "seed1"
    directory.mkdir(parents=True)
    model_path = directory / "step100.tar"
    torch.save(
        {
            "q_net_state_dict": {"weight": torch.zeros(1)},
            "q_net_optimizer_state_dict": {"state": {0: {"step": torch.tensor(1.0)}}},
        },
        model_path,
    )
    returns = np.array([[[1.0, 2.0, -1.0]], [[2.0, 1.0, -1.0]]])
    preferences = np.array([[1.0, 0, 0], [0, 1.0, 0]])
    result = {
        "raw_episode_returns": returns,
        "episode_returns": returns,
        "episode_lengths": [[1], [1]],
        "preferences": preferences,
        "split": "validation",
        "evaluation_seed": 77,
        "terminated": [[True], [True]],
        "truncated": [[False], [False]],
        "training_interactions": 100,
        "evaluation_steps": 2,
        "gradient_updates": 1,
        "checkpoint_sha256": sha(model_path),
        "ore_positive_episodes": [2, 2],
        "hypervolume": compute_hypervolume(returns.mean(axis=1), np.array([0, 0, -3])),
        "expected_utility": compute_expected_utility(returns.mean(axis=1), preferences),
    }
    result_path = directory / "validation_step100.json"
    write_json(result_path, result)
    write_json(
        directory / "run_manifest.json",
        {
            "status": "complete",
            "smoke": False,
            "seed": 1,
            "plan_sha256": sha(plan_path),
            "plan": plan,
            "protocol": protocol,
            "protocol_sha256": protocol_hash(protocol),
            "training_interactions": 100,
            "gradient_updates": 1,
            "curriculum_steps": 0,
            "final_test_steps": 0,
            "validation_steps": 2,
            "validation_artifacts": [{"sha256": sha(result_path)}],
        },
    )
    return root, plan_path


def test_audit_checks_complete_cohort_and_rejects_tampered_model(tmp_path: Path) -> None:
    root, plan = fixture_cohort(tmp_path)
    result = audit(root, plan)
    assert result["episodes"] == 2
    assert result["training_interactions"] == 100
    assert result["records"][0]["ore_positive_episodes"] == [2, 2]
    with (root / "seed1/step100.tar").open("ab") as stream:
        stream.write(b"tamper")
    with pytest.raises(ValueError, match="Changed validation or model"):
        audit(root, plan)


def test_audit_rejects_test_access_and_incomplete_jobs(tmp_path: Path) -> None:
    root, plan = fixture_cohort(tmp_path)
    path = root / "seed1/run_manifest.json"
    manifest = json.loads(path.read_text())
    manifest["final_test_steps"] = 1
    write_json(path, manifest)
    with pytest.raises(ValueError, match="identity/budget mismatch"):
        audit(root, plan)
    manifest["final_test_steps"] = 0
    manifest["status"] = "running"
    write_json(path, manifest)
    with pytest.raises(ValueError, match="Incomplete"):
        audit(root, plan)

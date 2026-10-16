from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

from scripts.train import parse_args
from src.evaluation.remediation import (
    RemediationError,
    _validate_qualification_run_config,
    authorize_qualification,
    build_qualification_jobs,
    qualify_seed,
    run_qualification_jobs,
)

ROOT = Path(__file__).resolve().parents[1]


def load_plan() -> dict:
    return json.loads((ROOT / "configs/remediations/minecart_pcqn_backbone_v1.json").read_text(encoding="utf-8"))


def load_v2_plan() -> dict:
    return json.loads((ROOT / "configs/remediations/minecart_pcqn_backbone_v2.json").read_text(encoding="utf-8"))


def test_jobs_are_exactly_the_predeclared_validation_only_runs() -> None:
    plan = load_plan()

    jobs = build_qualification_jobs(plan)

    assert [job["seed"] for job in jobs] == [20264001, 20264002, 20264003]
    assert all(job["command"][:2] == ["python", "scripts/train.py"] for job in jobs)
    assert all("<qualification-seed>" not in job["command"] for job in jobs)
    assert all("test" not in [part.lower() for part in job["command"]] for job in jobs)
    for flag in (
        "--batch-size",
        "--bootstrap-probability",
        "--curriculum-eval-episodes",
        "--curriculum-update-freq",
        "--device",
        "--eps-end",
        "--eps-start",
        "--eval-seed",
        "--gamma",
        "--lr",
        "--num-heads",
        "--target-update-freq",
    ):
        assert flag in jobs[0]["command"]


def test_v2_jobs_are_exactly_the_prioritized_replay_runs() -> None:
    jobs = build_qualification_jobs(load_v2_plan())

    assert [job["seed"] for job in jobs] == [20264011, 20264012, 20264013]
    assert all("--replay-sampling" in job["command"] for job in jobs)
    assert all("test" not in [part.lower() for part in job["command"]] for job in jobs)


def test_v2_auditor_rejects_prioritized_replay_argument_drift(monkeypatch: pytest.MonkeyPatch) -> None:
    plan = load_v2_plan()
    job = build_qualification_jobs(plan)[0]
    protocol = json.loads((ROOT / plan["environment"]["protocol"]).read_text(encoding="utf-8"))
    monkeypatch.setattr(sys, "argv", job["command"][1:])
    config = vars(parse_args()) | {"protocol": protocol}

    _validate_qualification_run_config(config, plan, job, protocol)
    config["priority_beta_end"] = 0.9

    with pytest.raises(RemediationError, match="priority_beta_end mismatch"):
        _validate_qualification_run_config(config, plan, job, protocol)


def test_authorization_requires_exact_acknowledgement_and_bounded_explicit_seeds() -> None:
    plan = load_plan()
    jobs = build_qualification_jobs(plan)

    with pytest.raises(RemediationError, match="exact plan acknowledgement"):
        authorize_qualification(
            plan,
            jobs,
            execute=True,
            acknowledgement="wrong",
            max_seeds=3,
            selectors_used=True,
        )
    with pytest.raises(RemediationError, match="explicit seed selector"):
        authorize_qualification(
            plan,
            jobs,
            execute=True,
            acknowledgement=plan["id"],
            max_seeds=3,
            selectors_used=False,
        )
    with pytest.raises(RemediationError, match="exceeding --max-seeds"):
        authorize_qualification(
            plan,
            jobs,
            execute=True,
            acknowledgement=plan["id"],
            max_seeds=2,
            selectors_used=True,
        )


def test_execution_status_is_resumable_and_hash_verifies_completed_artifact(tmp_path: Path) -> None:
    plan = load_plan()
    jobs = build_qualification_jobs(plan)[:1]
    status_path = tmp_path / "artifacts/status.json"
    calls = 0

    def successful_runner(_command: list[str], root: Path) -> None:
        nonlocal calls
        calls += 1
        artifact = root / jobs[0]["final_artifact"]
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_bytes(b"checkpoint")

    run_qualification_jobs(
        root=tmp_path,
        plan=plan,
        plan_sha256="a" * 64,
        jobs=jobs,
        status_path=status_path,
        run_command=successful_runner,
        retry_failed=False,
        execution_git_commit="abc123",
        python_executable="/python3.11",
    )
    run_qualification_jobs(
        root=tmp_path,
        plan=plan,
        plan_sha256="a" * 64,
        jobs=jobs,
        status_path=status_path,
        run_command=successful_runner,
        retry_failed=False,
        execution_git_commit="abc123",
        python_executable="/python3.11",
    )

    status = json.loads(status_path.read_text(encoding="utf-8"))
    assert calls == 1
    assert status["kind"] == "minecart_backbone_qualification_execution"
    assert status["jobs"][jobs[0]["job_id"]]["status"] == "complete"

    (tmp_path / jobs[0]["final_artifact"]).write_bytes(b"tampered")
    with pytest.raises(RemediationError, match="completed artifact hash mismatch"):
        run_qualification_jobs(
            root=tmp_path,
            plan=plan,
            plan_sha256="a" * 64,
            jobs=jobs,
            status_path=status_path,
            run_command=successful_runner,
            retry_failed=False,
            execution_git_commit="abc123",
            python_executable="/python3.11",
        )


def test_seed_qualification_uses_selected_checkpoint_and_fixed_ore_floor() -> None:
    plan = load_plan()
    candidates = []
    for step, hypervolume in ((100_000, 2.0), (200_000, 3.0)):
        returns = np.zeros((32, 5, 3), dtype=np.float32)
        if step == 200_000:
            returns.reshape(-1, 3)[:8, 0] = np.arange(1, 9, dtype=np.float32)
            returns.reshape(-1, 3)[:8, 1] = np.arange(1, 9, dtype=np.float32)
        candidates.append(
            {
                "step": step,
                "hypervolume": hypervolume,
                "expected_utility": 1.0,
                "discounted_episode_returns": returns.tolist(),
                "artifact": {"path": f"step-{step}.json", "sha256": "b" * 64},
            }
        )

    decision = qualify_seed(20264001, candidates, plan["qualification"]["pass_rule"])

    assert decision["selected_checkpoint"]["step"] == 200_000
    assert decision["passed"] is True
    assert decision["ore_objectives"]["0"]["positive_episode_count"] == 8
    assert decision["ore_objectives"]["1"]["distinct_positive_values"] == 8


def test_seed_qualification_fails_when_one_ore_objective_misses_floor() -> None:
    plan = load_plan()
    returns = np.zeros((32, 5, 3), dtype=np.float32)
    returns.reshape(-1, 3)[:8, 0] = 1.0
    returns.reshape(-1, 3)[:7, 1] = np.arange(1, 8, dtype=np.float32)
    candidate = {
        "step": 100_000,
        "hypervolume": 1.0,
        "expected_utility": 1.0,
        "discounted_episode_returns": returns.tolist(),
        "artifact": {"path": "step.json", "sha256": "c" * 64},
    }

    decision = qualify_seed(20264001, [candidate], plan["qualification"]["pass_rule"])

    assert decision["passed"] is False
    assert decision["ore_objectives"]["1"]["positive_episode_count"] == 7

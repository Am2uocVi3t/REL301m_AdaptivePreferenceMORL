from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from src.evaluation.course_executor import (
    CourseExecutionError,
    authorize_execution,
    load_verified_execution_inputs,
    prepare_smoke_job,
    run_selected_jobs,
    select_jobs,
    verify_manifest_matches_study,
    verify_post_validation_execution_gate,
)
from src.evaluation.course_matrix import build_course_manifest, load_course_study

ROOT = Path(__file__).resolve().parents[1]


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_execution_fixture(root: Path) -> tuple[Path, Path, Path]:
    qualification = root / "research" / "qualification" / "baseline.json"
    write_json(qualification, {"passed": True})
    manifest = root / "research" / "experiments" / "matrix.json"
    write_json(
        manifest,
        {
            "schema_version": 1,
            "study_id": "study-v1",
            "execution_authorized": False,
            "jobs": [
                {
                    "job_id": "env__uniform__seed1",
                    "family": "pcqn",
                    "environment": "env",
                    "arm": "uniform",
                    "seed": 1,
                    "status": "planned",
                    "command": ["python", "scripts/train.py"],
                    "final_artifact": "outputs/uniform.bin",
                },
                {
                    "job_id": "env__full__seed1",
                    "family": "pcqn",
                    "environment": "env",
                    "arm": "full",
                    "seed": 1,
                    "status": "planned",
                    "command": ["python", "scripts/train.py"],
                    "final_artifact": "outputs/full.bin",
                },
            ],
        },
    )
    gates = root / "research" / "qualification" / "gates.json"
    write_json(
        gates,
        {
            "schema_version": 1,
            "matrix_manifest": str(manifest.relative_to(root)),
            "matrix_manifest_sha256": sha256(manifest),
            "execution_authorized": False,
            "gates": {
                "baseline_qualification": {
                    "status": "passed",
                    "artifacts": [{"path": str(qualification.relative_to(root)), "sha256": sha256(qualification)}],
                }
            },
        },
    )
    return manifest, gates, qualification


def test_verified_inputs_reject_manifest_tampering(tmp_path: Path):
    manifest_path, gates_path, _ = make_execution_fixture(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["jobs"][0]["seed"] = 999
    write_json(manifest_path, manifest)

    with pytest.raises(CourseExecutionError, match="manifest hash"):
        load_verified_execution_inputs(tmp_path, manifest_path, gates_path)


def test_verified_inputs_reject_qualification_artifact_tampering(tmp_path: Path):
    manifest_path, gates_path, qualification_path = make_execution_fixture(tmp_path)
    write_json(qualification_path, {"passed": False})

    with pytest.raises(CourseExecutionError, match="qualification artifact hash"):
        load_verified_execution_inputs(tmp_path, manifest_path, gates_path)


def test_selection_and_authorization_require_explicit_bounded_scope(tmp_path: Path):
    manifest_path, gates_path, _ = make_execution_fixture(tmp_path)
    manifest, _ = load_verified_execution_inputs(tmp_path, manifest_path, gates_path)
    selected = select_jobs(manifest, arms={"uniform"})

    assert [job["job_id"] for job in selected] == ["env__uniform__seed1"]
    with pytest.raises(CourseExecutionError, match="exact study acknowledgement"):
        authorize_execution(
            manifest,
            selected,
            execute=True,
            acknowledgement="wrong",
            max_jobs=1,
            selectors_used=True,
            smoke_only=False,
        )
    with pytest.raises(CourseExecutionError, match="explicit selector"):
        authorize_execution(
            manifest,
            selected,
            execute=True,
            acknowledgement="study-v1",
            max_jobs=1,
            selectors_used=False,
            smoke_only=False,
        )


def test_job_status_is_atomic_and_complete_jobs_resume_by_skipping(tmp_path: Path):
    manifest_path, gates_path, _ = make_execution_fixture(tmp_path)
    manifest, gates = load_verified_execution_inputs(tmp_path, manifest_path, gates_path)
    selected = select_jobs(manifest, job_ids={"env__uniform__seed1"})
    status_path = tmp_path / "artifacts" / "status.json"
    calls: list[list[str]] = []

    def successful_runner(command: list[str], cwd: Path) -> None:
        calls.append(command)
        artifact = cwd / selected[0]["final_artifact"]
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_bytes(b"complete")

    first = run_selected_jobs(
        root=tmp_path,
        manifest=manifest,
        gates=gates,
        jobs=selected,
        status_path=status_path,
        run_command=successful_runner,
        retry_failed=False,
        smoke_only=False,
    )
    assert first["jobs"][selected[0]["job_id"]]["status"] == "complete"
    assert not status_path.with_suffix(".json.tmp").exists()

    def forbidden_runner(command: list[str], cwd: Path) -> None:
        raise AssertionError("completed jobs must be skipped")

    second = run_selected_jobs(
        root=tmp_path,
        manifest=manifest,
        gates=gates,
        jobs=selected,
        status_path=status_path,
        run_command=forbidden_runner,
        retry_failed=False,
        smoke_only=False,
    )
    assert second["jobs"][selected[0]["job_id"]]["attempts"] == 1
    assert len(calls) == 1


def test_resume_fails_closed_when_completed_artifact_changes(tmp_path: Path):
    manifest_path, gates_path, _ = make_execution_fixture(tmp_path)
    manifest, gates = load_verified_execution_inputs(tmp_path, manifest_path, gates_path)
    selected = select_jobs(manifest, job_ids={"env__uniform__seed1"})
    status_path = tmp_path / "artifacts" / "status.json"

    def successful_runner(command: list[str], cwd: Path) -> None:
        artifact = cwd / selected[0]["final_artifact"]
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_bytes(b"complete")

    run_selected_jobs(
        root=tmp_path,
        manifest=manifest,
        gates=gates,
        jobs=selected,
        status_path=status_path,
        run_command=successful_runner,
        retry_failed=False,
        smoke_only=False,
    )
    (tmp_path / selected[0]["final_artifact"]).write_bytes(b"tampered")

    with pytest.raises(CourseExecutionError, match="completed artifact hash"):
        run_selected_jobs(
            root=tmp_path,
            manifest=manifest,
            gates=gates,
            jobs=selected,
            status_path=status_path,
            run_command=successful_runner,
            retry_failed=False,
            smoke_only=False,
        )


def test_smoke_job_is_isolated_and_does_not_mutate_frozen_job():
    job = {
        "job_id": "env__uniform__seed1",
        "family": "pcqn",
        "environment": "env",
        "arm": "uniform",
        "seed": 1,
        "command": [
            "python",
            "scripts/train.py",
            "--algo",
            "uniform-pcqn",
            "--total-timesteps",
            "500000",
            "--learning-starts",
            "5000",
            "--output-dir",
            "artifacts/course",
        ],
        "final_artifact": "artifacts/course/uniform-pcqn_env_seed1/final.pt",
    }

    smoke = prepare_smoke_job(job, "artifacts/course-executor-smoke")

    assert smoke["command"][smoke["command"].index("--total-timesteps") + 1] == "20"
    assert smoke["command"][smoke["command"].index("--learning-starts") + 1] == "100"
    assert smoke["command"][smoke["command"].index("--output-dir") + 1] == ("artifacts/course-executor-smoke")
    assert smoke["final_artifact"] == ("artifacts/course-executor-smoke/uniform-pcqn_env_seed1/final.pt")
    assert job["command"][job["command"].index("--total-timesteps") + 1] == "500000"


def test_new_attempt_refuses_untracked_existing_artifact(tmp_path: Path):
    manifest_path, gates_path, _ = make_execution_fixture(tmp_path)
    manifest, gates = load_verified_execution_inputs(tmp_path, manifest_path, gates_path)
    selected = select_jobs(manifest, job_ids={"env__uniform__seed1"})
    artifact = tmp_path / selected[0]["final_artifact"]
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_bytes(b"untracked")

    with pytest.raises(CourseExecutionError, match="untracked final artifact"):
        run_selected_jobs(
            root=tmp_path,
            manifest=manifest,
            gates=gates,
            jobs=selected,
            status_path=tmp_path / "status.json",
            run_command=lambda _command, _cwd: None,
            retry_failed=False,
            smoke_only=False,
        )


def test_manifest_must_match_current_frozen_study_and_protocols():
    config = load_course_study(ROOT / "configs/experiments/course_paired_matrix_v1.json")
    manifest = build_course_manifest(config, ROOT)
    verify_manifest_matches_study(manifest, config, ROOT)
    manifest["jobs"][0]["seed"] = -1

    with pytest.raises(CourseExecutionError, match="current frozen study"):
        verify_manifest_matches_study(manifest, config, ROOT)


def test_post_validation_gate_blocks_course_but_not_smoke(tmp_path: Path):
    gate_path = tmp_path / "research" / "qualification" / "post_validation.json"
    write_json(
        gate_path,
        {
            "schema_version": 1,
            "study_id": "study-v1",
            "status": "blocked",
            "unlocks_additional_course_execution": False,
        },
    )

    with pytest.raises(CourseExecutionError, match="blocks additional course execution"):
        verify_post_validation_execution_gate(
            tmp_path,
            gate_path,
            "study-v1",
            smoke_only=False,
        )
    verify_post_validation_execution_gate(
        tmp_path,
        tmp_path / "missing.json",
        "study-v1",
        smoke_only=True,
    )


def test_passed_post_validation_gate_requires_hashed_qualification(tmp_path: Path):
    qualification = tmp_path / "research" / "qualification" / "remediation.json"
    write_json(qualification, {"passed": True})
    gate_path = tmp_path / "research" / "qualification" / "post_validation.json"
    write_json(
        gate_path,
        {
            "schema_version": 1,
            "study_id": "study-v2",
            "status": "passed",
            "unlocks_additional_course_execution": True,
            "qualification_artifact": {
                "path": str(qualification.relative_to(tmp_path)),
                "sha256": sha256(qualification),
            },
        },
    )

    verify_post_validation_execution_gate(
        tmp_path,
        gate_path,
        "study-v2",
        smoke_only=False,
    )
    write_json(qualification, {"passed": False})
    with pytest.raises(CourseExecutionError, match="qualification artifact hash mismatch"):
        verify_post_validation_execution_gate(
            tmp_path,
            gate_path,
            "study-v2",
            smoke_only=False,
        )

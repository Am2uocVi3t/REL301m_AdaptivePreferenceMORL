from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.evaluation.course_matrix import build_course_manifest, load_course_study, validate_course_study

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs" / "experiments" / "course_paired_matrix_v1.json"


def test_frozen_course_matrix_is_fully_paired_and_non_executing():
    config = load_course_study(CONFIG_PATH)
    manifest = build_course_manifest(config, ROOT)

    expected_jobs = (
        len(config["environments"])
        * len(config["paired_seeds"])
        * (len(config["pcqn_arms"]) + len(config["comparators"]))
    )
    assert manifest["job_count"] == expected_jobs == 150
    assert manifest["execution_authorized"] is False
    assert len({job["job_id"] for job in manifest["jobs"]}) == expected_jobs
    assert all(job["status"] != "complete" for job in manifest["jobs"])
    assert all(job.get("final_artifact") for job in manifest["jobs"])

    pcqn_job = next(job for job in manifest["jobs"] if job["family"] == "pcqn")
    assert pcqn_job["final_artifact"] == (
        f"{pcqn_job['output_root']}/"
        f"{pcqn_job['command'][pcqn_job['command'].index('--algo') + 1]}_"
        f"{pcqn_job['environment']}_seed{pcqn_job['seed']}/final.pt"
    )

    pair_keys = {(job["environment"], job["arm"]) for job in manifest["jobs"]}
    for pair_key in pair_keys:
        seeds = {job["seed"] for job in manifest["jobs"] if (job["environment"], job["arm"]) == pair_key}
        assert seeds == set(config["paired_seeds"])


def test_geometry_only_arm_is_executable_and_isolates_static_geometry():
    config = load_course_study(CONFIG_PATH)
    manifest = build_course_manifest(config, ROOT)
    job = next(job for job in manifest["jobs"] if job["arm"] == "geometry-only")
    command = job["command"]

    assert command[command.index("--geometry-weight") + 1] == "1"
    for flag in ("--gap-weight", "--uncertainty-weight", "--coverage-weight", "--progress-weight"):
        assert command[command.index(flag) + 1] == "0"


def test_course_study_rejects_test_based_checkpoint_selection():
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    config["checkpoint_selection"]["split"] = "test"

    with pytest.raises(ValueError, match="validation only"):
        validate_course_study(config, ROOT)

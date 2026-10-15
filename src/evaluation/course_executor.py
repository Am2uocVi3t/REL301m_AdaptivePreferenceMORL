from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.evaluation.course_matrix import build_course_manifest


class CourseExecutionError(RuntimeError):
    """Raised when a frozen course execution invariant is violated."""


CommandRunner = Callable[[list[str], Path], None]


def verify_manifest_matches_study(
    manifest: dict[str, Any],
    study: dict[str, Any],
    root: Path,
) -> None:
    if manifest != build_course_manifest(study, root):
        raise CourseExecutionError("Versioned manifest does not match the current frozen study or protocol hashes")


def prepare_smoke_job(job: dict[str, Any], output_root: str) -> dict[str, Any]:
    """Return an isolated 20-step copy of one frozen PCQN job."""
    if job.get("family") != "pcqn":
        raise CourseExecutionError("Smoke execution only supports PCQN jobs")
    _validate_relative_path(output_root, "smoke output")
    smoke = deepcopy(job)
    command = smoke.get("command")
    if not isinstance(command, list):
        raise CourseExecutionError("Smoke job command must be a list")
    _replace_flag_value(command, "--total-timesteps", "20")
    _replace_flag_value(command, "--learning-starts", "100")
    _replace_flag_value(command, "--output-dir", output_root)
    algorithm = _flag_value(command, "--algo")
    environment = str(smoke.get("environment", ""))
    seed = smoke.get("seed")
    smoke["command"] = command
    smoke["output_root"] = output_root
    smoke["final_artifact"] = f"{output_root}/{algorithm}_{environment}_seed{seed}/final.pt"
    return smoke


def load_verified_execution_inputs(
    root: Path,
    manifest_path: Path,
    gates_path: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest = _load_json(manifest_path)
    gates = _load_json(gates_path)
    expected_manifest_path = root / str(gates.get("matrix_manifest", ""))
    if expected_manifest_path.resolve() != manifest_path.resolve():
        raise CourseExecutionError("Qualification gates reference a different matrix manifest")
    expected_manifest_hash = gates.get("matrix_manifest_sha256")
    if not isinstance(expected_manifest_hash, str) or _sha256_file(manifest_path) != expected_manifest_hash:
        raise CourseExecutionError("Frozen matrix manifest hash does not match qualification gates")
    if manifest.get("execution_authorized") is not False or gates.get("execution_authorized") is not False:
        raise CourseExecutionError("Frozen inputs must not embed execution authorization")
    if manifest.get("schema_version") != 1 or gates.get("schema_version") != 1:
        raise CourseExecutionError("Unsupported course execution input schema")

    gate_records = gates.get("gates")
    if not isinstance(gate_records, dict) or not gate_records:
        raise CourseExecutionError("Qualification gates are missing")
    for gate_name, gate in gate_records.items():
        if not isinstance(gate, dict) or gate.get("status") != "passed":
            raise CourseExecutionError(f"Qualification gate has not passed: {gate_name}")
        references = list(gate.get("artifacts", []))
        if "artifact" in gate:
            references.append(gate["artifact"])
        for reference in references:
            _verify_qualification_reference(root, reference)
    return manifest, gates


def select_jobs(
    manifest: dict[str, Any],
    *,
    arms: set[str] | None = None,
    environments: set[str] | None = None,
    seeds: set[int] | None = None,
    job_ids: set[str] | None = None,
    families: set[str] | None = None,
) -> list[dict[str, Any]]:
    jobs = manifest.get("jobs")
    if not isinstance(jobs, list):
        raise CourseExecutionError("Matrix manifest jobs must be a list")
    selected = [
        job
        for job in jobs
        if isinstance(job, dict)
        and (not arms or job.get("arm") in arms)
        and (not environments or job.get("environment") in environments)
        and (not seeds or job.get("seed") in seeds)
        and (not job_ids or job.get("job_id") in job_ids)
        and (not families or job.get("family") in families)
    ]
    return selected


def authorize_execution(
    manifest: dict[str, Any],
    jobs: list[dict[str, Any]],
    *,
    execute: bool,
    acknowledgement: str | None,
    max_jobs: int | None,
    selectors_used: bool,
    smoke_only: bool,
) -> bool:
    if not execute:
        return False
    study_id = manifest.get("study_id")
    if acknowledgement != study_id:
        raise CourseExecutionError(f"Execution requires exact study acknowledgement: {study_id}")
    if not selectors_used:
        raise CourseExecutionError("Execution requires at least one explicit selector")
    if not jobs:
        raise CourseExecutionError("Execution selection is empty")
    if max_jobs is None or max_jobs <= 0:
        raise CourseExecutionError("Execution requires an explicit positive --max-jobs")
    if len(jobs) > max_jobs:
        raise CourseExecutionError(f"Selected {len(jobs)} jobs, exceeding --max-jobs={max_jobs}")
    if smoke_only and (len(jobs) != 1 or jobs[0].get("family") != "pcqn"):
        raise CourseExecutionError("Smoke execution requires exactly one PCQN job")
    return True


def run_selected_jobs(
    *,
    root: Path,
    manifest: dict[str, Any],
    gates: dict[str, Any],
    jobs: list[dict[str, Any]],
    status_path: Path,
    run_command: CommandRunner,
    retry_failed: bool,
    smoke_only: bool,
) -> dict[str, Any]:
    manifest_hash = str(gates["matrix_manifest_sha256"])
    status = _load_or_initialize_status(status_path, manifest, manifest_hash, smoke_only)
    records = status["jobs"]

    for job in jobs:
        _validate_job(job)
        job_id = str(job["job_id"])
        record = records.setdefault(job_id, {"status": "planned", "attempts": 0})
        if record["status"] == "complete":
            _verify_completed_artifact(root, job, record)
            continue
        if record["status"] in {"failed", "running"} and not retry_failed:
            raise CourseExecutionError(f"Job {job_id} is {record['status']}; use --retry-failed to retry")

        artifact_path = _resolve_artifact(root, str(job["final_artifact"]))
        if artifact_path.exists():
            raise CourseExecutionError(f"Job {job_id} has an untracked final artifact: {artifact_path}")

        record.update(
            {
                "status": "running",
                "attempts": int(record.get("attempts", 0)) + 1,
                "started_at": _utc_now(),
                "command": job["command"],
                "final_artifact": job["final_artifact"],
            }
        )
        _write_json_atomic(status_path, status)
        try:
            run_command(list(job["command"]), root)
            if not artifact_path.is_file():
                raise CourseExecutionError(f"Job {job_id} completed without final artifact: {artifact_path}")
            record.update(
                {
                    "status": "complete",
                    "completed_at": _utc_now(),
                    "artifact_sha256": _sha256_file(artifact_path),
                }
            )
            record.pop("error", None)
            _write_json_atomic(status_path, status)
        except Exception as error:
            record.update({"status": "failed", "completed_at": _utc_now(), "error": str(error)})
            _write_json_atomic(status_path, status)
            if isinstance(error, CourseExecutionError):
                raise
            raise CourseExecutionError(f"Job {job_id} failed: {error}") from error
    return status


def _load_or_initialize_status(
    path: Path,
    manifest: dict[str, Any],
    manifest_hash: str,
    smoke_only: bool,
) -> dict[str, Any]:
    if path.exists():
        status = _load_json(path)
        if status.get("manifest_sha256") != manifest_hash:
            raise CourseExecutionError("Execution status belongs to a different manifest hash")
        if bool(status.get("smoke_only")) != smoke_only:
            raise CourseExecutionError("Execution status smoke/course mode mismatch")
        if not isinstance(status.get("jobs"), dict):
            raise CourseExecutionError("Execution status jobs must be an object")
        return status
    status = {
        "schema_version": 1,
        "study_id": manifest.get("study_id"),
        "manifest_sha256": manifest_hash,
        "smoke_only": smoke_only,
        "course_evidence": not smoke_only,
        "created_at": _utc_now(),
        "jobs": {},
    }
    _write_json_atomic(path, status)
    return status


def _validate_job(job: dict[str, Any]) -> None:
    command = job.get("command")
    if not isinstance(command, list) or not all(isinstance(part, str) for part in command):
        raise CourseExecutionError(f"Job {job.get('job_id')} has an invalid command")
    if command[:2] not in (["python", "scripts/train.py"], ["python", "scripts/train_baseline.py"]):
        raise CourseExecutionError(f"Job {job.get('job_id')} command is not allowlisted")
    if "--split" in command or any("test" == part.lower() for part in command):
        raise CourseExecutionError(f"Job {job.get('job_id')} attempts to access a test split")
    _validate_relative_path(str(job.get("final_artifact", "")), "final_artifact")


def _verify_qualification_reference(root: Path, reference: Any) -> None:
    if not isinstance(reference, dict):
        raise CourseExecutionError("Qualification artifact reference must be an object")
    relative_path = str(reference.get("path", ""))
    _validate_relative_path(relative_path, "qualification artifact")
    artifact_path = root / relative_path
    expected_hash = reference.get("sha256")
    if (
        not artifact_path.is_file()
        or not isinstance(expected_hash, str)
        or _sha256_file(artifact_path) != expected_hash
    ):
        raise CourseExecutionError(f"qualification artifact hash mismatch: {relative_path}")
    payload = _load_json(artifact_path)
    if payload.get("passed") is not True:
        raise CourseExecutionError(f"Qualification artifact did not pass: {relative_path}")


def _verify_completed_artifact(root: Path, job: dict[str, Any], record: dict[str, Any]) -> None:
    artifact_path = _resolve_artifact(root, str(job["final_artifact"]))
    expected_hash = record.get("artifact_sha256")
    if (
        not artifact_path.is_file()
        or not isinstance(expected_hash, str)
        or _sha256_file(artifact_path) != expected_hash
    ):
        raise CourseExecutionError(f"Job {job['job_id']} completed artifact hash mismatch")


def _resolve_artifact(root: Path, relative_path: str) -> Path:
    _validate_relative_path(relative_path, "final_artifact")
    resolved = (root / relative_path).resolve()
    if root.resolve() not in resolved.parents:
        raise CourseExecutionError("Final artifact escapes the repository root")
    return resolved


def _validate_relative_path(value: str, label: str) -> None:
    path = Path(value)
    if not value or path.is_absolute() or ".." in path.parts:
        raise CourseExecutionError(f"Invalid relative {label} path: {value!r}")


def _flag_value(command: list[str], flag: str) -> str:
    try:
        index = command.index(flag)
        return command[index + 1]
    except (ValueError, IndexError) as error:
        raise CourseExecutionError(f"Command is missing a value for {flag}") from error


def _replace_flag_value(command: list[str], flag: str, value: str) -> None:
    try:
        index = command.index(flag)
        command[index + 1] = value
    except (ValueError, IndexError) as error:
        raise CourseExecutionError(f"Command is missing a value for {flag}") from error


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise CourseExecutionError(f"Cannot load JSON file {path}: {error}") from error
    if not isinstance(value, dict):
        raise CourseExecutionError(f"Expected JSON object: {path}")
    return value


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()

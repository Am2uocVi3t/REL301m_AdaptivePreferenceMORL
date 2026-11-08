#!/home/hei/.cache/rel301m-conda311/bin/python
"""Fail-closed Claude bridge. Offline tests inject executables; production never does."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import select
import signal
import sqlite3
import subprocess
import sys
import tempfile
import time
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path("/home/hei/.local/share/rel301m-aris-setup")
CLI = Path("/home/hei/.local/share/rel301m-claude-runtime/node_modules/.bin/claude")
SECRET = re.compile(
    r"sk-(?:ant-)?[A-Za-z0-9_-]{16,}|-----BEGIN .*PRIVATE KEY-----|"
    r"(?i:api[_-]?key|access[_-]?token|password)\s*[=:]\s*[\"']?[^\s\"']{8,}"
)


def number(value: Any, maximum: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("Numeric metadata required")
    if not math.isfinite(value) or not 0 <= value <= maximum:
        raise ValueError("Numeric metadata outside bounds")
    return float(value)


def scan(text: str) -> None:
    if SECRET.search(text) or "\x00" in text:
        raise ValueError("Review packet contains suspected credentials or binary content")


def packet(root: Path, entries: list[str]) -> tuple[str, str]:
    """Explicit file list only; stage content inline with tools disabled.

    This is a disclosure boundary, not an OS sandbox. The caller must choose
    reviewed public artifacts; heuristic secret scanning cannot prove absence.
    """
    if not entries or len(entries) != len(set(entries)) or len(entries) > 20:
        raise ValueError("Packet requires 1-20 unique allowlisted files")
    chunks = []
    root = root.resolve(strict=True)
    for entry in entries:
        relative = Path(entry)
        if relative.is_absolute() or ".." in relative.parts or not relative.parts:
            raise ValueError("Packet path must be relative without traversal")
        if relative.parts[0] not in {"docs", "research", "src", "scripts", "tests", "configs"}:
            raise ValueError("Packet path outside public artifact roots")
        if any(part.startswith(".") for part in relative.parts) or relative.suffix not in {".md", ".json", ".py"}:
            raise ValueError("Packet file type or hidden path refused")
        # Walk directory descriptors so swapping an ancestor cannot redirect reads.
        parent_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            for part in relative.parts[:-1]:
                next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent_fd)
                os.close(parent_fd)
                parent_fd = next_fd
            fd = os.open(relative.name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=parent_fd)
        except OSError as exc:
            raise ValueError("Packet symlink or invalid path refused") from exc
        finally:
            os.close(parent_fd)
        with os.fdopen(fd, "rb") as source:
            if os.fstat(source.fileno()).st_nlink != 1:
                raise ValueError("Packet hardlink refused")
            content = source.read(100_001)
        if len(content) > 100_000:
            raise ValueError("Packet file too large")
        text = content.decode("utf-8")
        scan(text)
        chunks.append(f"FILE {entry}\n{text}\nEND FILE")
    combined = "\n".join(chunks)
    if len(combined.encode()) > 250_000:
        raise ValueError("Packet too large")
    return combined, hashlib.sha256(combined.encode()).hexdigest()


def metadata(stdout: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """Require a terminal result and preserve provider-reported model usage."""
    try:
        parsed = json.loads(stdout)
    except json.JSONDecodeError:
        parsed = [json.loads(line) for line in stdout.splitlines() if line.strip()]
    events = parsed if isinstance(parsed, list) else [parsed]
    results = [event for event in events if isinstance(event, dict) and event.get("type") == "result"]
    if len(results) != 1:
        raise ValueError("Exactly one terminal result required")
    result = results[0]
    cost = number(result.get("total_cost_usd"), 1_000_000)
    usage, models = result.get("usage"), result.get("modelUsage")
    if not isinstance(usage, dict) or not isinstance(models, dict) or not models:
        raise ValueError("Actual token/model metadata missing")
    for key in ("input_tokens", "output_tokens"):
        value = usage.get(key)
        number(value, 10**12)
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError("Token counts must be integers")
    for name, details in models.items():
        if not isinstance(name, str) or not name.startswith("claude-") or not isinstance(details, dict):
            raise ValueError("Actual model identity missing")
    if not isinstance(result.get("session_id"), str) or not result["session_id"]:
        raise ValueError("Provider session identity missing")
    audit = {
        "actual_cost_usd": cost,
        "usage": usage,
        "model_usage": models,
        "actual_models": sorted(models),
        "session_id": result["session_id"],
        "cost_basis": "provider_cli_report_not_console_reconciled",
    }
    return result, audit


@contextmanager
def ledger(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise ValueError("Ledger symlink refused")
    with sqlite3.connect(path, timeout=10) as db:
        os.chmod(path, 0o600)
        db.execute("PRAGMA synchronous=FULL")
        db.execute(
            "CREATE TABLE IF NOT EXISTS calls (id TEXT PRIMARY KEY, batch TEXT NOT NULL, "
            "reserved REAL NOT NULL, status TEXT NOT NULL, metadata TEXT NOT NULL)"
        )
        db.commit()
        db.execute("BEGIN IMMEDIATE")
        yield db


def reserve(path: Path, policy: dict[str, Any], digest: str) -> str:
    cap = number(policy["max_budget_usd_per_call"], 0.25)
    total = number(policy["batch_budget_usd"], 1)
    calls = policy["max_calls"]
    if not cap or not total or isinstance(calls, bool) or not isinstance(calls, int) or not 1 <= calls <= 4:
        raise ValueError("Invalid bounded batch policy")
    with ledger(path) as db:
        rows = db.execute("SELECT batch, reserved, status FROM calls").fetchall()
        if any(row[2] not in {"complete", "reconciled", "reconciled_aggregate"} for row in rows):
            raise ValueError("Unsettled reservation: inspect live processes and reconcile; never retry blindly")
        selected = [row for row in rows if row[0] == policy["batch_id"]]
        if len(selected) >= calls or sum(row[1] for row in selected) + cap > total + 1e-12:
            raise ValueError("Batch reservation allowance exhausted")
        call_id = uuid.uuid4().hex
        details = {"packet_sha256": digest, "requested_model": policy["model"], "reserved_at": time.time()}
        db.execute(
            "INSERT INTO calls VALUES (?, ?, ?, 'reserved', ?)",
            (call_id, policy["batch_id"], cap, json.dumps(details)),
        )
    return call_id


def record(path: Path, call_id: str, status: str, details: dict[str, Any]) -> None:
    with ledger(path) as db:
        previous = db.execute("SELECT metadata FROM calls WHERE id=?", (call_id,)).fetchone()
        if previous is None:
            raise ValueError("Unknown reservation")
        db.execute(
            "UPDATE calls SET status=?, metadata=? WHERE id=?",
            (status, json.dumps({**json.loads(previous[0]), **details}), call_id),
        )


def import_legacy(root: Path) -> dict[str, Any]:
    """Idempotently preserve old reservations; never mark unknown spend reconciled."""
    source = root / "reserved-calls.txt"
    raw = source.read_bytes()
    lines = raw.decode().splitlines()
    if any(line != "reserved" for line in lines):
        raise ValueError("Malformed legacy ledger")
    digest = hashlib.sha256(raw).hexdigest()
    with ledger(root / "usage.sqlite3") as db:
        existing = db.execute("SELECT id FROM calls WHERE batch='legacy-unreconciled'").fetchall()
        expected = [f"legacy-{digest}-{index}" for index in range(len(lines))]
        if existing and {row[0] for row in existing} != set(expected):
            raise ValueError("Legacy reservation source changed; inspect manually")
        for call_id in expected:
            db.execute(
                "INSERT OR IGNORE INTO calls VALUES (?, 'legacy-unreconciled', 0.25, "
                "'console_reconciliation_required', ?)",
                (call_id, json.dumps({"legacy_source_sha256": digest, "actual_cost_usd": None})),
            )
    return {
        "legacy_reservations": len(lines),
        "reserved_usd": len(lines) * 0.25,
        "legacy_source_sha256": digest,
        "console_reconciled": False,
    }


def check_reconciliation(root: Path, policy: dict[str, Any]) -> None:
    """Verify a separately supplied Console record; never synthesize billing data."""
    evidence = root / "console-reconciliation.json"
    if evidence.is_symlink():
        raise ValueError("Console evidence symlink refused")
    raw = evidence.read_bytes()
    if hashlib.sha256(raw).hexdigest() != policy.get("console_evidence_sha256"):
        raise ValueError("Console evidence hash mismatch")
    report = json.loads(raw)
    if report.get("source") == "user_supplied_console_display":
        reconcile_aggregate(root, report, policy["console_evidence_sha256"])
        return
    if report.get("source") != "anthropic_console_export" or report.get("status") != "reconciled":
        raise ValueError("Historical Console reconciliation required")
    legacy = root / "reserved-calls.txt"
    if legacy.exists():
        imported = import_legacy(root)
        if report.get("legacy_source_sha256") != imported["legacy_source_sha256"]:
            raise ValueError("Console record does not bind historical reservations")
        calls = report.get("calls")
        if not isinstance(calls, list) or len(calls) != imported["legacy_reservations"]:
            raise ValueError("Each legacy reservation needs a Console record")
        with ledger(root / "usage.sqlite3") as db:
            expected = {row[0] for row in db.execute("SELECT id FROM calls WHERE batch='legacy-unreconciled'")}
            if {call.get("reservation_id") for call in calls} != expected:
                raise ValueError("Console reservation mapping mismatch")
            sessions = [call.get("session_id") for call in calls]
            if any(not isinstance(session, str) or not session for session in sessions) or len(set(sessions)) != len(
                calls
            ):
                raise ValueError("Unique historical sessions required")
            for call in calls:
                number(call.get("console_cost_usd"), 1_000_000)
                if not call.get("console_record_id"):
                    raise ValueError("Console source record required")
            for call in calls:
                old = db.execute("SELECT metadata FROM calls WHERE id=?", (call["reservation_id"],)).fetchone()
                db.execute(
                    "UPDATE calls SET status='reconciled', metadata=? WHERE id=?",
                    (
                        json.dumps(
                            {**json.loads(old[0]), **call, "console_evidence_sha256": policy["console_evidence_sha256"]}
                        ),
                        call["reservation_id"],
                    ),
                )


def reconcile_aggregate(root: Path, report: dict[str, Any], digest: str) -> None:
    """Keep rounded Console total at group level; never invent per-call costs."""
    imported = import_legacy(root)
    if (
        report.get("status") != "reconciled_aggregate"
        or report.get("legacy_source_sha256") != imported["legacy_source_sha256"]
    ):
        raise ValueError("Aggregate evidence must bind historical reservations")
    total = number(report.get("console_display_spent_usd"), imported["reserved_usd"])
    if report.get("display_precision_usd") != 0.01 or not report.get("user_statement"):
        raise ValueError("Explicit Console display statement and precision required")
    if report.get("per_invocation_costs_known") is not False:
        raise ValueError("Aggregate evidence cannot claim individual costs")
    with ledger(root / "usage.sqlite3") as db:
        rows = db.execute("SELECT id, metadata FROM calls WHERE batch='legacy-unreconciled'").fetchall()
        ids = report.get("reservation_ids")
        if not isinstance(ids, list) or len(ids) != len(set(ids)) or set(ids) != {row[0] for row in rows}:
            raise ValueError("Aggregate reservation mapping mismatch")
        for call_id, old in rows:
            details = {
                **json.loads(old),
                "console_evidence_sha256": digest,
                "reconciliation_basis": "user_supplied_console_display_aggregate_to_cent",
                "aggregate_group_id": report["group_id"],
                "aggregate_console_spent_usd": total,
                "actual_cost_usd": None,
                "per_invocation_cost_known": False,
            }
            db.execute(
                "UPDATE calls SET status='reconciled_aggregate',metadata=? WHERE id=?", (json.dumps(details), call_id)
            )


def run_process(command: list[str], cwd: Path, timeout: float) -> tuple[int, str, str]:
    """A guardian owns the process group and observes EOF when the wrapper dies.

    Even SIGKILL of the wrapper closes its pipe. A simultaneous kill of the
    guardian or descendants escaping their process group requires OS isolation.
    """
    if not 0 < timeout <= 600:
        raise ValueError("Timeout must be within 600 seconds")

    def interrupted(signum, frame):
        raise InterruptedError(f"Review interrupted by signal {signum}")

    previous = {sig: signal.signal(sig, interrupted) for sig in (signal.SIGTERM, signal.SIGINT)}
    control_read, control_write = os.pipe()
    status_read, status_write = os.pipe()
    guardian = None
    try:
        with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
            guardian = os.fork()
            if guardian == 0:
                os.close(control_write)
                os.close(status_read)
                for sig in previous:
                    signal.signal(sig, signal.SIG_DFL)
                process = None
                outcome: dict[str, Any] = {"error": "guardian_failure"}
                try:
                    process = subprocess.Popen(
                        command,
                        cwd=cwd,
                        stdin=subprocess.DEVNULL,
                        stdout=stdout,
                        stderr=stderr,
                        start_new_session=True,
                    )
                    deadline = time.monotonic() + timeout
                    while True:
                        ready, _, _ = select.select([control_read], [], [], 0.02)
                        if ready and not os.read(control_read, 1):
                            raise InterruptedError("Wrapper exited")
                        if time.monotonic() >= deadline:
                            raise TimeoutError("Review timeout")
                        if os.fstat(stdout.fileno()).st_size + os.fstat(stderr.fileno()).st_size > 2_000_000:
                            raise ValueError("Review output limit exceeded")
                        if process.poll() is not None:
                            outcome = {"returncode": process.returncode}
                            break
                except (OSError, ValueError, TimeoutError, InterruptedError) as exc:
                    outcome = {"error": type(exc).__name__}
                finally:
                    if process is not None:
                        try:
                            os.killpg(process.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                        process.wait(timeout=5)
                    try:
                        os.write(status_write, json.dumps(outcome).encode())
                    except BrokenPipeError:
                        pass
                    os._exit(0)
            os.close(control_read)
            os.close(status_write)
            response = b""
            while chunk := os.read(status_read, 4096):
                response += chunk
            outcome = json.loads(response)
            if outcome.get("error") == "TimeoutError":
                raise TimeoutError("Review timeout; actual spend remains unknown")
            if "error" in outcome:
                raise ValueError(f"Review guardian stopped: {outcome['error']}")
            stdout.seek(0)
            stderr.seek(0)
            return outcome["returncode"], stdout.read(2_000_001).decode(), stderr.read(2_000_001).decode()
    finally:
        os.close(control_write)
        os.close(status_read)
        if guardian:
            os.waitpid(guardian, 0)
        elif guardian is None:
            os.close(control_read)
            os.close(status_write)
        for sig, handler in previous.items():
            signal.signal(sig, handler)


def guarded_command(args: list[str], policy: dict[str, Any]) -> list[str]:
    allowed = {"-p", "--output-format", "--permission-mode", "--model", "--system-prompt", "--tools"}
    values: dict[str, str] = {}
    if len(args) % 2:
        raise ValueError("Flag/value pairs required")
    for key, value in zip(args[::2], args[1::2], strict=True):
        if key not in allowed or key in values:
            raise ValueError("Unsupported/duplicate flag; resume requires a new reviewed packet")
        values[key] = value
    if values.get("--output-format") != "json" or values.get("--permission-mode") != "plan" or not values.get("-p"):
        raise ValueError("JSON print-mode plan review required")
    if values.get("--model", policy["model"]) != policy["model"] or values.get("--tools", ""):
        raise ValueError("Model override and filesystem tools refused; use inline packet")
    for value in values.values():
        scan(value)
    values["--model"] = policy["model"]
    values["--tools"] = ""
    cap = number(policy["max_budget_usd_per_call"], 0.25)
    return [
        str(CLI),
        *[item for pair in values.items() for item in pair],
        "--max-budget-usd",
        str(cap),
        "--safe-mode",
        "--restricted",
        "--strict-mcp-config",
        "--mcp-config",
        '{"mcpServers":{}}',
        "--setting-sources",
        "",
        "--no-session-persistence",
    ]


def execute(root: Path, args: list[str]) -> tuple[int, dict[str, Any]]:
    policy = json.loads((root / "policy.json").read_text())
    if policy.get("enabled") is not True:
        raise ValueError("Paid reviews are disabled")
    # This gate deliberately cannot be met by the historical CLI cost estimates.
    if policy.get("console_reconciled") is not True or not policy.get("console_evidence_sha256"):
        raise ValueError("Historical Console reconciliation required")
    check_reconciliation(root, policy)
    observed = datetime.fromisoformat(policy["quota_observed_at"])
    if observed.tzinfo is None or not 0 <= (datetime.now(UTC) - observed).total_seconds() <= 300:
        raise ValueError("Fresh quota observation required")
    if number(policy["codex_remaining_percent"], 100) < 10:
        raise ValueError("Quota below dispatch floor")
    command = guarded_command(args, policy)
    content, digest = packet(Path(policy["project_root"]), policy["packet_files"])
    if digest != policy["packet_sha256"]:
        raise ValueError("Review packet changed since approval")
    prompt_index = command.index("-p") + 1
    command[prompt_index] += "\n\nPUBLIC REVIEW PACKET\n" + content
    call_id = reserve(root / "usage.sqlite3", policy, digest)
    try:
        # No repository, credentials or remembered sessions in the review cwd.
        with tempfile.TemporaryDirectory(prefix="aris-review-") as directory:
            code, stdout, _stderr = run_process(command, Path(directory), policy["timeout_seconds"])
        result, audit = metadata(stdout)
        status = "complete" if code == 0 and not result.get("is_error") else "failed"
        if audit["actual_cost_usd"] > policy["max_budget_usd_per_call"]:
            status = "over_budget"
        record(root / "usage.sqlite3", call_id, status, audit)
        result["model"] = ",".join(audit["actual_models"])
        result["bridge_call_id"] = call_id
        if status != "complete":
            result["is_error"] = True
        return (0 if status == "complete" else 1), result
    except (OSError, ValueError, TimeoutError, InterruptedError) as exc:
        record(root / "usage.sqlite3", call_id, "unknown_spend", {"failure_type": type(exc).__name__})
        raise


def main() -> int:
    try:
        code, result = execute(ROOT, sys.argv[1:])
    except (OSError, ValueError, KeyError, TypeError, TimeoutError, InterruptedError) as exc:
        print(json.dumps({"is_error": True, "result": str(exc)}))
        return 1
    print(json.dumps(result))
    return code


if __name__ == "__main__":
    raise SystemExit(main())

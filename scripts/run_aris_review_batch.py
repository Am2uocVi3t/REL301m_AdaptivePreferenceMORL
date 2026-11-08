#!/usr/bin/env python3
"""One supervised batch, one review invocation, durable resume and no blind retry."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.aris_review_guard import ROOT as BRIDGE_ROOT
from scripts.aris_review_guard import check_reconciliation, packet
from src.research_harness.aris import preflight
from src.research_harness.store import utc_now, write_registry

PROJECT = Path(__file__).resolve().parents[1]
SPEC_PATH = PROJECT / "configs/aris/batch_20261017.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def calls(bridge: Path, batch_id: str) -> list[tuple]:
    with sqlite3.connect((bridge / "usage.sqlite3").as_uri() + "?mode=ro", uri=True) as db:
        return db.execute("SELECT id,reserved,status,metadata FROM calls WHERE batch=?", (batch_id,)).fetchall()


def rpc(bridge: Path, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    request = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": name, "arguments": arguments}}
    result = subprocess.run(
        ["bash", str(bridge / "start-review-server.sh")],
        input=json.dumps(request) + "\n",
        capture_output=True,
        text=True,
        timeout=45,
        check=True,
    )
    response = json.loads(result.stdout)["result"]
    if response.get("isError"):
        raise ValueError(response["content"][0]["text"])
    return json.loads(response["content"][0]["text"])


def disabled(bridge: Path) -> None:
    policy_path = bridge / "policy.json"
    policy = json.loads(policy_path.read_text())
    policy["enabled"] = False
    write_registry(policy_path, policy)


def step(project: Path, bridge: Path, spec: dict[str, Any], execute: bool) -> dict[str, Any]:
    directory = project / ".aris/batches" / spec["id"]
    directory.mkdir(parents=True, exist_ok=True)
    state_path = directory / "state.json"
    with (directory / "dispatch.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state = (
            json.loads(state_path.read_text())
            if state_path.exists()
            else {
                "batch_id": spec["id"],
                "status": "prepared",
                "created_at": utc_now(),
                "job_id": None,
                "provider_dispatches": 0,
                "scientific_acceptance": False,
            }
        )
        if state["status"] == "complete":
            if len(calls(bridge, spec["id"])) != 1:
                raise ValueError("Completed batch ledger mismatch")
            state["resume_checks"] = state.get("resume_checks", 0) + 1
            write_registry(state_path, state)
            return state
        if state["status"] in {"stopped", "dispatch_intent"}:
            disabled(bridge)
            raise ValueError("Stopped or ambiguous dispatch: inspect state/ledger, never re-dispatch")
        try:
            if state["status"] == "prepared" and execute:
                if spec["maximum_invocations"] != 1 or spec["invocation_budget_usd"] != 0.25:
                    raise ValueError("Only the authorized single-invocation batch is supported")
                quota = json.loads((project / ".aris/preflight.json").read_text())
                report = preflight(
                    project, "evidence-analysis", quota["reported_remaining_percent"], quota["quota_observed_at"]
                )
                if report["status"] != "PASS":
                    raise ValueError("Fresh project preflight required")
                policy = json.loads((bridge / "policy.json").read_text())
                if policy.get("enabled") is not False:
                    raise ValueError("Paid policy must be disabled before bounded dispatch")
                if calls(bridge, spec["id"]):
                    raise ValueError("Existing batch reservation; refusing duplicate dispatch")
                check_reconciliation(bridge, policy)
                with sqlite3.connect((bridge / "usage.sqlite3").as_uri() + "?mode=ro", uri=True) as db:
                    rows = db.execute("SELECT reserved,status FROM calls").fetchall()
                if any(row[1] not in {"complete", "reconciled", "reconciled_aggregate"} for row in rows):
                    raise ValueError("Unsettled spend")
                if sum(row[0] for row in rows) + 0.25 > spec["total_authorized_envelope_usd"]:
                    raise ValueError("Preserved reservations leave insufficient authorized capacity")
                content, digest = packet(project, spec["packet_files"])
                if digest != spec["packet_sha256"] or sha(project / spec["prompt_file"]) != spec["prompt_sha256"]:
                    raise ValueError("Approved packet/prompt drift")
                (directory / "packet.txt").write_text(content)
                state.update(
                    status="dispatch_intent", packet_sha256=digest, dispatch_intent_at=utc_now(), provider_dispatches=1
                )
                write_registry(state_path, state)  # Persist before any provider-triggering action.
                policy.update(
                    enabled=True,
                    batch_id=spec["id"],
                    model=spec["model"],
                    max_calls=1,
                    max_budget_usd_per_call=0.25,
                    batch_budget_usd=0.25,
                    project_root=str(project),
                    packet_files=spec["packet_files"],
                    packet_sha256=digest,
                    timeout_seconds=spec["timeout_seconds"],
                    quota_observed_at=quota["quota_observed_at"],
                    codex_remaining_percent=quota["reported_remaining_percent"],
                )
                write_registry(bridge / "policy.json", policy)
                response = rpc(
                    bridge,
                    "review_start",
                    {"prompt": (project / spec["prompt_file"]).read_text(), "tools": "", "model": spec["model"]},
                )
                state.update(status="running", job_id=response["jobId"], start_response=response)
                write_registry(state_path, state)
            if state["status"] == "running":
                response = rpc(bridge, "review_status", {"jobId": state["job_id"], "waitSeconds": 20})
                state["last_status"] = response
                current = calls(bridge, spec["id"])
                if current:
                    disabled(bridge)  # The only guard already loaded its immutable local policy.
                if response.get("done"):
                    disabled(bridge)
                    if response.get("status") != "completed" or len(current) != 1 or current[0][2] != "complete":
                        raise ValueError("Review failed or spend unknown; no retries")
                    state.update(
                        status="complete",
                        completed_at=utc_now(),
                        review=response,
                        cost_metadata=json.loads(current[0][3]),
                        call_id=current[0][0],
                    )
                    write_registry(directory / "review.json", response)
                    (directory / "review.md").write_text(response["response"])
            write_registry(state_path, state)
            return state
        except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
            disabled(bridge)
            state.update(status="stopped", error=str(exc), stopped_at=utc_now())
            write_registry(state_path, state)
            raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="Dispatch the single predeclared review once")
    args = parser.parse_args()
    os.umask(0o077)
    state = step(PROJECT, BRIDGE_ROOT, json.loads(SPEC_PATH.read_text()), args.execute)
    print(json.dumps(state, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

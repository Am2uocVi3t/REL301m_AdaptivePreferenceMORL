#!/usr/bin/env python3
"""Run finite offline gates and persist source-bound, non-scientific evidence."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET  # nosec B405 - locally generated pytest report
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.research_harness.aris import quota_errors
from src.research_harness.store import ResearchStore, utc_now, write_registry

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    quota = json.loads((ROOT / ".aris/preflight.json").read_text())
    if quota.get("status") != "PASS" or quota_errors(quota.get("quota_observed_at")):
        raise ValueError("A fresh timestamped preflight is required before this finite audit")
    policy = json.loads((ROOT / "configs/aris/project.json").read_text())
    if policy["claude"]["paid_enabled"] is not False or policy["unattended_enabled"] is not False:
        raise ValueError("Offline audit requires paid/scheduler disabled")
    checks = []
    with tempfile.TemporaryDirectory(prefix="aris-offline-audit-") as directory:
        junit = Path(directory) / "pytest.xml"
        commands = [
            [sys.executable, "-m", "ruff", "format", "--check", "."],
            [sys.executable, "-m", "ruff", "check", "."],
            [sys.executable, "-m", "mypy", "src", "scripts"],
            [sys.executable, "-m", "pytest", "-q", f"--junitxml={junit}"],
            [sys.executable, "-m", "bandit", "-q", "-r", "src", "scripts", "-ll"],
            [sys.executable, "-m", "compileall", "-q", "src", "scripts", "tests"],
            ["git", "diff", "--check"],
            ["bash", "-n", "scripts/start_aris_review_server.sh"],
            [sys.executable, "scripts/research_harness.py", "doctor"],
        ]
        for command in commands:
            completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=120, check=False)
            check = {
                "command": command,
                "exit_code": completed.returncode,
                "stdout": completed.stdout[-4000:],
                "stderr": completed.stderr[-2000:],
            }
            checks.append(check)
            print(json.dumps({"command": command[1:4], "exit_code": completed.returncode}), flush=True)
        cases = ET.parse(junit).getroot().findall(".//testcase") if junit.exists() else []  # nosec B314
        names = [
            case.attrib.get("name", "")
            for case in cases
            if case.attrib.get("classname", "").startswith("tests.test_aris")
        ]
        passed = bool(cases) and all(check["exit_code"] == 0 for check in checks)
    sources = [
        "scripts/aris_review_guard.py",
        "scripts/aris_preflight.py",
        "scripts/audit_aris_offline.py",
        "src/research_harness/aris.py",
        "tests/test_aris_review_guard.py",
        "tests/test_aris_offline_e2e.py",
        "tests/test_aris_integration.py",
        "configs/aris/project.json",
        "scripts/start_aris_review_server.sh",
    ]
    gate_tests = {
        "cost_model_metadata": ["metadata", "persistent_metadata", "failed_review"],
        "process_cleanup": ["timeout_kills", "interrupted_guard", "pipe_holding", "output_limit"],
        "reservations": ["concurrent_reservations", "refund_reserved", "legacy_import", "console_mapping"],
        "quota_freshness": ["quota_age", "low_or_unknown_quota"],
        "review_packet_boundaries": ["packet_", "command_boundaries"],
        "interruption_resume": ["server_restart", "unreviewed_done", "concurrent_reservations", "killed_execute"],
        "disabled_real_mcp": ["disabled_bridge_preserves", "disabled_and_historical", "installed_launcher"],
    }
    gates = {}
    for gate, fragments in gate_tests.items():
        selected = [name for name in names if any(fragment in name for fragment in fragments)]
        gates[gate] = {
            "status": "PASS" if passed and selected else "BLOCKED",
            "tests": selected,
            "scope": "synthetic_offline_fixtures_only",
        }
    external = Path("/home/hei/.local/share/rel301m-aris-setup")
    legacy = (external / "reserved-calls.txt").read_bytes()
    historical_notes = (external / "TEAM_COSTS.md").read_bytes()
    runtime_policy = json.loads((external / "policy.json").read_text())
    installed = (external / "claude-review-guard.py").read_bytes()
    report = {
        "kind": "aris_offline_hardening_v1",
        "checked_at": utc_now(),
        "status": "PASS" if passed else "BLOCKED",
        "git": ResearchStore(ROOT).git_snapshot(),
        "python": sys.version,
        "test_count": len(cases),
        "gates": gates,
        "checks": checks,
        "source_sha256": {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in sources},
        "paid_calls_performed": 0,
        "unattended_ready": False,
        "scientific_acceptance": False,
        "historical_console_reconciliation": "BLOCKED: no Console export provided; CLI estimates are not billing proof",
        "historical_reservations": {
            "count": len(legacy.splitlines()),
            "reserved_usd": len(legacy.splitlines()) * 0.25,
            "source_sha256": hashlib.sha256(legacy).hexdigest(),
            "source_unchanged": legacy == b"reserved\nreserved\n",
            "cli_reported_costs_usd": [0.0117487, 0.2251555],
            "cli_reported_sum_usd": 0.2369042,
            "cost_note_sha256": hashlib.sha256(historical_notes).hexdigest(),
            "console_reconciled": False,
        },
        "external_runtime": {
            "guard_matches_versioned_source": installed == (ROOT / sources[0]).read_bytes(),
            "guard_sha256": hashlib.sha256(installed).hexdigest(),
            "paid_enabled": runtime_policy.get("enabled"),
            "launcher_matches_versioned_source": (external / "start-review-server.sh").read_bytes()
            == (ROOT / "scripts/start_aris_review_server.sh").read_bytes(),
        },
        "bounded_cross_family_batch": "NOT_RUN: paid calls remain disabled",
        "limits": [
            "Packet scanning is heuristic and inline tools-off review is not an OS sandbox.",
            "Guardian covers wrapper death and same-group descendants; "
            "escaping setsid or guardian kill needs OS isolation.",
            "SIGKILL leaves a durable unsettled reservation; recovery must inspect processes and reconcile spend.",
            "Quota is an operator snapshot, not authenticated by this script.",
            "The pinned upstream serializes review prompts in its private local job state.",
        ],
    }
    write_registry(ROOT / "research/qualification/aris_offline_hardening_v1.json", report)
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())

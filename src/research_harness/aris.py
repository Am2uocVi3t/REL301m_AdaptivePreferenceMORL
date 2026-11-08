"""Read-only ARIS installation/policy preflight; not a dispatcher or sandbox."""

from __future__ import annotations

import hashlib
import math
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.research_harness.store import ResearchStore, load_registry, utc_now


def action_blockers(policy: dict[str, Any], action: str, remaining: float | None) -> list[str]:
    """Fail closed on unknown authority or quota before an operator dispatches."""
    reasons = []
    authorization = policy.get("authorization", {})
    authorized_actions = (
        set(authorization.get("authorized_actions", [])) if authorization.get("status") == "active" else set()
    )
    permitted_actions = set(policy["routine_actions"]) | authorized_actions
    if action not in permitted_actions:
        reasons.append(f"Action {action!r} requires separate authorization; bootstrap cannot dispatch it.")
    if remaining is None or not math.isfinite(remaining) or not 0 <= remaining <= 100:
        reasons.append("Fresh Codex quota snapshot required; unknown quota is not zero-cost capacity.")
    elif remaining < policy["minimum_codex_remaining_percent"]:
        reasons.append("Codex remaining quota is below the dispatch floor; save handoff and wait for reset.")
    return reasons


def _files(directory: Path) -> dict[str, str]:
    return {
        str(path.relative_to(directory)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in directory.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    }


def installation_errors(root: Path, policy: dict[str, Any]) -> tuple[list[str], int, int]:
    upstream = Path(policy["upstream_root"])
    errors = []
    if not upstream.is_dir():
        return ["Pinned ARIS checkout unavailable; do not fall back to an unpinned global install."], 0, 0
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=upstream, check=True, capture_output=True, text=True, timeout=10
        ).stdout.strip()
        dirty = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=no"],
            cwd=upstream,
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError) as exc:
        return [f"Cannot verify pinned ARIS checkout: {exc}"], 0, 0
    if commit != policy["upstream_commit"] or dirty:
        errors.append("ARIS upstream commit differs from pin or has tracked modifications.")
    selected: dict[str, dict[str, str]] = {}
    overlay_count = 0
    for package in policy["packages"]:
        source = upstream / "skills" / package
        if not source.is_dir():
            errors.append(f"Missing package: {package}")
        for directory in source.iterdir() if source.is_dir() else []:
            if directory.is_dir() and (directory / "SKILL.md").is_file():
                overlay_count += int(directory.name in selected)
                selected.setdefault(directory.name, {}).update(_files(directory))
    if not selected:
        errors.append("ARIS catalog is empty.")
    references = upstream / "skills" / "skills-codex" / "shared-references"
    selected["shared-references"] = _files(references)
    if not selected["shared-references"]:
        errors.append("Missing Codex shared references.")
    for name, expected in selected.items():
        target = root / ".agents" / "skills" / name
        if not target.is_dir() or expected != _files(target):
            errors.append(f"Installed ARIS content drift or missing files: {name}")
    if not (upstream / "tools" / "run_state.py").is_file():
        errors.append("Missing upstream resume helper.")
    return errors, len(selected) - 1, overlay_count


def quota_errors(observed_at: str | None, *, now: datetime | None = None) -> list[str]:
    """Operator snapshots expire after five minutes; future/naive times fail closed."""
    try:
        observed = datetime.fromisoformat(observed_at or "")
        if observed.tzinfo is None:
            raise ValueError("timezone missing")
        age = ((now or datetime.now(UTC)) - observed).total_seconds()
        if not 0 <= age <= 300:
            raise ValueError("snapshot stale or in future")
    except (TypeError, ValueError):
        return ["Quota observation requires a timezone-aware timestamp within the last 300 seconds."]
    return []


def preflight(root: Path, action: str, remaining: float | None, observed_at: str | None = None) -> dict[str, Any]:
    policy = load_registry(root / "configs" / "aris" / "project.json")
    errors, skills, overlays = installation_errors(root, policy)
    errors.extend(ResearchStore(root).validate())
    errors.extend(action_blockers(policy, action, remaining))
    errors.extend(quota_errors(observed_at))
    if policy["claude"]["paid_enabled"] is not False or policy["unattended_enabled"] is not False:
        errors.append("Bootstrap cannot enable paid/unattended dispatch; complete hardening gates first.")
    qualification = load_registry(root / "research" / "qualification" / "minecart_pcqn_backbone_v2.json")
    if qualification.get("passed") is not False:
        errors.append("Unexpected Minecart qualification state: re-review authority before continuing.")
    return {
        "kind": "aris_bootstrap_preflight",
        "checked_at": utc_now(),
        "status": "BLOCKED" if errors else "PASS",
        "scope": "installation_quota_and_recorded_action_authority_not_scientific_acceptance",
        "policy_is_os_sandbox": False,
        "dispatch_performed": False,
        "action": action,
        "authorization_id": policy.get("authorization", {}).get("id"),
        "authorized_actions": policy.get("authorization", {}).get("authorized_actions", []),
        "reported_remaining_percent": remaining,
        "quota_observed_at": observed_at,
        "quota_source": "operator_snapshot_not_independently_authenticated_by_this_script",
        "installed_skills": skills,
        "claude_overlays": overlays,
        "upstream_commit": policy["upstream_commit"],
        "canonical_phase": ResearchStore(root).state()["roadmap_phase_id"],
        "git": ResearchStore(root).git_snapshot(),
        "minecart_qualification": "failed" if qualification.get("passed") is False else "unexpected",
        "paid_dispatch_enabled": False,
        "unattended_ready": False,
        "remaining_work": [
            "Persist actual cost/token/model metadata and reconcile historical Console spend.",
            "Offline-test process-group cleanup, interruption and concurrent budget reservations.",
            "Stage allowlisted review packets; test path/symlink/secret exclusion.",
            "Run a defined bounded cross-family workflow batch before unattended enablement.",
        ],
        "blockers": errors,
    }

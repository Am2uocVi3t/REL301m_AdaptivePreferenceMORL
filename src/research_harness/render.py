from __future__ import annotations

from typing import Any

from src.research_harness.store import ResearchStore, utc_now


def render_status(store: ResearchStore) -> str:
    state = store.state()
    claims = store.claims().get("claims", [])
    papers = store.papers().get("papers", [])
    experiments = store.experiments().get("experiments", [])
    open_blockers = [blocker for blocker in state.get("open_blockers", []) if blocker.get("status") == "open"]
    snapshot = store.git_snapshot()
    lines = [
        f"Project: {state.get('project', 'UNKNOWN')}",
        f"Phase: {state.get('phase', 'UNKNOWN')}",
        f"Publication state: {state.get('publication_state', 'UNKNOWN')}",
        f"Git: {snapshot['branch']} @ {snapshot['commit']} (dirty: {snapshot['dirty']})",
        f"Claims: {_count_statuses(claims)}",
        f"Papers: {_count_statuses(papers)}",
        f"Experiments: {_count_statuses(experiments)}",
        f"Open blockers: {len(open_blockers)}",
        "Next actions:",
    ]
    lines.extend(f"  {index}. {action}" for index, action in enumerate(state.get("next_actions", []), start=1))
    return "\n".join(lines)


def render_handoff(store: ResearchStore) -> str:
    state = store.state()
    claims = store.claims().get("claims", [])
    papers = store.papers().get("papers", [])
    experiments = store.experiments().get("experiments", [])
    latest_session = store.latest_session()
    snapshot = store.git_snapshot()
    blockers = [blocker["description"] for blocker in state.get("open_blockers", []) if blocker.get("status") == "open"]
    active_claims = [
        f"{claim['id']} [{claim['status']}]: {claim['title']}" for claim in claims if claim.get("status") != "rejected"
    ]
    paper_queue = [
        f"{paper['id']} [{paper['status']}; {paper['evidence_level']}; access={paper['access_status']}]: "
        f"{paper['title']}"
        for paper in papers
        if paper["status"] != "excluded"
    ]
    full_text_requests = [
        f"{paper['id']}: {paper['title']} — {paper['url']} — {paper.get('access_note') or 'access not checked'}"
        for paper in papers
        if paper.get("full_text_required") and paper.get("status") != "excluded"
    ]
    active_experiments = [
        f"{experiment['id']} [{experiment['status']}]: {experiment['title']}"
        for experiment in experiments
        if experiment["status"] != "complete"
    ]
    session_summary = (
        latest_session.get("summary", "No session has been closed yet.")
        if latest_session
        else "No session has been closed yet."
    )
    body = f"""You are continuing the REL301m Adaptive Preference MORL research project.

Before acting:
1. Read `AGENTS.md`, `.agents/memory/MEMORY.md`, and `docs/research/PROJECT_STATUS.md`.
2. Run `python scripts/research_harness.py doctor` and `python scripts/research_harness.py status`.
3. Run `git status --short --branch`; do not overwrite unrelated changes.
4. Read the relevant protocol/config/code directly before making scientific claims.

Snapshot generated: {utc_now()}
Expected working branch at generation: {snapshot["branch"]}
Expected commit at generation: {snapshot["commit"]}
Working tree dirty at generation: {snapshot["dirty"]}
Current phase: {state["phase"]}
Publication state: {state["publication_state"]}

Research question:
{state["research_question"]}

Source precedence:
1. Executed tests and versioned raw-result artifacts.
2. Code and protocol/config files.
3. Machine-readable registries under `research/`, `docs/research/PROJECT_STATUS.md`, and `docs/ARCHITECTURE.md`.
4. Editable proposal v2.
5. Other Markdown documents.
6. Original submitted proposal PDF (historical only).

Active claims:
{_bullets(active_claims)}

Literature queue:
{_bullets(paper_queue, empty="No papers registered yet. Add primary sources before making novelty claims.")}

Full-text requests for the user:
{_bullets(full_text_requests, empty="None currently registered.")}

Active experiments:
{_bullets(active_experiments, empty="No active experiments registered.")}

Open blockers:
{_bullets(blockers)}

Latest closed-session summary:
{session_summary}

Next actions:
{_numbered(state.get("next_actions", []))}

Non-negotiable scientific guardrails:
- Do not label a claim `experimentally_supported` without a versioned raw-result artifact.
- Do not use final-test data for tuning, normalization, reference points, or checkpoint selection.
- Separate preference generalization from environment/dynamics generalization.
- Match interaction, update, diagnostic-evaluation, final-evaluation, and tuning budgets.
- Literature: use primary sources; log queries; register metadata/BibTeX; complete notes; never commit PDFs.
- Search legal full-text alternatives autonomously. If access still fails, keep the paper `screened`, record
  `full_text_required`, state what was tried, and ask the user for an uploaded PDF or authorized link.
- Never make a strong novelty or mechanism claim from metadata or an abstract alone.
- End substantial sessions with `python scripts/research_harness.py session close ... --write-handoff`.

User request for this new session:
[PASTE THE NEW REQUEST HERE]
"""
    return (
        "# Cross-Chat Research Handoff\n\nCopy the complete prompt below into a new chat.\n\n```text\n" + body + "```\n"
    )


def _count_statuses(records: list[dict[str, Any]]) -> str:
    if not records:
        return "0"
    counts: dict[str, int] = {}
    for record in records:
        status = str(record.get("status", "UNKNOWN"))
        counts[status] = counts.get(status, 0) + 1
    return f"{len(records)} (" + ", ".join(f"{key}={counts[key]}" for key in sorted(counts)) + ")"


def _bullets(items: list[str], *, empty: str = "None.") -> str:
    return "\n".join(f"- {item}" for item in items) if items else f"- {empty}"


def _numbered(items: list[str]) -> str:
    return "\n".join(f"{index}. {item}" for index, item in enumerate(items, start=1)) or "1. Reassess project state."

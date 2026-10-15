from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.research_harness.cli import main
from src.research_harness.render import render_handoff, render_status
from src.research_harness.store import ResearchStore, write_registry


def make_workspace(root: Path) -> ResearchStore:
    (root / "docs" / "research").mkdir(parents=True)
    (root / "configs" / "protocols").mkdir(parents=True)
    (root / "research" / "literature" / "notes").mkdir(parents=True)
    (root / "research" / "experiments").mkdir(parents=True)
    (root / "research" / "sessions").mkdir(parents=True)
    (root / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
    (root / "docs" / "research" / "PROJECT_STATUS.md").write_text("# Status\n", encoding="utf-8")
    (root / "docs" / "research" / "AI_RESEARCH_WORKFLOW.md").write_text("# Workflow\n", encoding="utf-8")
    (root / "docs" / "research" / "HANDOFF_PROMPT.md").write_text("# Handoff\n", encoding="utf-8")
    (root / "configs" / "protocols" / "test.json").write_text("{}\n", encoding="utf-8")
    (root / "research" / "literature" / "library.bib").write_text("", encoding="utf-8")
    write_registry(
        root / "research" / "state.json",
        {
            "schema_version": 1,
            "project": "Test project",
            "phase": "pilot",
            "publication_state": "unsupported",
            "research_question": "Does the mechanism work?",
            "open_blockers": [],
            "next_actions": ["Run pilot."],
        },
    )
    write_registry(
        root / "research" / "claims.json",
        {
            "schema_version": 1,
            "claims": [
                {
                    "id": "test-claim",
                    "title": "A testable claim",
                    "status": "hypothesis",
                    "confidence": "low",
                    "evidence": [],
                    "antecedents": ["doe2025antecedent"],
                    "closest_antecedent": "doe2025antecedent",
                    "known": "A prior allocation mechanism exists.",
                    "difference": "The test mechanism changes the allocation unit.",
                    "novelty_verdict": "incremental",
                    "novelty_confidence": "low",
                    "falsifier": "An equivalent prior mechanism.",
                    "differentiating_experiment": "Compare mechanisms under matched budgets.",
                    "allowed_wording": "The mechanism is a test hypothesis.",
                }
            ],
        },
    )
    write_registry(
        root / "research" / "roadmap.json",
        {
            "schema_version": 1,
            "active_phase_id": "phase-1",
            "phases": [
                {
                    "id": "phase-1",
                    "title": "Map claims",
                    "status": "active",
                    "deliverables": [{"id": "map", "description": "Map claims", "status": "in_progress"}],
                    "entry_criteria": ["Question defined"],
                    "exit_criteria": ["Claims mapped"],
                    "go_no_go_rule": "Proceed only with mapped claims.",
                    "evidence_paths": [],
                    "blocker_ids": [],
                    "allowed_next_phase_ids": [],
                }
            ],
        },
    )
    state = json.loads((root / "research" / "state.json").read_text(encoding="utf-8"))
    state["roadmap_phase_id"] = "phase-1"
    write_registry(root / "research" / "state.json", state)
    write_registry(
        root / "research" / "literature" / "index.json",
        {
            "schema_version": 1,
            "papers": [
                {
                    "id": "doe2025antecedent",
                    "title": "Prior Allocation",
                    "authors": ["Jane Doe"],
                    "year": 2025,
                    "venue": "TestConf",
                    "source_type": "peer-reviewed",
                    "status": "screened",
                    "access_status": "not_checked",
                    "evidence_level": "metadata_only",
                    "full_text_required": True,
                    "access_note": "",
                    "access_checked_at": None,
                    "url": "https://example.test/prior",
                    "tags": ["allocation"],
                    "claim_ids": ["test-claim"],
                    "note": "research/literature/notes/doe2025antecedent.md",
                }
            ],
        },
    )
    write_registry(
        root / "research" / "experiments" / "registry.json",
        {"schema_version": 1, "experiments": []},
    )
    return ResearchStore(root)


def test_repository_research_state_is_valid() -> None:
    root = Path(__file__).resolve().parents[1]
    assert ResearchStore(root).validate() == []


def test_doctor_and_status_work_without_project_dependencies(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    make_workspace(tmp_path)
    assert main(["--root", str(tmp_path), "doctor"]) == 0
    assert main(["--root", str(tmp_path), "status"]) == 0
    output = capsys.readouterr().out
    assert "Research harness validation passed" in output
    assert "Phase: phase-1 — Map claims (active)" in output


def test_roadmap_cli_lists_active_phase(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    make_workspace(tmp_path)
    assert main(["--root", str(tmp_path), "roadmap", "list"]) == 0
    assert "phase-1\tactive\tMap claims" in capsys.readouterr().out


def test_completed_roadmap_phase_requires_evidence(tmp_path: Path) -> None:
    store = make_workspace(tmp_path)
    roadmap = store.roadmap()
    roadmap["phases"][0]["status"] = "complete"
    write_registry(store.roadmap_path, roadmap)
    assert "roadmap: exactly one phase must be active" in store.validate()
    assert "roadmap: completed phase phase-1 needs evidence paths" in store.validate()


def test_roadmap_rejects_unknown_transition(tmp_path: Path) -> None:
    store = make_workspace(tmp_path)
    roadmap = store.roadmap()
    roadmap["phases"][0]["allowed_next_phase_ids"] = ["missing-phase"]
    write_registry(store.roadmap_path, roadmap)
    assert "roadmap: phase-1 has unknown next phases: ['missing-phase']" in store.validate()


def test_claim_antecedents_must_reference_registered_papers(tmp_path: Path) -> None:
    store = make_workspace(tmp_path)
    claims = store.claims()
    claims["claims"][0]["antecedents"] = ["missing-paper"]
    claims["claims"][0]["closest_antecedent"] = "missing-paper"
    write_registry(store.claims_path, claims)
    assert "claims: test-claim has unknown antecedents: ['missing-paper']" in store.validate()


def test_add_paper_creates_metadata_note_and_bibtex(tmp_path: Path) -> None:
    store = make_workspace(tmp_path)
    note = store.add_paper(
        identifier="doe2026allocation",
        title="Adaptive Allocation",
        year=2026,
        authors=["Jane Doe", "John Roe"],
        url="https://example.test/paper",
        source_type="peer-reviewed",
        venue="TestConf",
        status="queued",
        tags=["allocation"],
        claim_ids=["test-claim"],
    )
    assert note.exists()
    assert "Mechanism and assumptions" in note.read_text(encoding="utf-8")
    assert "@misc{doe2026allocation" in store.bib_path.read_text(encoding="utf-8")
    paper = next(paper for paper in store.papers()["papers"] if paper["id"] == "doe2026allocation")
    assert paper["note"] == "research/literature/notes/doe2026allocation.md"
    assert paper["evidence_level"] == "metadata_only"
    assert paper["full_text_required"] is True
    assert paper["claim_ids"] == ["test-claim"]
    assert store.validate() == []


def test_duplicate_paper_is_rejected(tmp_path: Path) -> None:
    store = make_workspace(tmp_path)
    store.add_paper(
        identifier="doe2026allocation",
        title="Adaptive Allocation",
        year=2026,
        authors=["Jane Doe"],
        url="https://example.test/paper",
        source_type="preprint",
        venue=None,
        status="queued",
        tags=[],
    )
    with pytest.raises(ValueError, match="already exists"):
        store.add_paper(
            identifier="doe2026allocation",
            title="Adaptive Allocation",
            year=2026,
            authors=["Jane Doe"],
            url="https://example.test/paper",
            source_type="preprint",
            venue=None,
            status="queued",
            tags=[],
        )


def test_read_paper_requires_completed_structured_note(tmp_path: Path) -> None:
    store = make_workspace(tmp_path)
    note = store.add_paper(
        identifier="doe2026allocation",
        title="Adaptive Allocation",
        year=2026,
        authors=["Jane Doe"],
        url="https://example.test/paper",
        source_type="preprint",
        venue=None,
        status="queued",
        tags=[],
    )
    with pytest.raises(ValueError, match="verified full-text access"):
        store.set_paper_status("doe2026allocation", "read")
    store.set_paper_access(
        "doe2026allocation",
        "open_full_text",
        "full_text",
        False,
        "Official proceedings PDF checked.",
    )
    with pytest.raises(ValueError, match="structured note is complete"):
        store.set_paper_status("doe2026allocation", "read")
    completed_note = note.read_text(encoding="utf-8").replace("TODO", "Completed analysis")
    note.write_text(completed_note.replace("FULL_TEXT_REQUIRED", "FULL_TEXT_VERIFIED"), encoding="utf-8")
    store.set_paper_status("doe2026allocation", "read")
    assert store.validate() == []


def test_paywalled_paper_stays_screened_and_is_requested_in_handoff(tmp_path: Path) -> None:
    store = make_workspace(tmp_path)
    store.add_paper(
        identifier="doe2026allocation",
        title="Adaptive Allocation",
        year=2026,
        authors=["Jane Doe"],
        url="https://example.test/paper",
        source_type="peer-reviewed",
        venue="TestConf",
        status="queued",
        tags=[],
    )
    store.set_paper_access(
        "doe2026allocation",
        "paywalled",
        "abstract_only",
        True,
        "Publisher and author page checked; abstract only.",
    )
    store.set_paper_status("doe2026allocation", "screened")
    assert store.validate() == []
    handoff = render_handoff(store)
    assert "Full-text requests for the user" in handoff
    assert "Publisher and author page checked" in handoff
    with pytest.raises(ValueError, match="verified full-text access"):
        store.set_paper_status("doe2026allocation", "read")


def test_full_text_evidence_rejects_blocked_access_status(tmp_path: Path) -> None:
    store = make_workspace(tmp_path)
    store.add_paper(
        identifier="doe2026allocation",
        title="Adaptive Allocation",
        year=2026,
        authors=["Jane Doe"],
        url="https://example.test/paper",
        source_type="preprint",
        venue=None,
        status="queued",
        tags=[],
    )
    with pytest.raises(ValueError, match="Full-text evidence requires"):
        store.set_paper_access(
            "doe2026allocation",
            "blocked",
            "full_text",
            False,
            "Access denied.",
        )


def test_cli_records_full_text_access(tmp_path: Path) -> None:
    store = make_workspace(tmp_path)
    store.add_paper(
        identifier="doe2026allocation",
        title="Adaptive Allocation",
        year=2026,
        authors=["Jane Doe"],
        url="https://example.test/paper",
        source_type="preprint",
        venue=None,
        status="queued",
        tags=[],
    )
    assert (
        main(
            [
                "--root",
                str(tmp_path),
                "paper",
                "set-access",
                "doe2026allocation",
                "--access-status",
                "author_manuscript",
                "--evidence-level",
                "full_text",
                "--full-text-required",
                "no",
                "--note",
                "Author manuscript checked.",
            ]
        )
        == 0
    )
    paper = next(paper for paper in store.papers()["papers"] if paper["id"] == "doe2026allocation")
    assert paper["access_status"] == "author_manuscript"
    assert paper["full_text_required"] is False


def test_claim_status_records_evidence(tmp_path: Path) -> None:
    store = make_workspace(tmp_path)
    evidence = tmp_path / "tests" / "evidence.txt"
    evidence.parent.mkdir()
    evidence.write_text("verified\n", encoding="utf-8")
    store.set_claim_status("test-claim", "validated", ["tests/evidence.txt"])
    claim = store.claims()["claims"][0]
    assert claim["status"] == "validated"
    assert claim["evidence"] == ["tests/evidence.txt"]
    assert store.validate() == []


def test_empirical_claim_requires_versioned_artifact(tmp_path: Path) -> None:
    store = make_workspace(tmp_path)
    with pytest.raises(ValueError, match="artifact:<versioned-path>"):
        store.set_claim_status("test-claim", "experimentally_supported", [])
    artifact = tmp_path / "research" / "artifacts" / "result.json"
    artifact.parent.mkdir()
    artifact.write_text("{}\n", encoding="utf-8")
    store.set_claim_status(
        "test-claim",
        "experimentally_supported",
        ["artifact:research/artifacts/result.json"],
    )
    assert store.validate() == []


def test_experiment_requires_known_claim_and_existing_protocol(tmp_path: Path) -> None:
    store = make_workspace(tmp_path)
    with pytest.raises(ValueError, match="Unknown claim"):
        store.add_experiment(
            identifier="unknown-claim-experiment",
            title="Invalid",
            protocol="configs/protocols/test.json",
            claim_ids=["missing"],
        )
    store.add_experiment(
        identifier="paired-pilot",
        title="Paired pilot",
        protocol="configs/protocols/test.json",
        claim_ids=["test-claim"],
    )
    assert store.experiments()["experiments"][0]["status"] == "planned"
    assert store.validate() == []


def test_completed_experiment_requires_artifact(tmp_path: Path) -> None:
    store = make_workspace(tmp_path)
    store.add_experiment(
        identifier="paired-pilot",
        title="Paired pilot",
        protocol="configs/protocols/test.json",
        claim_ids=["test-claim"],
    )
    with pytest.raises(ValueError, match="requires an artifact"):
        store.set_experiment_status("paired-pilot", "complete", None)


def test_session_close_updates_state_log_and_handoff(tmp_path: Path) -> None:
    store = make_workspace(tmp_path)
    record = store.close_session("Implemented the harness.", ["Review it."], ["No Git repository in test."])
    assert record["git"]["branch"] == "UNKNOWN"
    assert store.state()["next_actions"] == ["Review it."]
    logged = json.loads(store.sessions_path.read_text(encoding="utf-8"))
    assert logged["summary"] == "Implemented the harness."
    handoff = render_handoff(store)
    assert handoff.startswith("# Cross-Chat Research Handoff")
    assert "```text" in handoff
    assert "Implemented the harness." in handoff


def test_status_counts_registered_items(tmp_path: Path) -> None:
    store = make_workspace(tmp_path)
    status = render_status(store)
    assert "Claims: 1 (hypothesis=1)" in status
    assert "Papers: 1 (screened=1)" in status
    assert "Experiments: 0" in status

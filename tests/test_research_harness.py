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
                    "evidence": [],
                }
            ],
        },
    )
    write_registry(root / "research" / "literature" / "index.json", {"schema_version": 1, "papers": []})
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
    assert "Phase: pilot" in output


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
    )
    assert note.exists()
    assert "Mechanism and assumptions" in note.read_text(encoding="utf-8")
    assert "@misc{doe2026allocation" in store.bib_path.read_text(encoding="utf-8")
    assert store.papers()["papers"][0]["note"] == "research/literature/notes/doe2026allocation.md"
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
    with pytest.raises(ValueError, match="structured note is complete"):
        store.set_paper_status("doe2026allocation", "read")
    note.write_text(note.read_text(encoding="utf-8").replace("TODO", "Completed analysis"), encoding="utf-8")
    store.set_paper_status("doe2026allocation", "read")
    assert store.validate() == []


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
    assert "Papers: 0" in status
    assert "Experiments: 0" in status

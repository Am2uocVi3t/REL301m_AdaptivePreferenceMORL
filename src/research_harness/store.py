from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CLAIM_STATUSES = {
    "hypothesis",
    "implemented",
    "validated",
    "experimentally_supported",
    "rejected",
}
PAPER_STATUSES = {"queued", "screened", "read", "excluded"}
PAPER_SOURCE_TYPES = {"peer-reviewed", "preprint", "benchmark", "software", "venue-policy"}
PAPER_ACCESS_STATUSES = {
    "not_checked",
    "open_full_text",
    "author_manuscript",
    "user_supplied",
    "paywalled",
    "blocked",
}
PAPER_EVIDENCE_LEVELS = {"metadata_only", "abstract_only", "full_text"}
FULL_TEXT_ACCESS_STATUSES = {"open_full_text", "author_manuscript", "user_supplied"}
EXPERIMENT_STATUSES = {"planned", "running", "complete", "failed", "blocked"}
BLOCKER_STATUSES = {"open", "resolved"}
ROADMAP_PHASE_STATUSES = {"not_started", "active", "blocked", "complete"}
ROADMAP_DELIVERABLE_STATUSES = {"not_started", "in_progress", "complete", "blocked"}
NOVELTY_VERDICTS = {"not_novel", "incremental", "potentially_novel", "novelty_unresolved"}
IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_registry(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return data


def write_registry(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


class ResearchStore:
    """Read and mutate the versioned research registries under ``research/``."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.research_dir = self.root / "research"
        self.state_path = self.research_dir / "state.json"
        self.claims_path = self.research_dir / "claims.json"
        self.roadmap_path = self.research_dir / "roadmap.json"
        self.papers_path = self.research_dir / "literature" / "index.json"
        self.bib_path = self.research_dir / "literature" / "library.bib"
        self.notes_dir = self.research_dir / "literature" / "notes"
        self.experiments_path = self.research_dir / "experiments" / "registry.json"
        self.sessions_path = self.research_dir / "sessions" / "session-log.jsonl"
        self.handoff_path = self.root / "docs" / "research" / "HANDOFF_PROMPT.md"

    def state(self) -> dict[str, Any]:
        return load_registry(self.state_path)

    def claims(self) -> dict[str, Any]:
        return load_registry(self.claims_path)

    def roadmap(self) -> dict[str, Any]:
        return load_registry(self.roadmap_path)

    def papers(self) -> dict[str, Any]:
        return load_registry(self.papers_path)

    def experiments(self) -> dict[str, Any]:
        return load_registry(self.experiments_path)

    def latest_session(self) -> dict[str, Any] | None:
        if not self.sessions_path.exists():
            return None
        records = [line for line in self.sessions_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if not records:
            return None
        parsed = json.loads(records[-1])
        if not isinstance(parsed, dict):
            raise ValueError(f"Expected a JSON object in {self.sessions_path}")
        return parsed

    def git_snapshot(self) -> dict[str, str]:
        def run(*args: str) -> str:
            completed = subprocess.run(
                ["git", *args],
                cwd=self.root,
                check=True,
                capture_output=True,
                text=True,
            )
            return completed.stdout.strip()

        try:
            branch = run("branch", "--show-current") or "DETACHED"
            commit = run("rev-parse", "--short", "HEAD")
            dirty = "yes" if run("status", "--porcelain") else "no"
        except (FileNotFoundError, subprocess.CalledProcessError):
            return {"branch": "UNKNOWN", "commit": "UNKNOWN", "dirty": "UNKNOWN"}
        return {"branch": branch, "commit": commit, "dirty": dirty}

    def validate(self) -> list[str]:
        errors: list[str] = []
        loaders = {
            "state": self.state,
            "claims": self.claims,
            "roadmap": self.roadmap,
            "papers": self.papers,
            "experiments": self.experiments,
        }
        documents: dict[str, dict[str, Any]] = {}
        for name, loader in loaders.items():
            try:
                documents[name] = loader()
            except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
                errors.append(f"{name}: {exc}")
        if errors:
            return errors

        for name, document in documents.items():
            if document.get("schema_version") != 1:
                errors.append(f"{name}: schema_version must be 1")

        state = documents["state"]
        for field in ("project", "phase", "publication_state", "research_question", "next_actions"):
            if not state.get(field):
                errors.append(f"state: missing {field}")
        self._validate_blockers(state.get("open_blockers"), errors)

        roadmap = documents["roadmap"]
        self._validate_roadmap(roadmap, state, errors)

        claims = documents["claims"].get("claims")
        claim_ids = self._validate_records("claims", claims, CLAIM_STATUSES, errors)
        if isinstance(claims, list):
            for claim in claims:
                if isinstance(claim, dict):
                    for field in (
                        "closest_antecedent",
                        "known",
                        "difference",
                        "novelty_confidence",
                        "falsifier",
                        "differentiating_experiment",
                        "allowed_wording",
                    ):
                        if not claim.get(field):
                            errors.append(f"claims: {claim.get('id')} missing {field}")
                    if claim.get("novelty_verdict") not in NOVELTY_VERDICTS:
                        errors.append(f"claims: {claim.get('id')} has invalid novelty_verdict")
                    for evidence in claim.get("evidence", []):
                        if isinstance(evidence, str):
                            evidence_path = evidence.removeprefix("artifact:").split(":", maxsplit=1)[0]
                            if evidence_path and not (self.root / evidence_path).exists():
                                errors.append(
                                    f"claims: {claim.get('id')} evidence path does not exist: {evidence_path}"
                                )
                    if claim.get("status") == "experimentally_supported" and not any(
                        str(evidence).startswith("artifact:") for evidence in claim.get("evidence", [])
                    ):
                        errors.append(
                            f"claims: {claim.get('id')} needs artifact:<versioned-path> evidence for empirical support"
                        )

        papers = documents["papers"].get("papers")
        paper_ids = self._validate_records("papers", papers, PAPER_STATUSES, errors)
        if isinstance(papers, list):
            for paper in papers:
                if not isinstance(paper, dict):
                    continue
                if paper.get("source_type") not in PAPER_SOURCE_TYPES:
                    errors.append(f"papers: {paper.get('id')} has invalid source_type")
                unknown_claims = set(paper.get("claim_ids", [])) - claim_ids
                if unknown_claims:
                    errors.append(f"papers: {paper.get('id')} has unknown claims: {sorted(unknown_claims)}")
                access_status = paper.get("access_status")
                evidence_level = paper.get("evidence_level")
                full_text_required = paper.get("full_text_required")
                if access_status not in PAPER_ACCESS_STATUSES:
                    errors.append(f"papers: {paper.get('id')} has invalid access_status")
                if evidence_level not in PAPER_EVIDENCE_LEVELS:
                    errors.append(f"papers: {paper.get('id')} has invalid evidence_level")
                if not isinstance(full_text_required, bool):
                    errors.append(f"papers: {paper.get('id')} full_text_required must be boolean")
                if evidence_level == "full_text" and access_status not in FULL_TEXT_ACCESS_STATUSES:
                    errors.append(f"papers: {paper.get('id')} full_text evidence needs a full-text access status")
                if paper.get("status") == "read":
                    if evidence_level != "full_text" or access_status not in FULL_TEXT_ACCESS_STATUSES:
                        errors.append(f"papers: {paper.get('id')} is read without verified full-text access")
                    if full_text_required is not False:
                        errors.append(f"papers: {paper.get('id')} is read but still requires full text")
                    note = paper.get("note")
                    if not isinstance(note, str) or not (self.root / note).exists():
                        errors.append(f"papers: {paper.get('id')} is read but has no existing note")
                    elif any(
                        marker in (self.root / note).read_text(encoding="utf-8")
                        for marker in ("TODO", "FULL_TEXT_REQUIRED")
                    ):
                        errors.append(f"papers: {paper.get('id')} is read but its note is incomplete")
        if isinstance(claims, list):
            for claim in claims:
                if not isinstance(claim, dict):
                    continue
                antecedents = set(claim.get("antecedents", []))
                unknown_antecedents = antecedents - paper_ids
                if unknown_antecedents:
                    errors.append(f"claims: {claim.get('id')} has unknown antecedents: {sorted(unknown_antecedents)}")
                if claim.get("closest_antecedent") not in antecedents:
                    errors.append(f"claims: {claim.get('id')} closest antecedent must be in antecedents")

        experiments = documents["experiments"].get("experiments")
        self._validate_records("experiments", experiments, EXPERIMENT_STATUSES, errors)
        if isinstance(experiments, list):
            for experiment in experiments:
                if not isinstance(experiment, dict):
                    continue
                protocol = experiment.get("protocol")
                if protocol and not (self.root / str(protocol)).exists():
                    errors.append(f"experiments: {experiment.get('id')} protocol does not exist: {protocol}")
                if experiment.get("status") == "complete" and not experiment.get("artifact"):
                    errors.append(f"experiments: {experiment.get('id')} is complete but has no artifact")
                unknown = set(experiment.get("claim_ids", [])) - claim_ids
                if unknown:
                    errors.append(f"experiments: {experiment.get('id')} has unknown claims: {sorted(unknown)}")

        if len(paper_ids) != len(set(paper_ids)):
            errors.append("papers: duplicate IDs")
        for required in (
            self.root / "AGENTS.md",
            self.root / "docs" / "research" / "PROJECT_STATUS.md",
            self.root / "docs" / "research" / "AI_RESEARCH_WORKFLOW.md",
            self.handoff_path,
            self.bib_path,
        ):
            if not required.exists():
                errors.append(f"required file missing: {required.relative_to(self.root)}")
        return errors

    def _validate_roadmap(
        self,
        roadmap: dict[str, Any],
        state: dict[str, Any],
        errors: list[str],
    ) -> None:
        phases = roadmap.get("phases")
        if not isinstance(phases, list) or not phases:
            errors.append("roadmap: phases must be a non-empty list")
            return
        phase_ids = self._validate_records("roadmap phases", phases, ROADMAP_PHASE_STATUSES, errors)
        active_phase_id = roadmap.get("active_phase_id")
        active_phases = [phase for phase in phases if phase.get("status") == "active"]
        if len(active_phases) != 1:
            errors.append("roadmap: exactly one phase must be active")
        if active_phase_id not in phase_ids:
            errors.append(f"roadmap: unknown active_phase_id {active_phase_id!r}")
        elif not any(phase.get("id") == active_phase_id and phase.get("status") == "active" for phase in phases):
            errors.append("roadmap: active_phase_id must reference the active phase")
        if state.get("roadmap_phase_id") != active_phase_id:
            errors.append("state: roadmap_phase_id must match roadmap active_phase_id")
        active_index = next(
            (index for index, phase in enumerate(phases) if phase.get("id") == active_phase_id),
            None,
        )
        if active_index is not None:
            if any(phase.get("status") != "complete" for phase in phases[:active_index]):
                errors.append("roadmap: every phase before the active phase must be complete")
            if any(phase.get("status") == "complete" for phase in phases[active_index + 1 :]):
                errors.append("roadmap: phases after the active phase cannot be complete")

        blocker_ids = {
            blocker.get("id")
            for blocker in state.get("open_blockers", [])
            if isinstance(blocker, dict) and blocker.get("status") == "open"
        }
        for phase in phases:
            phase_id = phase.get("id")
            unknown_next = set(phase.get("allowed_next_phase_ids", [])) - phase_ids
            if unknown_next:
                errors.append(f"roadmap: {phase_id} has unknown next phases: {sorted(unknown_next)}")
            unknown_blockers = set(phase.get("blocker_ids", [])) - blocker_ids
            if unknown_blockers:
                errors.append(f"roadmap: {phase_id} has unknown open blockers: {sorted(unknown_blockers)}")
            evidence_paths = phase.get("evidence_paths", [])
            if phase.get("status") == "complete" and not evidence_paths:
                errors.append(f"roadmap: completed phase {phase_id} needs evidence paths")
            for evidence_path in evidence_paths:
                if not isinstance(evidence_path, str) or not (self.root / evidence_path).exists():
                    errors.append(f"roadmap: {phase_id} evidence path does not exist: {evidence_path}")
            deliverables = phase.get("deliverables")
            if not isinstance(deliverables, list) or not deliverables:
                errors.append(f"roadmap: {phase_id} needs deliverables")
                continue
            for deliverable in deliverables:
                if not isinstance(deliverable, dict):
                    errors.append(f"roadmap: {phase_id} deliverables must be mappings")
                elif deliverable.get("status") not in ROADMAP_DELIVERABLE_STATUSES:
                    errors.append(f"roadmap: {phase_id} deliverable {deliverable.get('id')} has invalid status")
            if phase.get("status") == "complete" and any(
                deliverable.get("status") != "complete" for deliverable in deliverables if isinstance(deliverable, dict)
            ):
                errors.append(f"roadmap: completed phase {phase_id} has incomplete deliverables")

    @staticmethod
    def _validate_blockers(value: Any, errors: list[str]) -> None:
        if not isinstance(value, list):
            errors.append("state: open_blockers must be a list")
            return
        for blocker in value:
            if not isinstance(blocker, dict) or not blocker.get("id") or not blocker.get("description"):
                errors.append("state: each blocker needs id and description")
            elif blocker.get("status") not in BLOCKER_STATUSES:
                errors.append(f"state: {blocker.get('id')} has invalid blocker status")

    @staticmethod
    def _validate_records(
        name: str,
        records: Any,
        valid_statuses: set[str],
        errors: list[str],
    ) -> set[str]:
        if not isinstance(records, list):
            errors.append(f"{name}: records must be a list")
            return set()
        seen: set[str] = set()
        for record in records:
            if not isinstance(record, dict):
                errors.append(f"{name}: every record must be a mapping")
                continue
            identifier = record.get("id")
            if not isinstance(identifier, str) or not IDENTIFIER_PATTERN.fullmatch(identifier):
                errors.append(f"{name}: invalid id {identifier!r}")
                continue
            if identifier in seen:
                errors.append(f"{name}: duplicate id {identifier}")
            seen.add(identifier)
            if record.get("status") not in valid_statuses:
                errors.append(f"{name}: {identifier} has invalid status {record.get('status')!r}")
        return seen

    def set_claim_status(self, identifier: str, status: str, evidence: list[str]) -> None:
        if status not in CLAIM_STATUSES:
            raise ValueError(f"Invalid claim status: {status}")
        document = self.claims()
        claim = self._find(document.get("claims", []), identifier, "claim")
        claim["status"] = status
        if evidence:
            claim["evidence"] = list(dict.fromkeys([*claim.get("evidence", []), *evidence]))
        if status == "experimentally_supported" and not any(
            str(item).startswith("artifact:") for item in claim.get("evidence", [])
        ):
            raise ValueError("experimentally_supported requires artifact:<versioned-path> evidence")
        claim["updated_at"] = utc_now()
        write_registry(self.claims_path, document)

    def add_paper(
        self,
        *,
        identifier: str,
        title: str,
        year: int,
        authors: list[str],
        url: str,
        source_type: str,
        venue: str | None,
        status: str,
        tags: list[str],
        claim_ids: list[str] | None = None,
    ) -> Path:
        self._require_identifier(identifier)
        if source_type not in PAPER_SOURCE_TYPES:
            raise ValueError(f"Invalid source type: {source_type}")
        if status not in PAPER_STATUSES:
            raise ValueError(f"Invalid paper status: {status}")
        if status == "read":
            raise ValueError("Add the paper as queued or screened; full-text access and notes are required before read")
        for field_name, value in {"title": title, "url": url, "venue": venue or ""}.items():
            if "\n" in value or "{" in value or "}" in value:
                raise ValueError(f"{field_name} cannot contain newlines or braces")
        document = self.papers()
        known_claims = {claim["id"] for claim in self.claims().get("claims", [])}
        unknown_claims = set(claim_ids or []) - known_claims
        if unknown_claims:
            raise ValueError(f"Unknown claim IDs: {sorted(unknown_claims)}")
        records = document.setdefault("papers", [])
        if any(paper.get("id") == identifier for paper in records):
            raise ValueError(f"Paper already exists: {identifier}")
        note_path = self.notes_dir / f"{identifier}.md"
        relative_note = note_path.relative_to(self.root).as_posix()
        records.append(
            {
                "id": identifier,
                "title": title,
                "authors": authors,
                "year": year,
                "venue": venue or "UNKNOWN",
                "source_type": source_type,
                "status": status,
                "access_status": "not_checked",
                "evidence_level": "metadata_only",
                "full_text_required": True,
                "access_note": "",
                "access_checked_at": None,
                "url": url,
                "tags": tags,
                "claim_ids": claim_ids or [],
                "note": relative_note,
                "added_at": utc_now(),
            }
        )
        write_registry(self.papers_path, document)
        note_path.parent.mkdir(parents=True, exist_ok=True)
        note_path.write_text(self._paper_note(identifier, title, url, status), encoding="utf-8")
        self.bib_path.parent.mkdir(parents=True, exist_ok=True)
        with self.bib_path.open("a", encoding="utf-8") as bibliography:
            bibliography.write(self._bibtex(identifier, title, year, authors, url, venue))
        return note_path

    def set_paper_status(self, identifier: str, status: str) -> None:
        if status not in PAPER_STATUSES:
            raise ValueError(f"Invalid paper status: {status}")
        document = self.papers()
        paper = self._find(document.get("papers", []), identifier, "paper")
        if status == "read":
            if (
                paper.get("evidence_level") != "full_text"
                or paper.get("access_status") not in FULL_TEXT_ACCESS_STATUSES
            ):
                raise ValueError("A paper can be marked read only after verified full-text access")
            if paper.get("full_text_required") is not False:
                raise ValueError("A paper can be marked read only when full_text_required is false")
            note = self.root / paper["note"]
            if not note.exists() or any(
                marker in note.read_text(encoding="utf-8") for marker in ("TODO", "FULL_TEXT_REQUIRED")
            ):
                raise ValueError("A paper can be marked read only after its structured note is complete")
        paper["status"] = status
        paper["updated_at"] = utc_now()
        write_registry(self.papers_path, document)

    def set_paper_access(
        self,
        identifier: str,
        access_status: str,
        evidence_level: str,
        full_text_required: bool,
        access_note: str,
    ) -> None:
        if access_status not in PAPER_ACCESS_STATUSES:
            raise ValueError(f"Invalid paper access status: {access_status}")
        if evidence_level not in PAPER_EVIDENCE_LEVELS:
            raise ValueError(f"Invalid paper evidence level: {evidence_level}")
        if evidence_level == "full_text" and access_status not in FULL_TEXT_ACCESS_STATUSES:
            raise ValueError("Full-text evidence requires open, author-manuscript, or user-supplied access")
        if evidence_level != "full_text" and not full_text_required:
            raise ValueError("full_text_required can be false only when evidence_level is full_text")
        document = self.papers()
        paper = self._find(document.get("papers", []), identifier, "paper")
        paper["access_status"] = access_status
        paper["evidence_level"] = evidence_level
        paper["full_text_required"] = full_text_required
        paper["access_note"] = access_note
        paper["access_checked_at"] = utc_now()
        paper["updated_at"] = utc_now()
        write_registry(self.papers_path, document)

    def add_experiment(
        self,
        *,
        identifier: str,
        title: str,
        protocol: str,
        claim_ids: list[str],
        status: str = "planned",
    ) -> None:
        self._require_identifier(identifier)
        if status not in EXPERIMENT_STATUSES:
            raise ValueError(f"Invalid experiment status: {status}")
        if not (self.root / protocol).exists():
            raise ValueError(f"Protocol does not exist: {protocol}")
        known_claims = {claim["id"] for claim in self.claims().get("claims", [])}
        unknown = set(claim_ids) - known_claims
        if unknown:
            raise ValueError(f"Unknown claim IDs: {sorted(unknown)}")
        document = self.experiments()
        records = document.setdefault("experiments", [])
        if any(experiment.get("id") == identifier for experiment in records):
            raise ValueError(f"Experiment already exists: {identifier}")
        records.append(
            {
                "id": identifier,
                "title": title,
                "status": status,
                "protocol": protocol,
                "claim_ids": claim_ids,
                "artifact": None,
                "notes": "",
                "created_at": utc_now(),
            }
        )
        write_registry(self.experiments_path, document)

    def set_experiment_status(self, identifier: str, status: str, artifact: str | None) -> None:
        if status not in EXPERIMENT_STATUSES:
            raise ValueError(f"Invalid experiment status: {status}")
        document = self.experiments()
        experiment = self._find(document.get("experiments", []), identifier, "experiment")
        effective_artifact = artifact if artifact is not None else experiment.get("artifact")
        if status == "complete" and not effective_artifact:
            raise ValueError("A completed experiment requires an artifact")
        experiment["status"] = status
        if artifact is not None:
            experiment["artifact"] = artifact
        experiment["updated_at"] = utc_now()
        write_registry(self.experiments_path, document)

    def close_session(self, summary: str, next_actions: list[str], blockers: list[str]) -> dict[str, Any]:
        snapshot = self.git_snapshot()
        record: dict[str, Any] = {
            "closed_at": utc_now(),
            "summary": summary,
            "next_actions": next_actions,
            "blockers": blockers,
            "git": snapshot,
        }
        append_jsonl(self.sessions_path, record)
        state = self.state()
        state["updated_at"] = record["closed_at"]
        state["last_session_summary"] = summary
        state["next_actions"] = next_actions
        state["working_branch"] = snapshot["branch"]
        write_registry(self.state_path, state)
        return record

    @staticmethod
    def _find(records: Any, identifier: str, kind: str) -> dict[str, Any]:
        if isinstance(records, list):
            for record in records:
                if isinstance(record, dict) and record.get("id") == identifier:
                    return record
        raise ValueError(f"Unknown {kind}: {identifier}")

    @staticmethod
    def _require_identifier(identifier: str) -> None:
        if not IDENTIFIER_PATTERN.fullmatch(identifier):
            raise ValueError("IDs must use lowercase letters, digits, hyphens, or underscores")

    @staticmethod
    def _paper_note(identifier: str, title: str, url: str, status: str) -> str:
        return f"""---
paper_id: {identifier}
registry_status_at_creation: {status}
---

# {title}

Primary source: {url}

## Access report

FULL_TEXT_REQUIRED

TODO — record the accessible version, access date, and whether evidence is metadata, abstract, or full text.

## Why this work is relevant

TODO

## Mechanism and assumptions

TODO

## Evidence and experimental protocol

TODO

## Relationship to project claims

TODO — identify what is already known, what differs, and which claim IDs are affected.

## Limitations and possible falsifiers

TODO

## Quotable facts

Record paraphrases with page/section pointers. Keep direct quotations short.
"""

    @staticmethod
    def _bibtex(
        identifier: str,
        title: str,
        year: int,
        authors: list[str],
        url: str,
        venue: str | None,
    ) -> str:
        venue_line = f"  howpublished = {{{venue}}},\n" if venue else ""
        author_text = " and ".join(authors)
        return (
            f"\n@misc{{{identifier},\n"
            f"  title = {{{title}}},\n"
            f"  author = {{{author_text}}},\n"
            f"  year = {{{year}}},\n"
            f"{venue_line}"
            f"  url = {{{url}}}\n"
            "}\n"
        )

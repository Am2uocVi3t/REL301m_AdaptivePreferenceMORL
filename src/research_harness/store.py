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
EXPERIMENT_STATUSES = {"planned", "running", "complete", "failed", "blocked"}
BLOCKER_STATUSES = {"open", "resolved"}
IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_registry(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected a YAML mapping: {path}")
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

        claims = documents["claims"].get("claims")
        claim_ids = self._validate_records("claims", claims, CLAIM_STATUSES, errors)
        if isinstance(claims, list):
            for claim in claims:
                if isinstance(claim, dict):
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
                if paper.get("status") == "read":
                    note = paper.get("note")
                    if not isinstance(note, str) or not (self.root / note).exists():
                        errors.append(f"papers: {paper.get('id')} is read but has no existing note")
                    elif "TODO" in (self.root / note).read_text(encoding="utf-8"):
                        errors.append(f"papers: {paper.get('id')} is read but its note is incomplete")

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
    ) -> Path:
        self._require_identifier(identifier)
        if source_type not in PAPER_SOURCE_TYPES:
            raise ValueError(f"Invalid source type: {source_type}")
        if status not in PAPER_STATUSES:
            raise ValueError(f"Invalid paper status: {status}")
        for field_name, value in {"title": title, "url": url, "venue": venue or ""}.items():
            if "\n" in value or "{" in value or "}" in value:
                raise ValueError(f"{field_name} cannot contain newlines or braces")
        document = self.papers()
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
                "url": url,
                "tags": tags,
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
            note = self.root / paper["note"]
            if not note.exists() or "TODO" in note.read_text(encoding="utf-8"):
                raise ValueError("A paper can be marked read only after its structured note is complete")
        paper["status"] = status
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
status: {status}
---

# {title}

Primary source: {url}

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

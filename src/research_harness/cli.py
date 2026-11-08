from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from src.research_harness.render import render_handoff, render_status
from src.research_harness.store import (
    CLAIM_STATUSES,
    EXPERIMENT_STATUSES,
    PAPER_ACCESS_STATUSES,
    PAPER_EVIDENCE_LEVELS,
    PAPER_SOURCE_TYPES,
    PAPER_STATUSES,
    ResearchStore,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="research-harness",
        description="Manage the Git-native research state, evidence, and cross-chat handoff.",
    )
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root (default: current directory)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("doctor", help="Validate registries, references, and required files")
    subparsers.add_parser("status", help="Show the current research state")

    roadmap = subparsers.add_parser("roadmap", help="Inspect the versioned research roadmap")
    roadmap_subparsers = roadmap.add_subparsers(dest="roadmap_command", required=True)
    roadmap_subparsers.add_parser("list")

    handoff = subparsers.add_parser("handoff", help="Render the self-contained prompt for a new chat")
    handoff.add_argument("--write", action="store_true", help="Write docs/research/HANDOFF_PROMPT.md")

    claim = subparsers.add_parser("claim", help="Inspect or update research claims")
    claim_subparsers = claim.add_subparsers(dest="claim_command", required=True)
    claim_subparsers.add_parser("list")
    claim_set = claim_subparsers.add_parser("set-status")
    claim_set.add_argument("id")
    claim_set.add_argument("status", choices=sorted(CLAIM_STATUSES))
    claim_set.add_argument("--evidence", action="append", default=[])

    paper = subparsers.add_parser("paper", help="Manage literature metadata and structured notes")
    paper_subparsers = paper.add_subparsers(dest="paper_command", required=True)
    paper_subparsers.add_parser("list")
    paper_add = paper_subparsers.add_parser("add")
    paper_add.add_argument("--id", required=True)
    paper_add.add_argument("--title", required=True)
    paper_add.add_argument("--year", required=True, type=int)
    paper_add.add_argument("--author", action="append", required=True)
    paper_add.add_argument("--url", required=True)
    paper_add.add_argument("--source-type", choices=sorted(PAPER_SOURCE_TYPES), required=True)
    paper_add.add_argument("--venue")
    paper_add.add_argument("--status", choices=sorted(PAPER_STATUSES), default="queued")
    paper_add.add_argument("--tag", action="append", default=[])
    paper_add.add_argument("--claim", action="append", default=[])
    paper_set = paper_subparsers.add_parser("set-status")
    paper_set.add_argument("id")
    paper_set.add_argument("status", choices=sorted(PAPER_STATUSES))
    paper_access = paper_subparsers.add_parser("set-access")
    paper_access.add_argument("id")
    paper_access.add_argument("--access-status", choices=sorted(PAPER_ACCESS_STATUSES), required=True)
    paper_access.add_argument("--evidence-level", choices=sorted(PAPER_EVIDENCE_LEVELS), required=True)
    paper_access.add_argument("--full-text-required", choices=("yes", "no"), required=True)
    paper_access.add_argument("--note", required=True, help="Access outcome, attempted sources, or supplied version")

    experiment = subparsers.add_parser("experiment", help="Manage the planned and executed experiment registry")
    experiment_subparsers = experiment.add_subparsers(dest="experiment_command", required=True)
    experiment_subparsers.add_parser("list")
    experiment_add = experiment_subparsers.add_parser("add")
    experiment_add.add_argument("--id", required=True)
    experiment_add.add_argument("--title", required=True)
    experiment_add.add_argument("--protocol", required=True)
    experiment_add.add_argument("--claim", action="append", default=[])
    experiment_add.add_argument("--status", choices=sorted(EXPERIMENT_STATUSES), default="planned")
    experiment_set = experiment_subparsers.add_parser("set-status")
    experiment_set.add_argument("id")
    experiment_set.add_argument("status", choices=sorted(EXPERIMENT_STATUSES))
    experiment_set.add_argument("--artifact")

    session = subparsers.add_parser("session", help="Close a work session and refresh the handoff")
    session_subparsers = session.add_subparsers(dest="session_command", required=True)
    session_close = session_subparsers.add_parser("close")
    session_close.add_argument("--summary", required=True)
    session_close.add_argument("--next", action="append", required=True, dest="next_actions")
    session_close.add_argument("--blocker", action="append", default=[])
    session_close.add_argument("--write-handoff", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    store = ResearchStore(args.root)
    try:
        if args.command == "doctor":
            errors = store.validate()
            if errors:
                print("Research harness validation failed:", file=sys.stderr)
                for error in errors:
                    print(f"- {error}", file=sys.stderr)
                return 1
            print("Research harness validation passed.")
            return 0
        if args.command == "status":
            print(render_status(store))
            return 0
        if args.command == "handoff":
            handoff = render_handoff(store)
            if args.write:
                store.handoff_path.parent.mkdir(parents=True, exist_ok=True)
                store.handoff_path.write_text(handoff, encoding="utf-8")
                print(f"Wrote {store.handoff_path.relative_to(store.root)}")
            else:
                print(handoff, end="")
            return 0
        if args.command == "roadmap":
            for phase in store.roadmap().get("phases", []):
                print(f"{phase['id']}\t{phase['status']}\t{phase['title']}")
            return 0
        if args.command == "claim":
            return _handle_claim(store, args)
        if args.command == "paper":
            return _handle_paper(store, args)
        if args.command == "experiment":
            return _handle_experiment(store, args)
        if args.command == "session":
            return _handle_session(store, args)
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 2


def _handle_claim(store: ResearchStore, args: argparse.Namespace) -> int:
    if args.claim_command == "list":
        for claim in store.claims().get("claims", []):
            print(f"{claim['id']}\t{claim['status']}\t{claim['title']}")
    else:
        store.set_claim_status(args.id, args.status, args.evidence)
        print(f"Updated claim {args.id} to {args.status}")
    return 0


def _handle_paper(store: ResearchStore, args: argparse.Namespace) -> int:
    if args.paper_command == "list":
        for paper in store.papers().get("papers", []):
            requirement = "full-text-required" if paper["full_text_required"] else "full-text-available"
            print(
                f"{paper['id']}\t{paper['status']}\t{paper['evidence_level']}\t{requirement}"
                f"\t{paper['year']}\t{paper['title']}"
            )
    elif args.paper_command == "add":
        note = store.add_paper(
            identifier=args.id,
            title=args.title,
            year=args.year,
            authors=args.author,
            url=args.url,
            source_type=args.source_type,
            venue=args.venue,
            status=args.status,
            tags=args.tag,
            claim_ids=args.claim,
        )
        print(f"Added paper {args.id}; complete {note.relative_to(store.root)}")
    elif args.paper_command == "set-status":
        store.set_paper_status(args.id, args.status)
        print(f"Updated paper {args.id} to {args.status}")
    else:
        store.set_paper_access(
            args.id,
            args.access_status,
            args.evidence_level,
            args.full_text_required == "yes",
            args.note,
        )
        print(f"Updated paper access for {args.id}")
    return 0


def _handle_experiment(store: ResearchStore, args: argparse.Namespace) -> int:
    if args.experiment_command == "list":
        for experiment in store.experiments().get("experiments", []):
            print(f"{experiment['id']}\t{experiment['status']}\t{experiment['title']}")
    elif args.experiment_command == "add":
        store.add_experiment(
            identifier=args.id,
            title=args.title,
            protocol=args.protocol,
            claim_ids=args.claim,
            status=args.status,
        )
        print(f"Added experiment {args.id}")
    else:
        store.set_experiment_status(args.id, args.status, args.artifact)
        print(f"Updated experiment {args.id} to {args.status}")
    return 0


def _handle_session(store: ResearchStore, args: argparse.Namespace) -> int:
    store.close_session(args.summary, args.next_actions, args.blocker)
    if args.write_handoff:
        store.handoff_path.write_text(render_handoff(store), encoding="utf-8")
        print(f"Closed session and wrote {store.handoff_path.relative_to(store.root)}")
    else:
        print("Closed session. Run `handoff --write` to refresh the checked-in prompt.")
    return 0

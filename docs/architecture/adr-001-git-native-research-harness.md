# ADR-001: Git-Native Research Harness

Status: accepted
Date: 2026-10-15

## Context

The project will span many coding and research chats. Conversation history is not a reliable source of truth, while a full autonomous-agent platform would add infrastructure and obscure scientific accountability. Literature support also needs durable metadata and notes without committing copyrighted PDFs.

## Decision

Use versioned JSON registries, an append-only JSONL session log, structured Markdown notes, a shared BibTeX file, and a standard-library Python CLI. Generate one self-contained handoff prompt for fresh chats. Keep execution artifacts outside Git and link them through provenance-aware experiment records.

The CLI validates semantic links—claim IDs, protocol paths, evidence paths, paper-note status—and does not infer that an implementation or smoke test establishes empirical support.

## Consequences

- State changes are reviewable in pull requests and available without an external service.
- A new chat has a deterministic bootstrap path and still verifies live Git state.
- Literature search and experiment execution remain deliberate agent/human work.
- Registry merge conflicts and manual narrative synchronization remain possible; `doctor` and session-close conventions reduce, but do not eliminate, that risk.
- If concurrent teams or automated schedulers later require transactional state, this design can be migrated from the versioned schemas rather than expanded into an accidental workflow engine.

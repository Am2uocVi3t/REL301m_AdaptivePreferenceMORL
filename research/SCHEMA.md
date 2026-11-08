# Research Data Contract

The `research/` tree is the machine-readable control plane for the project. All registries are JSON with `schema_version: 1`; corresponding JSON Schemas live under `research/schemas/`. The Python doctor uses only the standard library and performs semantic checks in addition to these structural contracts.

## Authority and lifecycle

- `state.json` tracks the current phase, blockers, and next actions.
- `roadmap.json` defines Phase 0–7 deliverables, gates, evidence, blockers, and allowed transitions.
- `claims.json` separates hypotheses, implementation, validation, and empirical support while recording antecedents and bounded novelty judgments.
- `literature/index.json` stores bibliographic metadata, affected claim IDs, and structured-note paths; `library.bib` supports manuscript tooling.
- `literature/search-queries.json` is a starting queue, while `SEARCH_LOG.md` records searches actually performed.
- `experiments/registry.json` connects planned or executed experiments to frozen protocols and claim IDs.
- `sessions/session-log.jsonl` is append-only. Each line captures one completed work session and its Git snapshot.

Use the CLI instead of editing a status field casually. A status of `read`, `complete`, `validated`, or `experimentally_supported` is an evidence claim, not a task-progress decoration.

An `experimentally_supported` claim must include an `artifact:<versioned-path>` evidence entry. A `read` paper must have `evidence_level: full_text`, a verified full-text access status, `full_text_required: false`, and a completed structured note with no `TODO` marker. A `complete` experiment must name its artifact. Exactly one roadmap phase is active; a completed phase must name existing evidence paths and may transition only to registered next phases.

Literature access is explicit:

- `access_status`: `not_checked`, `open_full_text`, `author_manuscript`, `user_supplied`, `paywalled`, or `blocked`;
- `evidence_level`: `metadata_only`, `abstract_only`, or `full_text`;
- `full_text_required`: whether the agent still needs an authorized full text to complete analysis;
- `access_note`: sources attempted, the accessible version, or the exact access blocker.

Metadata or an abstract may support screening, never a completed reading or a strong novelty conclusion.

## Artifact boundary

Git stores metadata, protocols, compact raw-result summaries where appropriate, and provenance. Large checkpoints, run outputs, and copyrighted paper PDFs remain outside Git. A registered artifact path or URI must be immutable enough for another researcher to retrieve the underlying evidence.

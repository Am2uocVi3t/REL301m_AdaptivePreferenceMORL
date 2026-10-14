# Research Data Contract

The `research/` tree is the machine-readable control plane for the project. All registries are JSON with `schema_version: 1`; corresponding JSON Schemas live under `research/schemas/`. The Python doctor uses only the standard library and performs semantic checks in addition to these structural contracts.

## Authority and lifecycle

- `state.json` tracks the current phase, blockers, and next actions.
- `claims.json` separates hypotheses, implementation, validation, and empirical support.
- `literature/index.json` stores bibliographic metadata and points to structured notes; `library.bib` supports manuscript tooling.
- `literature/search-queries.json` is a starting queue, while `SEARCH_LOG.md` records searches actually performed.
- `experiments/registry.json` connects planned or executed experiments to frozen protocols and claim IDs.
- `sessions/session-log.jsonl` is append-only. Each line captures one completed work session and its Git snapshot.

Use the CLI instead of editing a status field casually. A status of `read`, `complete`, `validated`, or `experimentally_supported` is an evidence claim, not a task-progress decoration.

An `experimentally_supported` claim must include an `artifact:<versioned-path>` evidence entry. A `read` paper must have a completed structured note with no `TODO` marker, and a `complete` experiment must name its artifact.

## Artifact boundary

Git stores metadata, protocols, compact raw-result summaries where appropriate, and provenance. Large checkpoints, run outputs, and copyrighted paper PDFs remain outside Git. A registered artifact path or URI must be immutable enough for another researcher to retrieve the underlying evidence.

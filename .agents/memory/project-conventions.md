---
type: project
created: 2026-05-25
updated: 2026-10-15
---

# Project Conventions

## Git Workflow
- Always create a new dedicated branch for major code changes.
- Branch name format should follow: `feature/[task-slug]` or `fix/[bug-slug]`.
- Preserve unrelated working-tree changes and do not commit or push unless requested.

## Scientific Workflow

- Treat code, protocol files, tests, and executed artifacts as stronger evidence than Markdown claims.
- Label work as `Planned`, `Implemented`, `Validated`, or `Experimentally supported` accurately.
- Never use the final test split for tuning, checkpoint selection, normalization, or reference-point selection.
- Keep preference generalization separate from environment/dynamics generalization.
- Match interaction, update, evaluation, and tuning budgets across methods.
- Retain raw and discounted vector returns with configuration, dependency, checkpoint, and Git provenance.

## Repository Hygiene

- Keep the repository root limited to entry points and project configuration.
- Put research status in `docs/research/`, audit procedures in `docs/audit/`, and proposal records in `docs/proposal/`.
- Do not commit generated caches, checkpoints, logs, or experiment outputs.
- Update the canonical project status after verified milestones or newly discovered blockers.

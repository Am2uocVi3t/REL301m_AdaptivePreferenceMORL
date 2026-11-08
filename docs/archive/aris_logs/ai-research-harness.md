# AI Research Harness Implementation Plan

Goal: add a small Git-native control plane that keeps research claims, literature, experiments, sessions, and cross-chat handoff synchronized without storing paper PDFs.

## Tasks

- [x] Define versioned JSON/JSONL schemas and seed the current verified project state.
- [x] Implement a Python CLI for validation, status, handoff, paper, claim, experiment, and session workflows.
- [x] Generate a copyable handoff prompt and document the end-to-end research loop.
- [x] Integrate the harness into `AGENTS.md`, repository documentation, Git ignores, and persistent agent memory.
- [x] Add unit/integration tests for validation and mutation workflows.
- [x] Run format, lint, typing, tests, security, compile, manifest, and repository consistency checks.

## Verification

The work is complete when `research doctor` passes, a generated handoff is self-contained, CLI mutations are covered in temporary workspaces, `.agents` manifests are current, and the repository's full validation suite passes.

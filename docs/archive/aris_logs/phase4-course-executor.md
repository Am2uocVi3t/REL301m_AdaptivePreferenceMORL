# Phase 4 Course Executor

## Goal
Add a fail-closed, qualification-aware, job-level resumable executor for the frozen course manifest without starting course-scale experiments.

## Tasks
- [x] Write RED tests for manifest/gate hash validation, explicit selection, authorization, atomic status, resume, and corrupted/missing artifacts. → Verify: focused tests failed before implementation and pass afterward.
- [x] Implement the executor core and CLI with Python 3.11 enforcement, command allowlisting, explicit acknowledgement, and bounded job selection. → Verify: focused tests pass.
- [x] Add a non-evidence one-job smoke mode that rewrites only runtime/output arguments and cannot mark a course job complete. → Verify: a 20-step PCQN smoke finished in the ignored smoke directory and a second invocation skipped it with `attempts: 1`.
- [x] Add explicit final-artifact paths to the operational manifest and rebind the qualification gate hash without changing the frozen study config. → Verify: deterministic regeneration produced manifest SHA-256 `02cab777...c586` and all gate hashes resolve.
- [x] Document job-level resume semantics and the absence of within-training checkpoint resume. → Verify: README, Kaggle guide, status, and architecture agree.
- [x] Run the complete Python 3.11 quality gate and refresh the research handoff. → Verify: Ruff, MyPy, 65 tests, Bandit, compileall, and diff checks pass; harness closure refreshes the handoff.

## Done When
- [x] The executor safely dry-runs the 30-job primary block, one isolated smoke job executes, zero course jobs execute, and all evidence boundaries remain explicit.

## Notes
- Actual course execution requires `--execute`, the exact study acknowledgement, explicit selectors, and an explicit maximum job count.
- Resume is between independent seeded jobs only; training-state resume remains unsupported.

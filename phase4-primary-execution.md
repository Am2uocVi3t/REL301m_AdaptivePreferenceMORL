# Phase 4 Primary Execution

## Goal
Review and checkpoint the frozen evidence stack, then launch the 30-job primary PCQN block without changing the study contract or accessing final-test data.

## Tasks
- [x] Audit every tracked/untracked path for scope, generated artifacts, secrets, and frozen-hash consistency. → Verify: only source, config, documentation, and compact versioned evidence remain; no binaries or common credential signatures are staged.
- [x] Re-run the complete Python 3.11 quality gate before committing. → Verify: pip check, doctor, Ruff, MyPy, 65 tests, Bandit, compileall, and diff checks pass.
- [x] Commit the Phase 2/3 evidence stack and Phase 4 executor on the dedicated branch. → Verify: commit `c4a90d6` succeeds and the worktree contains no pre-existing implementation changes.
- [x] Estimate primary-block runtime/storage from prior pilot evidence and validate the exact 30-job selection. → Verify: 78 GB disk and 13 GiB available RAM pass the local resource check; executor dry-run reports exactly 30 jobs.
- [x] Launch the primary block through the frozen executor with exact acknowledgement and `--max-jobs 30`. → Verify: status is bound to manifest SHA-256 `02cab777...c586`, the full-budget canary completed, and no test split is used.
- [x] Monitor failures and preserve completed job hashes; do not mutate the frozen protocol in response to outcomes. → Verify: 30/30 jobs complete, zero failed, and all recorded final-checkpoint hashes match.
- [x] Close the session with evidence-bounded state and a refreshed handoff. → Verify: research harness passes while the experiment remains `running`.

## Done When
- [x] The reviewed stack is committed and the 30-job primary block completed with intact hash-bound status and no final-test access.

## Notes
- Course execution is serial and job-level resumable; interrupted training cannot resume within a job.
- Validation output may guide checkpoint locking only after all planned primary jobs complete. Final-test evaluation stays prohibited.

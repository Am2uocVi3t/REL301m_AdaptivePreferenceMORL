# Minecart Remediation Execution

## Goal
Execute the predeclared three-seed Minecart backbone qualification through a validation-only, hash-bound, resumable workflow.

## Tasks
- [x] Freeze every training argument and bind the qualification plan to the diagnosis and protocol hashes.
- [x] Add a fail-closed runner that previews by default and requires exact plan acknowledgement, explicit seeds, and a positive seed cap.
- [x] Add a resumable validation auditor that verifies checkpoints, budgets, provenance, raw returns, checkpoint selection, and the fixed pass rule.
- [x] Add regression tests for authorization, command drift, test-split exclusion, resume safety, and pass/fail aggregation.
- [x] Run the complete repository quality gate under the pinned Python 3.11 environment.
- [ ] Commit the clean pre-execution snapshot before launching training.
- [ ] Execute only seeds 20264001–20264003 and produce the hash-bound qualification decision.
- [ ] Synchronize the registry, roadmap, status, memory, session log, and handoff with the observed outcome.

## Done When
- [ ] Exactly three predeclared Uniform-PCQN runs are accounted for with no final-test or shifted-environment access.
- [ ] A versioned qualification artifact records `passed: true` only if every seed meets the fixed 5% per-objective rule; otherwise Phase 4 remains blocked.
- [ ] Matrix v1 remains permanently blocked and no course-comparison claim is promoted.

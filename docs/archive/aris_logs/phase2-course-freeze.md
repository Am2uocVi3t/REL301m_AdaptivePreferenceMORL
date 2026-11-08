# Phase 2 Course Freeze and Qualification

## Goal
Freeze an executable, reviewable paired course matrix and analysis contract, then qualify GPI-LS and every enabled dynamics shift without running course-scale experiments.

## Tasks
- [x] Add a versioned study config/schema with paired seeds, fixed budgets, PCQN arms, comparator eligibility, checkpoint rules, and analysis choices. → Verify: schema and semantic validation pass.
- [x] Generate and version the dry-run matrix manifest without executing jobs. → Verify: expected paired jobs, unique outputs, protocol hashes, and zero completed jobs.
- [x] Implement the geometry-only allocation score and per-objective controllability metric named by the freeze. → Verify: focused unit tests pass.
- [x] Run a bounded GPI-LS training smoke test under Python 3.11 and record behavioral evidence. → Verify: training performs updates/steps and exits successfully or a concrete incompatibility is documented.
- [x] Behaviorally compare nominal and every enabled dynamics shift under controlled action traces. → Verify: deterministic evidence shows each shift changes its intended transition behavior.
- [x] Update roadmap, registries, status, memory, and handoff using only generated evidence. → Verify: research harness and full quality gate pass.

## Done When
- [x] Phase 2 is closed only if the frozen matrix passes review; Phase 3 records baseline and shift qualification evidence, and no course-scale run has executed.

## Notes
- Five paired seeds are frozen for the course matrix; analysis is estimation-first because five pairs cannot support a two-sided exact sign-flip result below 0.05.
- Final-test data remains inaccessible until model/hyperparameter selection is locked.

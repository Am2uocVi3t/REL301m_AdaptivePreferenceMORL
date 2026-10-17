---
type: project
created: 2026-10-15
updated: 2026-10-17
---

# Research Status

## ARIS bootstrap, 2026-10-17

- Branch `codex/aris-integration`; 84 pinned Codex skills and eight Claude overlays copied project-locally; existing 47 top-level skills preserved. Shared filesystem rejects symlinks, so use upstream copy installer, not reconcile of the interrupted symlink install.
- Read `docs/research/ARIS_INTEGRATION.md`, policy `configs/aris/project.json`, tooling evidence `research/qualification/aris_bootstrap_v1.json` and root plan `aris-integration.md`.
- Preflight verifies content against the pin, canonical harness, fresh quota and machine-readable action authority; it dispatches nothing and is not an OS sandbox. The 2026-10-17 authorization permits only the separately versioned F1 scope/protocol amendment, implementation, qualification and six paired local runs.
- Paid review and unattended scheduling remain disabled. F2, checkpoint lock and final test remain conditional on F1 all-seeds retention plus source audit and their explicit unlocks. Six roles are on demand; no persistent team was started.

## Current phase

- Phases 0–3 are complete; Phase 4 is active. The 30-job primary PCQN block and its validation re-evaluation are complete, but Minecart degeneracy blocks checkpoint locking and the remaining 120 jobs.
- The defensible contribution is a controlled study of which preference-allocation signals identify hard, uncertain, or learnable regions.
- No multi-seed course result or publication-level empirical claim has been established yet.
- A Git-native AI research harness now keeps claim, literature, experiment, blocker, session, and handoff state synchronized across chats.
- The primary-source map registers 22 full-text readings after a focused 2026 refresh. PBMORL is direct prior art for adaptive preference-task reallocation, MPFT for sparse-front training, and CAPQL/MORL-FB/D³PO use fixed preference sampling rather than the repository's four-signal scheduler. Signal claims are incremental; exact combined-rule novelty remains unresolved.

## Historical implementation and experiment progression (15–17 October)

- Core PCQN training, safe checkpoint loading, fixed-protocol evaluation, and the paired-seed matrix runner executed end to end.
- The complete pinned dependency set installed under Python 3.11.17 and passed `pip check`.
- The 103-test unit and integration suite, including analytic PER/Huber equivalence, non-finite PER-parameter rejection, validation-audit fail-closed, exact-preference/metric binding, and resume tests, passes under Python 3.11.17.
- Ruff, MyPy, Bandit, compileall, and Git whitespace checks passed.
- MO-Lunar-Lander and Minecart reset/step smoke tests passed.
- The six-job v1 pilot completed 600,000 training interactions and 960 validation episodes. LunarLander was non-degenerate, but all 480 Minecart validation returns had zero ore objectives, so calibration failed closed and no value was frozen.
- Uniform-PCQN now samples uniformly from the same fixed candidate pool as adaptive methods. A one-seed 100,000-interaction fixed-pool Minecart diagnostic still produced zero ore reward in all 160 validation episodes.
- Source-aware v2 resolved the blocker: three independent LunarLander pilots and a deterministic versioned Minecart front passed calibration, both protocols were frozen, and post-freeze train/evaluate/HV smoke tests passed.
- The frozen course study contains 150 non-executed planned jobs across two environments, five paired seeds, 13 PCQN arms, and two comparator slots; analysis is estimation-first and final test remains locked.
- Envelope and GPI-LS behavior passed 200-interaction Python 3.11 smokes on both course environments, and every enabled LunarLander shift changed controlled transition/reward traces over three seeds.
- Before course execution, the qualification-aware executor dry-ran the 30-job primary block. One isolated 20-step smoke completed and resume-skipped by artifact hash with `course_evidence: false`.
- After commit `c4a90d6`, the first 500,000-interaction Uniform-PCQN LunarLander course job completed with a hash-verified final checkpoint, and the remaining primary selection began through job-level resume. This is runtime progress, not a comparative result.
- The primary selection finished all 30 jobs (15,000,000 interactions) with zero executor failures and all final-checkpoint hashes verified.
- The source audit passed for 30 jobs and 300 periodic checkpoints. All 300 were deterministically re-evaluated on nominal validation data with raw and discounted returns retained and logged metrics reproduced.
- Aggregation failed closed because objectives 0 and 1 were constant zero at every checkpoint in all 15 Minecart runs. The 15 LunarLander runs were non-degenerate, but the atomic lock decision records zero locks; final test and the remaining 120 jobs stay blocked.
- The user chose to retain Minecart in the course study. The next gate is therefore a non-test diagnosis and predeclared Minecart remediation, not environment exclusion.
- The non-test Minecart diagnosis is complete: all 15 selected training archives contain positive ore, but all 14,400 greedy validation episodes return zero ore and representative ensemble/head policies never select `Mine`. The evidence supports common sparse delayed-credit backbone underqualification, not a broken reward path or allocation-arm effect.
- Minecart remediation v1 completed all three fresh validation-only Uniform-PCQN seeds and failed the all-seeds gate. Seeds 20264001 and 20264002 had zero ore at their selected checkpoints; seed 20264003 passed with 28/160 positive episodes per ore objective.
- Checkpoint-wide v1 evidence contains small, transient ore-delivery pockets in seeds 20264002 and 20264003, so a larger budget alone is not justified; v2 must target retention or delayed credit under a fresh predeclaration.
- A predeclared validation-only behavior probe evaluated seven v1 checkpoints over 1,120 episodes. Seed 20264003 moved from 35 successful-mining/27 delivery episodes at step 600,000 to zero `Mine` actions at steps 700,000 and 1,000,000; seed 20264002 showed smaller transient pockets.
- Remediation v2 was predeclared as a single-factor proportional prioritized-replay change with fresh seeds and unchanged v1 budgets, checkpoint selection, and 5% pass rule. A pre-execution amendment retained v1's masked Huber loss after correcting contradictory squared-TD wording. Its exact buffer/loss contract and fail-closed runner/auditor passed review; a non-evidence seed-9192 smoke completed 20 interactions and 17 updates. The later authorized execution failed as recorded below.
- Course matrix v1 is permanently blocked by a post-validation executor gate. Final test remains locked and no course-comparison claim was promoted.

## Open blockers

- Minecart v2 completed and failed: all three selected step-1M checkpoints had 0/160 positive ore episodes and zero distinct positive values. Authorization `aris-full-workflow-20261017` now permits a distinct, versioned F1 successful-episode replay feasibility amendment, implementation, deterministic qualification, and six paired local training/nominal-validation runs. This does not revive v2 or unlock matrix v1, checkpoint lock, final test, F2, paid review, unattended scheduling, or submission.
- Minecart non-nominal dynamics shifts remain disabled until a valid constructor-level intervention is identified and behaviorally tested.

## Verified outcome on 2026-10-17

- Three complete v2 runs: 3M training interactions, 2,985,003 updates, 6,310,626 curriculum-evaluation steps, 4,710,905 training validation steps. Independent 30-checkpoint re-audit: 4,800 episodes / 4,710,905 steps; 4,710 timeouts (98.125%).
- Interrupted first seed11 attempt is preserved: at least 27,044 logged interactions and 32,000 curriculum-evaluation steps; exact unflushed expenditure unknown. Do not call 3M the complete tuning cost.
- Historical statements above that v2 had not run describe the pre-execution review. Current evidence: `research/qualification/minecart_pcqn_backbone_v2.json`, failed, no unlocks; execution source commit25328e8 and plan c28b0de... match.
- External ARIS setup: `/home/hei/.local/share/rel301m-aris-setup`. Smoke plus workflow consultation reported total CLI usage $0.2369042, Console reconciliation pending; paid policy disabled. Full research integration pending, not submission-ready.
- User: initial progress report due 19 October in `paper/REL301m`; local demo plus backup video; autonomous evidence-grounded routine research. Unrelated template moved recoverably to `/home/hei/.local/share/rel301m-paper-backups/2026-10-17-original/`.
- Current execution branch is `codex/aris-full-workflow`, intended as a stacked PR on `feature/ai-research-harness`; commit/push/PR are explicitly authorized before F1 implementation/training.

## Canonical handoff

Run `python scripts/research_harness.py doctor`, `status`, and `roadmap list`, then read `docs/research/PROJECT_STATUS.md` and `docs/research/ROADMAP.md`. For a fresh chat, copy the complete prompt in `docs/research/HANDOFF_PROMPT.md` and verify its snapshot against live Git state.

---
type: project
created: 2026-10-15
updated: 2026-10-16
---

# Research Status

## Current phase

- Phases 0–3 are complete; Phase 4 is active. The 30-job primary PCQN block is complete, while validation aggregation, checkpoint locking, and 120 ablation/comparator jobs remain.
- The defensible contribution is a controlled study of which preference-allocation signals identify hard, uncertain, or learnable regions.
- No multi-seed course result or publication-level empirical claim has been established yet.
- A Git-native AI research harness now keeps claim, literature, experiment, blocker, session, and handoff state synchronized across chats.
- The primary-source map registers 22 full-text readings after a focused 2026 refresh. PBMORL is direct prior art for adaptive preference-task reallocation, MPFT for sparse-front training, and CAPQL/MORL-FB/D³PO use fixed preference sampling rather than the repository's four-signal scheduler. Signal claims are incremental; exact combined-rule novelty remains unresolved.

## Verified on 2026-10-16

- Core PCQN training, safe checkpoint loading, fixed-protocol evaluation, and the paired-seed matrix runner executed end to end.
- The complete pinned dependency set installed under Python 3.11.17 and passed `pip check`.
- Unit and integration suite passed with 65 tests, including 18 research-harness, 11 calibration, course-matrix/executor, and fixed-pool regression tests, under Python 3.11.17.
- Ruff, MyPy, Bandit, compileall, and Git whitespace checks passed.
- MO-Lunar-Lander and Minecart reset/step smoke tests passed.
- The six-job v1 pilot completed 600,000 training interactions and 960 validation episodes. LunarLander was non-degenerate, but all 480 Minecart validation returns had zero ore objectives, so calibration failed closed and no value was frozen.
- Uniform-PCQN now samples uniformly from the same fixed candidate pool as adaptive methods. A one-seed 100,000-interaction fixed-pool Minecart diagnostic still produced zero ore reward in all 160 validation episodes.
- Source-aware v2 resolved the blocker: three independent LunarLander pilots and a deterministic versioned Minecart front passed calibration, both protocols were frozen, and post-freeze train/evaluate/HV smoke tests passed.
- The frozen course study contains 150 non-executed planned jobs across two environments, five paired seeds, 13 PCQN arms, and two comparator slots; analysis is estimation-first and final test remains locked.
- Envelope and GPI-LS behavior passed 200-interaction Python 3.11 smokes on both course environments, and every enabled LunarLander shift changed controlled transition/reward traces over three seeds.
- Before course execution, the qualification-aware executor dry-ran the 30-job primary block. One isolated 20-step smoke completed and resume-skipped by artifact hash with `course_evidence: false`.
- After commit `c4a90d6`, the first 500,000-interaction Uniform-PCQN LunarLander course job completed with a hash-verified final checkpoint, and the remaining primary selection began through job-level resume. This is runtime progress, not a comparative result.
- The primary selection finished all 30 jobs (15,000,000 interactions) with zero executor failures and all final-checkpoint hashes verified. No validation aggregation, checkpoint lock, final-test evaluation, or comparative claim has yet followed.

## Open blockers

- Primary controls are trained, but their validation evidence is not aggregated and checkpoints are not locked. The remaining 100 signal/target PCQN jobs and 20 qualified baseline jobs have not run.
- Minecart non-nominal dynamics shifts remain disabled until a valid constructor-level intervention is identified and behaviorally tested.

## Canonical handoff

Run `python scripts/research_harness.py doctor`, `status`, and `roadmap list`, then read `docs/research/PROJECT_STATUS.md` and `docs/research/ROADMAP.md`. For a fresh chat, copy the complete prompt in `docs/research/HANDOFF_PROMPT.md` and verify its snapshot against live Git state.

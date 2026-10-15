---
type: project
created: 2026-10-15
updated: 2026-10-15
---

# Research Status

## Current phase

- Phase 1 claim/antecedent mapping is complete; Phase 2 pilot calibration and protocol freeze is active but execution is blocked by Python 3.11 dependency pins.
- The defensible contribution is a controlled study of which preference-allocation signals identify hard, uncertain, or learnable regions.
- No multi-seed course result or publication-level empirical claim has been established yet.
- A Git-native AI research harness now keeps claim, literature, experiment, blocker, session, and handoff state synchronized across chats.
- The primary-source map registers 22 full-text readings after a focused 2026 refresh. PBMORL is direct prior art for adaptive preference-task reallocation, MPFT for sparse-front training, and CAPQL/MORL-FB/D³PO use fixed preference sampling rather than the repository's four-signal scheduler. Signal claims are incremental; exact combined-rule novelty remains unresolved.

## Verified on 2026-10-15

- Core PCQN training, safe checkpoint loading, fixed-protocol evaluation, and the paired-seed matrix runner executed end to end.
- Unit and integration suite passed with 39 tests, including 18 research-harness tests; the harness tests also passed on Python 3.11.17.
- Ruff, MyPy, Bandit, compileall, and Git whitespace checks passed.
- MO-Lunar-Lander and Minecart reset/step smoke tests passed.

## Open blockers

- Pilot-only reward scaling and hypervolume reference points must be frozen before final runs.
- Required controls, ablations, close baselines, and paired multi-seed experiments have not been completed.
- GPI-LS runtime is unverified in the current Python 3.14 host because `pycddlib` needs native `cddlib`; the supported experiment environment is Python 3.11 with `libcdd-dev`.
- Minecart non-nominal dynamics shifts remain disabled until a valid constructor-level intervention is identified and behaviorally tested.
- The pinned `numpy==2.5.4` requires Python 3.12+, so `requirements.txt` cannot install on the declared Python 3.11 target; repair and full target-runtime verification are P0 before pilots.

## Canonical handoff

Run `python scripts/research_harness.py doctor`, `status`, and `roadmap list`, then read `docs/research/PROJECT_STATUS.md` and `docs/research/ROADMAP.md`. For a fresh chat, copy the complete prompt in `docs/research/HANDOFF_PROMPT.md` and verify its snapshot against live Git state.

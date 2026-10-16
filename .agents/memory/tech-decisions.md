---
type: project
created: 2026-07-18
updated: 2026-10-16
---

# Technical Decisions

- Python 3.11 is the supported experiment runtime; dependencies are pinned in `requirements.txt`.
- Protocol JSON files are authoritative for environment IDs, reward dimensions/scales, preference generation seeds, return definitions, and frozen reference points.
- The original submitted proposal PDF is immutable historical evidence. The editable proposal v2 is the current research-intent document.
- The algorithm uses a preference-conditioned vector Q-network with per-head Double-DQN targets and masked multi-head replay diversity.
- Adaptive allocation signals are empirical conditioning gap, head disagreement, local coverage/recency, and observed learning progress.
- The geometry-only control uses static inverse kernel density over the fixed preference pool; it does not include sampling history or learner outcomes.
- Allocation effects must be separated through `rollout_only`, `update_only`, and `rollout_and_update` modes.
- Uniform rollout allocation samples uniformly from the same protocol-seeded finite candidate pool as adaptive allocation; fresh per-episode Dirichlet samples are not a matched control.
- High-dimensional hypervolume must use deterministic exact tooling and fail explicitly when unavailable; no unseeded Monte Carlo fallback.
- Hypervolume reference points and reward scaling remain unset until they are frozen from pilot/training evidence without final-test leakage.
- Calibration v1 failed closed on degenerate Minecart ore returns. Accepted calibration v2 uses a versioned deterministic environment reference front when an audited capability exists and otherwise uses an independent validation-only fixed-pool pilot. Both protocols are frozen from the versioned v2 proposal; post-freeze diagnostics cannot revise values. Smoke results are never comparative evidence, and the calibrator cannot edit protocols.
- Course matrix v1 freezes five paired seeds, 500,000 training interactions per job, 13 PCQN arms, two gated comparators, validation-only checkpoint selection, one-time final test, per-objective controllability, and estimation-first paired analysis. Its generated manifest never authorizes execution.
- Course execution is a separate fail-closed boundary: exact study acknowledgement, explicit selectors, an explicit job cap, frozen-input and qualification hashes, atomic status, and completed-artifact hashes are required. Resume is between whole seeded jobs only; smoke outputs are isolated and marked as non-course evidence.
- Course checkpoint evidence is regenerated only on the frozen nominal validation split. Selection is lexicographic by hypervolume, expected utility, then earlier step; raw and discounted returns, preferences, four budget counters, protocol/checkpoint hashes, and degeneracy diagnostics are retained. Any degenerate run blocks the atomic primary lock rather than producing a partial lock.
- Durable cross-chat coordination uses versioned JSON registries under `research/`, an append-only JSONL session log, and the standard-library `scripts/research_harness.py` CLI.
- The generated `docs/research/HANDOFF_PROMPT.md` is a snapshot; agents must compare it with live Git state and regenerate it at the end of substantial sessions.
- Literature management stores primary-source metadata, BibTeX, query logs, and structured notes. Copyrighted paper PDFs are not committed.
- `read`, `complete`, and `experimentally_supported` are evidence-bearing states: completed notes, named experiment artifacts, and `artifact:<versioned-path>` claim evidence are required respectively.
- Literature agents search legal primary-source alternatives autonomously, but never bypass access controls. `read` requires verified full text; otherwise the paper remains `screened`, is flagged `full_text_required`, and is escalated to the user with attempted sources and affected claims.
- `research/roadmap.json` is the machine-readable phase authority. Exactly one phase is active; completion requires existing evidence paths, and future phases cannot be inferred from planned prose.
- Claim novelty records use only `not_novel`, `incremental`, or `unresolved`; literature mapping never promotes an empirical claim.

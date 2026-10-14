---
type: project
created: 2026-07-18
updated: 2026-10-15
---

# Technical Decisions

- Python 3.11 is the supported experiment runtime; dependencies are pinned in `requirements.txt`.
- Protocol JSON files are authoritative for environment IDs, reward dimensions/scales, preference generation seeds, return definitions, and frozen reference points.
- The original submitted proposal PDF is immutable historical evidence. The editable proposal v2 is the current research-intent document.
- The algorithm uses a preference-conditioned vector Q-network with per-head Double-DQN targets and masked multi-head replay diversity.
- Adaptive allocation signals are empirical conditioning gap, head disagreement, local coverage/recency, and observed learning progress.
- Allocation effects must be separated through `rollout_only`, `update_only`, and `rollout_and_update` modes.
- High-dimensional hypervolume must use deterministic exact tooling and fail explicitly when unavailable; no unseeded Monte Carlo fallback.
- Hypervolume reference points and reward scaling remain unset until they are frozen from pilot/training evidence without final-test leakage.

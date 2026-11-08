---
paper_id: teoh2025morl-generalization
evidence_level: full_text
---

# On Generalization Across Environments In Multi-Objective Reinforcement Learning

Primary source: https://openreview.net/forum?id=tuEP424UQ5

## Access report

Open ICLR 2025 full text checked on 2026-10-15.

## Relevance and mechanism

MORL-Generalization separates objective preferences from contexts that change environments and evaluates generalization over held-out contexts/tasks.

## Evidence and relationship to claims

The benchmark establishes the environment-generalization axis but does not isolate preference allocation. `environment-shift-robustness` is incremental only: it asks whether allocation affects locked-checkpoint shift performance while preference generalization remains separate.

## Limitations and falsifiers

Repository shifts are narrower than the benchmark. Equivalent matched-budget studies or no paired robustness effect eliminate the incremental contribution.

Evidence pointer: formalization, benchmark, and experiments.

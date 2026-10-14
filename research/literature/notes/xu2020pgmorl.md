---
paper_id: xu2020pgmorl
evidence_level: full_text
---

# Prediction-Guided Multi-Objective Reinforcement Learning for Continuous Robot Control

Primary source: https://proceedings.mlr.press/v119/xu20h.html

## Access report

Open PMLR full text checked on 2026-10-15.

## Relevance and mechanism

PGMORL is a close allocation antecedent. It maintains multiple policies, learns a performance-prediction model from policy/weight changes, and selects policy-weight tasks predicted to improve the current Pareto set.

## Evidence and relationship to claims

Continuous-control experiments evaluate Pareto quality. Expected improvement already guides weight-task selection, directly bounding `conditioning-gap-allocation`, `learning-progress-allocation`, and `combined-allocation`. The repository differs in using one conditioned network and comparing simpler observable signals.

## Limitations and falsifiers

Its learned predictor and policy population have different compute assumptions. If the empirical gap merely proxies this prediction signal without extra value, the incremental claim weakens.

Evidence pointer: Sections 3–5.

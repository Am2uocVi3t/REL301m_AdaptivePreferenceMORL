---
paper_id: colas2019curious
evidence_level: full_text
---

# CURIOUS: Intrinsically Motivated Modular Multi-Goal Reinforcement Learning

Primary source: https://proceedings.mlr.press/v97/colas19a.html

## Access report

Open PMLR full text checked on 2026-10-15.

## Relevance and mechanism

CURIOUS tracks competence and absolute competence progress per goal module, samples modules using progress, and trains one hindsight-replay policy, avoiding solved and presently unlearnable modules.

## Evidence and relationship to claims

Modular multi-goal experiments bound novelty for `learning-progress-allocation` and `combined-allocation`. The project difference is preference-space estimation and a matched signal comparison.

## Limitations and falsifiers

Module competence differs from dense preference regions. If progress cannot be estimated reliably over preferences, the transfer fails.

Evidence pointer: intrinsic motivation, module-selection, and experiment sections.

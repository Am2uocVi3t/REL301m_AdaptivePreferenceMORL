---
paper_id: jiang2021plr
evidence_level: full_text
---

# Prioritized Level Replay

Primary source: https://proceedings.mlr.press/v139/jiang21b.html

## Access report

Open PMLR full text checked on 2026-10-15.

## Relevance and mechanism

PLR scores levels with value-loss proxies such as TD/GAE error and balances score priority with staleness so old levels are revisited.

## Evidence and relationship to claims

Procedural generalization experiments concern levels, not Pareto preferences. PLR is the closest structural antecedent for `coverage-recency-allocation` and informs progress/combined claims; staleness is not novel.

## Limitations and falsifiers

High value loss need not imply useful progress. Equivalent preference replay or null recency ablations would narrow or falsify the incremental claim.

Evidence pointer: Sections 3–5.

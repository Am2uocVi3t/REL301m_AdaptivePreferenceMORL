---
paper_id: abels2019dynamic-weights
evidence_level: full_text
---

# Dynamic Weights in Multi-Objective Deep Reinforcement Learning

Primary source: https://proceedings.mlr.press/v97/abels19a.html

## Access report

Open PMLR full text checked on 2026-10-15.

## Relevance and mechanism

This early direct antecedent augments a multi-objective Q-network with a changing linear-scalarization weight and uses Diverse Experience Replay across preferences. It establishes preference conditioning under dynamic weights, not adaptive selection of which weights receive training.

## Evidence and relationship to claims

Deep Sea Treasure and Minecart experiments evaluate adaptation to changing weights. The work bounds broad novelty for `combined-allocation`; it does not provide the repository's gap, disagreement, coverage/recency, or progress rules.

## Limitations and falsifiers

Evidence is limited to the reported discrete-action tasks and linear preferences. Prior evidence that its replay/sampling is equivalent to the proposed allocator would narrow the distinction.

Evidence pointer: Sections 3–5.

---
paper_id: delasheras2026controllability
evidence_level: full_text
---

# Controllability in Preference-Conditioned Multi-Objective Reinforcement Learning

Primary source: https://arxiv.org/abs/2605.10585

## Access report

The 23-page arXiv full text was checked on 2026-10-15. The temporary PDF and extracted text remained outside Git. The work is recorded as a preprint rather than a peer-reviewed publication.

## Why this work is relevant

The paper shows why hypervolume, expected utility, sparsity, and cosine similarity do not by themselves establish that a conditioned policy follows its input preference. This directly affects the repository's evaluation protocol: an allocator can improve front-level metrics while the policy remains insensitive or inversely responsive to some preference components.

## Mechanism and assumptions

The proposed controllability view measures the mapping from a conditioning preference to the return it induces. For each objective, the paper recommends a rank-correlation statistic between that objective's preference weight and achieved return. Spearman correlation captures monotonic alignment while retaining sign and per-objective resolution; negative values expose inverted response.

This is an evaluation metric, not a training allocation algorithm. The paper assumes linear preference vectors for the main formulation and evaluates a MOPPO policy conditioned on those weights. It also provides a qualitative within-episode preference-switch example, but the main quantitative tests use fixed weights per evaluation batch.

## Evidence and experimental protocol

MOPPO is compared with PPO and a MOPPO variant whose policy ignores the conditioning input. Experiments cover multi-objective Tetris, Snake, and MOBA using a PufferLib extension. Thirty agents are trained per algorithm and environment; evaluation uses 30 batches associated with equally spaced simplex weights. Metrics include hypervolume, sparsity, expected utility, cosine similarity, and per-objective Spearman correlation.

The unconditioned methods sometimes equal or beat MOPPO on mainstream front metrics, even though only MOPPO can respond to weights. Per-objective rank correlation exposes positive, weak, or inverted controllability that aggregate metrics conceal. Appendix A qualitatively switches a Tetris preference at step 500 and observes behavioral adaptation with an LSTM-related lag.

## Relationship to project claims

- `combined-allocation`: a claimed allocation benefit should include preference-to-outcome controllability, not only front quality.
- The paper does not allocate training across preferences and is not an antecedent for the four curriculum signals.
- The repository already lists controllability/ordering as a secondary metric; this paper supplies a newer and more explicit per-objective operationalization that should be considered at protocol freeze.

## Limitations and possible falsifiers

Rank correlation tests monotonic association, not causal compliance, proportionality, or absolute performance. A policy can be controllable but poor, or strong on hypervolume but weakly controllable. The experiments cover one conditioned algorithm and three game environments, with some environment-specific hyperparameter selection. The implication for this project would weaken if rank correlation proved unstable under the fixed held-out preference manifest or added no information beyond a predeclared ordering metric.

## Evidence pointers

- Sections 3–4: formal preference-to-return mapping and per-objective rank-correlation metric.
- Section 5: 30-agent protocol, environments, fixed preference batches, metrics, and main results.
- Section 6: interpretation and evaluation recommendation.
- Appendix A: front visualizations, per-objective failures, and within-episode preference switch.
- Appendices B–C: PufferMO implementation and training configuration.

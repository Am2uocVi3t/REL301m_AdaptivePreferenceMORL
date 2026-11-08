---
paper_id: lu2023capql
evidence_level: full_text
---

# Multi-Objective Reinforcement Learning: Convexity, Stationarity and Pareto Optimality

Primary source: https://openreview.net/forum?id=TjEzIsyEsQ6

## Access report

User-supplied ICLR 2023 proceedings PDF checked in full on 2026-10-15. The local copy is stored at the Git-ignored path `research/literature/pdfs/lu2023capql.pdf`; SHA-256: `5412e729244b633a573585bc4a03fe529fef60288e344dc899ddc44d9b8f09c3`.

## Why this work is relevant

CAPQL is close prior art for preference-conditioned continuous-control MORL and for the theoretical relationship between linear scalarization, stationary stochastic policies, and Pareto coverage. It answers the previously unresolved question about preference scheduling: CAPQL samples weights from a fixed distribution; it does not adapt allocation using observed weakness, uncertainty, coverage, recency, or learning progress.

## Mechanism and assumptions

The theoretical analysis distinguishes single-state, distributed-initial-state, and aggregate Pareto efficiency. For finite state/action infinite-horizon discounted MORL, the paper proves convexity of the value-function range induced by stationary stochastic policies and argues that linear scalarization can recover single-state/distributed-initial-state Pareto-efficient policies with suitable nonnegative weights.

The paper attributes practical failures of existing linear-scalarization methods to deterministic-policy bias and numerical instability of a discontinuous preference-to-value mapping. It adds the same strongly concave term to every reward objective; the implementation uses policy entropy. This makes the augmented Pareto frontier strictly convex and its preference-to-value correspondence unique and uniformly continuous under the paper's assumptions.

CAPQL is a SAC-style actor-critic with two vector-valued Q-networks, target networks, and a Gaussian policy. Both Q and policy networks are conditioned on preference `w`. Algorithm 1 samples `w` from a fixed input distribution `Dφ` for environment interaction and trains on replay transitions carrying that weight. The sampling distribution is not updated from learning outcomes.

## Evidence and experimental protocol

The empirical study uses vector-reward variants of Hopper, Walker2D, HalfCheetah, and Humanoid. The preference set is restricted to positive weights within 22.5 degrees of unit vectors. CAPQL is compared with MOQ, discrete-action QEnv, and a continuous actor-critic QEnv variant. Each method is trained with five random seeds and evaluated during training on ten randomly sampled weights per step. An augmentation-strength ablation on Hopper and a small analytical example examine stability and continuity as entropy strength changes.

The reported evidence supports the authors' claims about their augmented target's stability in those settings. It does not test adaptive preference allocation, held-out preference splits, dynamics shifts, the project's matched rollout/update/evaluation budgets, or the project's gap/disagreement/coverage/progress signals.

## Relationship to project claims

- `combined-allocation`: CAPQL establishes that a preference-conditioned continuous-control actor-critic with fixed weight sampling and entropy augmentation is known. The project must not claim novelty for conditioning on preferences or training across a weight distribution.
- CAPQL is not a direct antecedent for `conditioning-gap-allocation`, `disagreement-allocation`, `coverage-recency-allocation`, or `learning-progress-allocation`, because its weight distribution is not adapted using any of those signals.
- CAPQL does not study `environment-shift-robustness`; preference variation and environment/dynamics variation remain separate.

The highest defensible project distinction remains a controlled comparison of familiar allocation signals for deciding where bounded training resources go, not a new preference-conditioned MORL architecture.

## Limitations and possible falsifiers

The main theoretical results rely on the paper's stationary-policy, discounting, finite state/action, and ergodicity conditions where specified; the practical algorithm is evaluated in continuous MuJoCo tasks. Augmentation changes the optimized reward, and its environment-specific strength trades fidelity to the original objective against stability. Discrete action-space baselines require action discretization, which complicates fairness. No equivalent adaptive allocation rule was found in the full text; future evidence of outcome-dependent updates to `Dφ` would falsify that reading.

## Evidence pointers

- Sections 4.1–4.2: convexity, linear scalarization, Pareto-efficiency definitions, and concave augmentation.
- Sections 5.1–5.3: preference-agnostic setting, conditioned SAC implementation, MuJoCo comparisons, and augmentation ablation.
- Appendix A: relationship to conditioned MORL and alternative scalarizations.
- Appendices D–H: discontinuity argument, entropy choice, Algorithm 1, convergence discussion, and analytical-example evidence.
- Appendix I: hyperparameters, environment reward dimensions, and software versions.

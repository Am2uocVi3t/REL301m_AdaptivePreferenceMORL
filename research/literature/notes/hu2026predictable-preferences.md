---
paper_id: hu2026predictable-preferences
evidence_level: full_text
---

# Near-Minimax Multi-Objective RL under Predictable Adversarial Preferences and Preference-Free Exploration in Linear MDPs

Primary source: https://proceedings.mlr.press/v306/hu26bc.html

## Access report

The official 56-page ICML 2026 PMLR full text was checked on 2026-10-15. The temporary PDF and extracted text were not committed.

## Why this work is relevant

This paper formalizes two 2026 settings in which preferences are not a fixed training distribution: predictable weights can change between online episodes, or arbitrary preference queries can arrive only after reward-free data collection. It is important for precise terminology and hypervolume semantics, but it does not choose training preferences because a region is weak or learnable.

## Mechanism and assumptions

The online setting uses finite-horizon linear MDPs with a known feature map, unknown transitions, and full vector reward feedback. An adversary may select each episode's preference using all past history but must do so before the new episode's randomness. The algorithm estimates each reward coordinate separately and scalarizes only when the current query arrives, preserving the martingale structure required for confidence bounds.

The reward-free preference-free exploration setting observes transitions without rewards and must answer arbitrary preferences after the corresponding scalar reward is revealed. The paper distinguishes decision-optimal query answering from the stronger task of explicitly recovering the transition model.

For deployment, episode-start randomization among policies makes the achievable return set convex. The paper therefore argues for hypervolume of the convex hull rather than raw observed return points and develops support-function-to-hypervolume stability bounds.

## Evidence and experimental protocol

The main contribution is theoretical: filtration-safe regret bounds, preference-free exploration rates, lower bounds, and hypervolume stability results. Experiments use synthetic anchored simplex-mixture linear MDPs. Preference schedules include i.i.d. Dirichlet weights, a fixed cyclic schedule, and a predictable adversary based on prior returns. Baselines include weight-net discretization and a feature-aware scalar-reward learner.

The supplement specifies at least 20 seeds, 95% confidence intervals for regret/suboptimality, and median/IQR for hypervolume. The experiments diagnose discretization costs and differences between raw and convexified hypervolume; they are not deep-control comparisons on the repository's environments.

## Relationship to project claims

- `combined-allocation`: adaptive allocation chosen by the learner is distinct from an exogenous predictable preference sequence. The repository should not use “adaptive preferences” without stating who adapts them and from which signal.
- The coordinate-wise reward interface supports preserving vector returns and delaying scalarization, which is consistent with the repository's provenance contract.
- The convexified hypervolume proposal is relevant to evaluation semantics but should not silently replace the currently frozen protocol metric without a documented protocol decision.

## Limitations and possible falsifiers

The strongest guarantees assume vector feedback, linear MDPs with known features, and episode-start policy randomization. Experiments are synthetic rather than MO-Gymnasium deep RL. High-dimensional convex-hull hypervolume remains computationally challenging. This note's classification would change if a method section were found to allocate learner-controlled training episodes from regional empirical outcomes rather than merely respond to queried or adversarial preferences.

## Evidence pointers

- Sections 1–3: filtration timeline, two protocols, linear-MDP assumptions, and feedback model.
- Sections 4–6: deployable convex-hull hypervolume, algorithms, and main guarantees.
- Sections 7–8: synthetic experiments and explicit limitations.
- Appendix A.1: preference schedules, metrics, and seed/statistics protocol.
- Appendix D: counterexamples and boundaries of the guarantees.

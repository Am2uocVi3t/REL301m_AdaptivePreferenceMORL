# Hard, Uncertain, or Learnable?

## A Controlled Study of Preference Allocation in Preference-Conditioned MORL

**Status:** Revised research protocol, 15 October 2026
**Original record:** `REL301m_Research_Project_Proposal_MORL_VI.pdf`
**Primary purpose:** REL301m course project
**Publication path:** empirical study suitable for later workshop or journal extension

## 1. Motivation

Preference-conditioned multi-objective reinforcement learning (MORL) aims to learn one policy that can respond to different objective trade-offs. A practical training decision is how to allocate a fixed interaction and update budget across preferences. Existing work already establishes conditioned policies, adaptive weight selection, disagreement-based curricula, coverage or staleness sampling, and preference relabeling. This project therefore does not claim that any of those ingredients is new in isolation.

The study asks a narrower question: which preference-allocation signals identify regions where additional training produces measurable future improvement? In particular, a region may be hard for the current policy, uncertain under an ensemble, under-sampled, or currently learnable. These concepts need not coincide.

## 2. Research questions

- **RQ1:** Which signal—conditioning gap, calibrated ensemble disagreement, local coverage and recency, or observed learning progress—best predicts subsequent improvement in held-out utility, hypervolume, or tail regret?
- **RQ2:** Under matched interaction, update, evaluation, and tuning budgets, does adaptive allocation improve sample efficiency or worst-region performance over uniform and compute-matched random allocation?
- **RQ3:** Does an allocation signal help through the rollout distribution, the gradient-update preference distribution, or both?
- **RQ4:** How stable are these findings across held-out preferences, Pareto-front geometry, and separately specified environment shifts?

## 3. Hypotheses

- **H1:** Observed learning progress is more predictive of future improvement than current difficulty alone.
- **H2:** Conditioning gap and disagreement identify hard or uncertain regions, but high values do not necessarily imply positive learning progress.
- **H3:** Adaptive allocation has a larger effect when the sampled preference is used consistently in replay and gradient updates than when it only selects rollout episodes.
- **H4 (stretch):** Nominal allocation gains do not automatically transfer to dynamics shifts; robustness is an independent empirical outcome.

Effect-size thresholds will be frozen only after a pilot estimates seed-level variance. The final test set must not be used to choose thresholds, checkpoints, reference points, or hyperparameters.

## 4. Contributions that may be claimed

The course report may claim implementation and controlled evaluation of preference-allocation signals. A later paper may claim an empirical insight only if it is supported across environments and seeds. Permitted wording is:

> We conduct a fixed-budget factorial study of archive-relative difficulty, masked-ensemble disagreement, local coverage and recency, and observed learning progress for preference-conditioned MORL.

The project must not claim a first method, state of the art, calibrated epistemic uncertainty, broad environment generalization, or improved robustness without the corresponding evidence.

## 5. Method

### 5.1 Conditioned vector value function

For state `s`, action `a`, and simplex preference `w`, the network predicts a vector value

`Q_theta(s, a, w) in R^d`.

Greedy action selection uses linear scalarization:

`a*(s,w) = argmax_a w^T mean_k Q_theta_k(s,a,w)`.

Every externally supplied preference must be non-negative, finite, and sum to one within tolerance.

### 5.2 Replay and update semantics

Each transition stores `(s, a, r, s', terminated, truncated, w_behavior, bootstrap_mask)`. Time-limit truncation ends a rollout but does not suppress Bellman bootstrapping; true termination does.

The experiment exposes three allocation modes:

- `rollout_only`: adaptive preferences select episodes and stored behavior preferences drive updates;
- `update_only`: rollouts are uniform while update preferences are drawn from the adaptive distribution;
- `rollout_and_update`: the adaptive distribution controls both.

This distinction is a required ablation, not an implementation detail.

For each ensemble head `k`, Double-DQN selects and evaluates its own greedy action. Bernoulli bootstrap masks provide different replay samples per head. The shared representation means the result is described as a **masked multi-head ensemble**, not a fully independent bootstrap ensemble.

### 5.3 Allocation signals

For candidate preference `w`:

- **Conditioning gap:** `[max_(v in A) w^T v - w^T J_pi(w)]_+`, where `J_pi(w)` is measured with the current policy on a curriculum-evaluation environment.
- **Disagreement:** variance across masked ensemble heads of their scalarized greedy values on replay states.
- **Coverage/recency:** a combination of inverse kernel density in preference space and time since the candidate or its neighborhood was sampled.
- **Observed learning progress:** absolute change in measured scalarized return since the preceding curriculum evaluation for that candidate.

Signals are normalized before weighting. Sampling uses a temperature-controlled softmax mixed with a fixed uniform exploration floor. Paired methods and seeds share a versioned candidate pool, validation set, and final-test set. Curriculum checkpoints reuse common episode seeds to reduce measurement noise. All curriculum-evaluation interactions are recorded separately and matched by the random-score control.

## 6. Course-project scope

### Environments

- `mo-lunar-lander-v3`
- `minecart-v0`

Only shifts that can be instantiated and behaviorally verified are reported. Unsupported Minecart perturbations remain publication extensions rather than simulated results.

### Methods

- Uniform-PCQN
- Adaptive-PCQN
- Compute-matched random-score PCQN
- Independent scalarized DQN
- Envelope Q-learning
- GPI-LS where the environment and current library API support it

### Required ablations

- uniform;
- gap only;
- disagreement only;
- coverage/recency only;
- learning progress only;
- pairwise combinations selected before the full run;
- full composite;
- compute-matched random score;
- rollout-only, update-only, and rollout-and-update.

### Protocol

- 0.5–1 million training interactions per method and seed;
- one immutable validation preference set and one immutable final-test set;
- 5 seeds are acceptable for the course as a pilot, with effect sizes and confidence intervals rather than a required `p < 0.05` claim;
- 8–10 paired seeds are preferred for the primary course comparison when compute permits;
- 30–50 final-evaluation episodes per preference for stochastic environments;
- identical interaction, update, evaluation, and tuning budgets across compared methods.

## 7. Metrics and statistical analysis

Primary metrics are normalized hypervolume with a reference point frozen before final testing, expected utility, worst-decile or CVaR regret, and area under the learning curve. Secondary metrics include IGD, sparsity, per-objective preference-to-return rank-correlation controllability, robustness degradation, wall-clock time, peak memory, ensemble calibration, and correlation between allocation scores and future improvement.

Analysis is performed at training-seed level. Report paired differences, confidence intervals, and effect sizes. Exact paired permutation or Wilcoxon tests may be used for predeclared contrasts, followed by Holm correction. Five paired seeds cannot by themselves produce a two-sided exact sign result below 0.05 and must not be presented as adequate significance evidence.

## 8. Reproducibility contract

Every reported run records:

- repository commit and dirty-state flag;
- complete resolved configuration and its hash;
- environment and dependency versions;
- training, protocol, and episode seeds;
- preference manifest hash;
- reward scaling, normalization bounds, and hypervolume reference point;
- interaction, update, curriculum-evaluation, and final-evaluation counts;
- raw per-episode vector returns, checkpoint identity, wall-clock time, and hardware.

The executable course protocol defines `J` as discounted episodic vector return with `gamma = 0.99`. Evaluation artifacts also retain undiscounted returns, but archive, gap, hypervolume, utility, and regret use the discounted definition consistently.

The final test set is evaluated once after model and hyperparameter selection. Validation results may select checkpoints; final-test results may not.

## 9. Publication extension

A workshop or TMLR submission additionally requires a continuous-control family, MORL-Generalization environments, modern action-space-compatible baselines such as WVS/PGMORL, CAPQL, PD-MORL, PCRL, HPR-CAPQL, MORL-FB, or D³PO, and allocation comparisons informed by PBMORL and MPFT where their multi-policy/human-feedback settings are compatible. It also requires broader objective dimensions and front geometries and approximately 10–20 paired seeds for primary comparisons based on pilot precision analysis.

Main-track positioning requires either a new mechanism that outperforms strong allocation antecedents for an identified reason, or a broad and reproducible empirical principle. Combining familiar scores without such evidence is not sufficient.

## 10. Success criteria

- **Course-ready:** end-to-end reproducible runs on both core environments, correct fixed-budget comparisons, critical ablations, and an honest analysis regardless of whether the adaptive method wins.
- **Workshop-ready:** stable insight across additional domains with close mechanism baselines and complete artifacts.
- **Journal-ready:** broad evidence, modern baselines, calibrated diagnostics, fixed final testing, and a conclusion that remains useful under negative results.

The course project is successful if it answers the revised research questions correctly. Superiority of the full adaptive method is not a prerequisite.

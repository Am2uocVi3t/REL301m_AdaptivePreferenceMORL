# Frozen-model cause investigation

The completed n-step screen is not reopened. This diagnostic is a new,
zero-training scope authorized by the user's request on 2 November 2026 to
investigate causes and develop a rigorous improvement plan.

Executable plan: `configs/experiments/policy_extraction_diagnosis_v1.json`.
All twelve fixed-final checkpoints are pinned by hash. No optimizer updates,
checkpoint selection, normalization/reference changes or final-test access.

## Competing explanations

1. Mean-Q aggregation can destroy a useful head's actions. Falsifier: none of
   the three individual heads or plurality voting restores task expression.
2. Epsilon behavior can reach rewards while its greedy policy cannot.
   Compare episode-head epsilon .05, mean epsilon .05 and uniform random with
   aligned per-step exploration/action streams. A successful random rollout
   does not demonstrate learned control.
3. Positive behavior rewards may disappear or be poorly fitted in replay.
   Audit positive n-step reward windows, per-head masks and masked TD errors
   using the model/target/replay from the same final recovery boundary.
4. Scalar utility can improve without the intended task. Preserve native
   vectors, lengths, task events and action histograms alongside utility.

## Matrix and controls

Main policies: mean-Q greedy, heads 0/1/2 greedy, plurality vote, episode-fixed
sampled-head epsilon .05, mean-Q epsilon .05, and uniform random. Voting uses
ensemble-mean scores only to break tied plurality candidates; this is a
declared adaptation. Lunar also includes the unchanged Gymnasium heuristic as
a handwritten positive control, never as a learned MORL method.

Six Minecart models x five fixed preferences x ten new development environment
seeds x eight policies = 2400 episodes. Six Lunar models x two preferences x
ten seeds x nine policies = 1080. Add exact replication of all 240 old final
task cases: 3720 episodes, at most 3.72M diagnostic environment steps. The two
engineering replication witnesses (40 episodes) are accounted separately.
There is no additional training. Pure-fuel preferences are controls and do
not carry an ore/landing success requirement.

Each case retains native state/action/reward traces, exploration indicators,
periodic per-head vector-Q probes and exact on-device head/mean argmax actions
in compressed NPZ files on D:. New policies share initial states and controlled
ore/environment seeds. Every original checkpoint is checked unchanged after
execution. All 240 old-case replication comparisons must pass before accepting
the new policy comparisons. Three training seeds remain the statistical units.

## Interpretation gates

Compare fixed policies across all seeds; never choose a best head per seed.
Head rescue would support an extraction bottleneck under these cases, not a
universal explanation. If all greedy heads fail, averaging alone is insufficient
as the cause. Epsilon rescue can diagnose exploration dependence, but requires
comparison with random actions. TD errors and Q-to-return gaps identify fitting
or calibration problems without proving a unique causal mechanism.

Next interventions must be chosen after this finite diagnosis, predeclared in
a new scope, and confirmed on independent development cases. The original
matrix/F1/final-test locks stay intact. This is a local, user-triggered finite
run through the qualified Windows process method; no scheduled ARIS workflow,
paid review or automatic retry is enabled.

## Literature constraints

Osband et al., *Deep Exploration via Bootstrapped DQN* (NeurIPS 2016), main
Section 3 and supplement D.1: episode-fixed training heads and Atari ensemble
voting. It does not establish our mean-Q extraction, three-head MORL performance
or tie-break. Terekhov and Gulcehre (2024) discuss unstable/collapsing Minecart
policies; sampled PPO versus deterministic baselines and different checkpoint
selection prevent importing their numerical ranking as our result.
Full primary main/supplement reading and access evidence are in the literature
notes. We test these mechanisms rather than treating a citation as a repair.

# Completed n-step development screen — 2 November 2026

All 12 combined jobs completed their fixed 500k budgets: three original complete
jobs retained plus nine recovery jobs. The coordinator exited normally after
the recovery-aware numerical/provenance audit passed. No new training is active.

Evidence: `research/evidence/credit_assignment_recovery_v1.json`.
This is an executor numerical audit, not an independent semantic-review PASS.

## Budgets and units

- 6,000,000 logical training interactions and 1,485,012 gradient updates.
- 3,456 validation episodes / 1,377,795 validation environment steps.
- 720 separate task-diagnostic episodes / 428,406 diagnostic environment steps.
- Zero final-test and curriculum-evaluation steps.
- Interrupted original compute and engineering qualification are extra costs,
  retained separately under the recovery amendment; they are not extra seeds.

Both arms use uniform preference allocation, the same frozen gamma/scales and
three paired training seeds. Intermediate checkpoints are descriptive; all
comparisons below use the fixed 500k checkpoint. Three training seeds are the
experimental units, not the repeated validation episodes.

## Fixed-final-checkpoint results

Expected utility: mean +/- sample standard deviation across the three seeds.

| Environment | n=1 | n=20 |
|---|---:|---:|
| Lunar | -0.04550 +/- 0.01964 | -0.04240 +/- 0.02514 |
| Minecart | -0.63997 +/- 0.01853 | -0.16218 +/- 0.03381 |

Lunar landing-heavy diagnostic, per seed 20261211/12/13, ten cases each:

| Metric | n=1 | n=20 |
|---|---|---|
| Native +100 | 3, 3, 7 | 0, 0, 1 |
| Native +100 and pad x | 1, 1, 5 | 0, 0, 1 |

No seed reaches the declared 8/10 pad screen. Longer returns do not improve
this task metric in any of the three paired seeds. The small mean utility
change does not establish improved landing or a general n-step advantage.

Minecart: zero ore deliveries and zero cargo collection in all 120 final
task-diagnostic cases (six models, two preferences, ten cases). Both ore
objectives are also zero across all 576 final validation episodes, and across
all 1,728 Minecart validation episodes including the intermediate checkpoints.
No seed reaches the declared 5/10 delivery screen. All 12 final task gates fail.

The Minecart utility increase is real within this fixed validation protocol:
paired n=20 minus n=1 effects are +0.51803, +0.43585, +0.47949. Because both ore
components are zero, these utilities reflect the discounted fuel component
alone. This is not evidence of useful ore trade-offs. Mean validation lengths
are 1000.0/938.66/876.06 for n=1 versus 71.78/133.47/132.72 for n=20, consistent
with more early empty-return behavior in the latter. The two selected task
preferences can behave differently; raw fuel costs in those cases do not
uniformly improve. No significance or broad preference-generalization claim
is made from these three pairs.

## New diagnostic lead, not a causal conclusion

The completed training logs contain ore-positive behavior episodes:

| Arm | Ore-positive completed episodes | All completed training episodes |
|---|---:|---:|
| n=1 | 875 | 4,264 |
| n=20 | 3,880 | 21,806 |

Different episode counts at equal interaction budgets prevent interpreting the
larger numerator as a success-rate gain. These are logged native episode sums,
not successful greedy evaluation episodes or independently reproduced traces.
They show that the recorded behavior data contains a reward signal, so a claim
that exploration never obtains ore would be incorrect for this cohort.

Training uses an episode-fixed sampled bootstrap head plus epsilon exploration;
evaluation uses a deterministic action from the mean of three Q heads. A
separate, predeclared frozen-model diagnosis should compare individual-head
greedy policies with ensemble-mean inference and behavior exploration, retaining
native traces and controlling preference/environment seeds. Value-learning
failure, policy extraction and preference/state distribution differences remain
competing explanations. No one of these is established as the cause yet.

## Decision

The finite screen is complete and fails its task qualification. Preserve it
without extending budgets or choosing favorable seeds/checkpoints. Original
matrix/F1/final-test locks remain unchanged. The next useful investigation is
the behavior-to-greedy-evaluation gap before another training intervention.
The current course PDF remains an earlier update and has not yet incorporated
this completed cohort; no final-project-completion claim follows.

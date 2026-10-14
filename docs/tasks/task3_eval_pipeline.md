# Task 3: Evaluation and statistical protocol

**Status:** core evaluator, paired-seed runner, metrics, statistics, and provenance implemented; multi-seed aggregation and interactive demo remain planned.

## Implemented

- Immutable seeded validation and test preference specifications.
- Checkpoint loading and ensemble-mean rollouts.
- Raw per-episode vector returns and episode lengths.
- Deterministic 2-D and `pymoo` high-dimensional hypervolume.
- Expected utility, scalarized regret, CVaR-style worst tail, IGD, and sparsity.
- Seed-level bootstrap confidence intervals, paired sign-flip permutation test, paired effect size, and Holm correction.
- Protocol/checkpoint hashes, Git state, dependency versions, and budget counters.

## Required workflow

1. Use validation preferences for checkpoints and hyperparameter decisions.
2. Freeze reward scales, normalization bounds, reference point, and reference front without final-test information.
3. Evaluate the final test split once per selected method/seed.
4. Aggregate at seed level and report paired differences, confidence intervals, effect sizes, and corrected tests.

Five paired seeds are a course pilot. They do not support a required two-sided exact `p < 0.05` result; report uncertainty and practical effect size.

## Planned

- Multi-run aggregation CLI and publication tables.
- 3-D front plotting and robustness heatmaps.
- Preference-controllability/ordering metrics.
- Interactive preference slider. These must not be described as implemented.

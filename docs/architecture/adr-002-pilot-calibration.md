# ADR-002: Pilot-Only Reward and Hypervolume Calibration

Status: accepted
Date: 2026-10-15

## Context

The course protocols need per-objective reward scales and dominated hypervolume reference points before course-scale comparisons. Choosing them from final-test trajectories would leak test information. Choosing them from one adaptive method could also favor the regions that method happens to visit. Smoke runs prove integration only and must not be promoted into calibration evidence.

## Options considered

1. Keep identity scales and select an arbitrary reference point. This is simple but can distort vector losses and hypervolume and has no empirical calibration basis.
2. Tune scale and reference points from final-test returns. This uses the most relevant distribution but violates the final-test firewall.
3. Run a predeclared uniform-policy pilot on immutable validation preferences, derive deterministic proposals, and require explicit review before protocol mutation.

## Decision

Use option 3 for both course environments. Run Uniform-PCQN for three fixed seeds and 100,000 training interactions per environment with identity reward scales. Disable curriculum and checkpoint validation diagnostics because this pilot estimates objective magnitudes rather than method performance. Evaluate each final pilot checkpoint on the immutable validation preferences for five episodes per preference under nominal dynamics.

For objective `j`, set the proposed multiplicative reward scale to the inverse 95th percentile of the absolute discounted pilot return. Reject objectives whose magnitude is at or below `1e-6`. After applying the proposed scale, construct the hypervolume reference coordinate as the observed coordinatewise minimum minus the larger of 5% of the scaled 5th-to-95th percentile span and `0.01`. This guarantees strict domination by every observed pilot return while providing a deterministic margin.

The calibrator writes a provenance-rich proposal and never edits course protocols. Only a complete real-pilot manifest can become eligible for freeze review. Smoke manifests and proposals are permanently marked non-freezable.

## Trade-offs

- Uniform allocation avoids scheduler-specific sampling bias but may underrepresent rare regions that an adaptive method would visit.
- A robust magnitude quantile limits outlier influence, while the coordinatewise minimum keeps the reference point strictly dominated; a single extreme minimum can still enlarge hypervolume.
- Three pilot seeds and five validation episodes per preference control course compute, but they estimate scale rather than publication-grade uncertainty.
- Multiplicative scaling cannot remove objective offsets. Revisit the normalization contract if pilot diagnostics show offsets, near-constant objectives, or unstable scales.

## Consequences

- Final-test data is mechanically rejected by the calibration pipeline.
- Pilot and smoke budgets, seeds, algorithms, splits, and formulas are reviewable before execution.
- Course protocols remain unchanged until a separate reviewed freeze commit cites complete pilot artifacts.

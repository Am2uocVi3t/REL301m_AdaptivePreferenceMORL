# Minecart Validation Remediation

## Goal
Diagnose the all-zero Minecart ore validation returns from non-test evidence and predeclare a remediation that preserves matched budgets and blocks final-test access until qualification passes.

## Tasks
- [x] Trace Minecart reward, action, episode, and evaluation semantics from the pinned environment through training and validation code.
- [x] Quantify training-archive ore events, episode termination, action use, and validation behavior across existing pilot and primary artifacts.
- [x] Reproduce the smallest non-test behavioral probes needed to distinguish reward-pipeline failure from policy-learning failure.
- [x] Compare remediation candidates against validity, fairness, compute, and protocol-freeze constraints.
- [x] Predeclare the selected remediation, qualification thresholds, failure rules, and permitted execution sequence in versioned research state.
- [x] Add regression/semantic tests for any changed code or configuration.
- [x] Run the repository quality gate and regenerate the research handoff.

## Done When
- [x] The root cause is evidence-bounded, no final-test data were accessed, and no blocked course jobs were launched.
- [x] A machine-readable, reviewable remediation gate exists and the remaining matrix stays blocked until it passes.

# Minecart Remediation V2 Implementation

## Goal
Implement and qualify the frozen proportional-prioritized-replay v2 contract without launching qualification seeds, resuming matrix v1, or accessing final-test data.

## Tasks
- [x] Add analytic replay tests for proportional probabilities, maximum-priority insertion, normalized importance weights, and priority updates. → Verify: focused tests fail before implementation and pass afterward.
- [x] Add analytic update tests for active-head/objective TD aggregation and importance-weighted prioritized loss while preserving the uniform Huber path. → Verify: exact hand-computed values match.
- [x] Integrate replay selection and the fixed linear beta schedule into `scripts/train.py`. → Verify: uniform defaults remain unchanged and a bounded prioritized train smoke performs updates.
- [x] Extend the remediation loader, runner, and source auditor to bind v2 sources and all frozen PER arguments. → Verify: v1 remains accepted, v2 preview succeeds, and drift/missing-source tests fail closed.
- [x] Record implementation-qualification evidence and synchronize architecture, experiment, roadmap, status, memory, and handoff state. → Verify: harness doctor/status pass and execution remains unauthorized.
- [x] Run the complete Python 3.11 repository quality gate. → Verify: Ruff, MyPy, pytest, Bandit, compileall, and `git diff --check` all pass.

## Done When
- [x] The exact v2 implementation is reviewable and qualified locally, all three v2 seeds remain unexecuted, matrix v1/final test remain blocked, and the next action is explicit authorization review.

## Notes
- The existing uniform path retains uniform sampling, unit importance weights, and masked Huber loss.
- The amended-before-execution v2 path uses proportional sampling, `beta=0.4→1.0` across exactly 995,001 gradient updates, epsilon-adjusted pre-update TD priorities, and importance weighting applied to the unchanged masked Huber loss and active-head reduction.

# Minecart Remediation V2 Huber Amendment

## Goal
Resolve the pre-execution loss-family inconsistency so remediation v2 changes only the replay strategy while retaining v1's masked Huber objective.

## Tasks
- [x] Add a failing analytic test for importance-weighted per-transition masked Huber loss. → Verify: the squared-loss implementation does not satisfy the hand-computed Huber value.
- [x] Amend the unexecuted v2 plan and implementation from weighted squared TD to weighted masked Huber. → Verify: the plan records the pre-execution rationale and code follows it exactly.
- [x] Re-run the prioritized Minecart smoke and verify the expected 20 interactions and 17 updates. → Verify: no curriculum, validation, qualification seed, or final-test access occurs.
- [x] Refresh implementation hashes, research status, memory, and generated handoff. → Verify: v2 remains planned and unauthorized after implementation review.
- [x] Run the complete Python 3.11 quality gate. → Verify: Ruff, MyPy, pytest, Bandit, compileall, harness doctor, and `git diff --check` pass.

## Done When
- [x] V2 is a defensible single-factor PER intervention with v1's Huber loss preserved, and no qualification execution has occurred.

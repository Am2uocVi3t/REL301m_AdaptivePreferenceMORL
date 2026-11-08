# Primary Validation Audit and Checkpoint Lock

## Goal

Audit the completed 30-job primary PCQN block, reproduce validation evidence with full return tensors, and lock one checkpoint per run without test or shifted-environment access.

## Tasks

- [x] Add failing tests for frozen-input verification, malformed or incompatible checkpoints, deterministic selection, and resumable evidence reuse.
- [x] Implement a validation-only audit/evaluation module and bounded CLI that verifies execution status, manifests, logs, protocol hashes, checkpoints, and budgets.
- [x] Persist deterministic per-checkpoint validation artifacts and atomically resume only hash-verified completed work.
- [x] Aggregate raw and discounted returns, preferences, metrics, provenance, counters, missingness, and degeneracy diagnostics.
- [x] Apply the frozen hypervolume → expected utility → earlier-step rule and version compact audit, aggregate, and blocked-lock artifacts under `research/`.
- [x] Update canonical experiment/roadmap/status/memory state and regenerate the handoff without promoting an empirical claim.
- [x] Run the complete Python 3.11 quality gate, verify generated evidence, and commit the completed audit on the current branch.

## Done When

- [x] All 30 runs and 300 saved checkpoints pass provenance, hash, budget, validation-log, and tensor-shape checks.
- [x] The failed lock records 30 diagnostic selections, zero locks, 15 degenerate Minecart runs, and no final-test evidence.
- [x] The research harness and full repository quality gate pass from the live working tree; commit verification follows session closure.

## Outcome

The source audit passed, but checkpoint locking failed closed because Minecart ore objectives 0 and 1 were constant zero for every validation episode at every saved checkpoint in all 15 primary Minecart runs. LunarLander's 15 runs were non-degenerate, but partial locking is prohibited; the lock artifact therefore records zero locks.

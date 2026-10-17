# F1 implementation review — 2026-10-17

Reviewer: fresh `gpt-6-astra`, xhigh, agent `/root/f1_review_resume`.
Review independence: same-family. Acceptance status: provisional.

The first review returned REVISE. The implementation now isolates Minecart's
global evaluation RNG, assigns independent exploration/action/preference/replay
streams, validates exact run arguments before launch, rejects automatic retries,
records completed episodes before updates and checkpoints, and reconciles replay
counters with episode metadata and label histograms. Uniform replay avoids
buffer-sized work per update. Independent evaluation checks training metrics.

The final reviewer response was:

> PASS — scoped predeployment code review, same-family provisional.
>
> Both remaining blockers are resolved:
>
> - The F1 runner rejects `--retry-failed` before dispatch. Existing failed/running records therefore remain blocked; completed jobs retain hash-verified skipping. Historical v1/v2 behavior need not change.
> - F1 explicitly enables independent RNG streams in both cells. Exploration, action sampling, rollout preferences, bootstrap masks, success sampling, diagnostics, and uniform replay have distinct initial streams. I verified 21 distinct states across the three frozen seeds.
>
> Verification completed:
>
> - 55 focused deterministic tests passed.
> - A mocked launch confirmed retry rejection occurs before job dispatch.
> - All six frozen commands include both RNG flags.
> - The 1,000-step sanity artifacts contain 997 updates and one completed truncated trajectory in both the periodic and final checkpoints.
>
> The completed-episode sanity had zero eligible trajectories and predates the latest independent-RNG flag. It verifies episode finalization/persistence; synthetic tests verify successful replay, and deterministic checks verify the new stream separation.
>
> No remaining blocker found for the authorized F1 deployment after recording the final review/qualification evidence and satisfying the existing clean-tree/quota gates. This verdict establishes implementation readiness only—not empirical sufficiency, cross-family acceptance, F2 eligibility, checkpoint locking, or final-test access.

The coordinator subsequently ran a second completed-episode sanity with both
RNG flags on seed 9196: 1,000 interactions, 997 updates, one complete episode,
zero curriculum/validation steps, and zero eligible ore episodes. Its resource
record reports 2.5900328159332275 seconds and 392,808 KiB peak RSS. These are
sanity measurements; full-budget resources remain to be measured.

The previous reviewer dispatch failed on account usage before producing any
review. It supplied no evidence and was not counted as a passing review.

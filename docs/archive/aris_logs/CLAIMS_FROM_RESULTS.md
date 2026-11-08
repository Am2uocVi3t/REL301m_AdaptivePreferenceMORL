# Claims from completed F1 results

claim_supported: no

review_independence: same-family

acceptance_status: provisional

integrity_status_at_review: unavailable

attached_integrity_status: warn [INTEGRITY: WARN]

The subsequently completed `EXPERIMENT_AUDIT.json` is attached by the coordinator;
the original claim verdict is unchanged. Its warnings concern units, missing
behavior measurements and scope, not a changed retention decision.

In the predeclared nominal-validation Minecart F1 screen, successful-episode stratification plus deterministic achieved-return preference relabeling was insufficient to produce retained greedy ore behavior under the frozen one-step PCQN and 1M-interaction budget. All three intervention seeds acquired eligible training trajectories and received successful-episode replay exposure, yet both ore returns were zero across all 30 saved intervention-checkpoint evaluations. The paired uniform baseline showed intermittent or late ore expression in two seeds. These observations do not identify the responsible component or establish universal replay failure, adaptive-allocation effects, or generalization.

## Supported and unsupported scope

- A bounded negative result: the specified combined replay intervention did not produce ore delivery at any of the ten saved nominal-validation checkpoints in any of its three seeds.
  A1R1 has 0/4800 positive episodes for each ore objective across 30 checkpoint evaluations. Raw undiscounted and discounted tensors agree on zero ore.

- The observed failure is operationally replay-expression insufficiency after acquisition and exposure, rather than the predeclared no-acquisition category.
  A1R1 seeds 20264021, 20264022, and 20264023 acquired 1176, 1134, and 1073 eligible completed training trajectories. Each sampled 31840032 success-branch positions with zero fallback. Actual preference changes occurred at 46313803, 45294470, and 45826066 sampled positions. These counters establish recorded exposure, not successful greedy learning or a causal failure mechanism.

- The baseline contains intermittent or late positive greedy behavior; a claim that every F1 run returned zero ore would be false.
  A0R0 seed 20264021 passes expression at 500k, 900k, and 1M, with 13, 10, and 19 positive episodes per ore objective. It fails at 600k and 700k, so the earliest pass is not retained. Seed 20264022 first passes at 1M with 17/160 per objective. Seed 20264023 never passes. These are paired descriptive observations, not a general superiority or causal-component estimate.

- The finite evidence accounting and failure decision reproduce from the supplied artifacts.
  I read all 60 referenced validation JSON files, verified their hashes, and independently recomputed all expression-pass flags and positive-episode counts. They agree with the qualification artifact. Totals are 9600 episodes and 8654847 independent audit steps. Source counters separately record 6000000 training interactions, 5970006 updates, 11476292 curriculum-evaluation steps, and 8654847 validation steps during training.

## Not supported

- C1 positive bounded sufficiency, convergence, stable greedy ore behavior, or successful retention.
- Attribution to stratification, relabeling, their interaction, delayed credit, preference-map concentration, or another specific mechanism.
- A general causal claim that the intervention is harmful or that uniform replay is superior.
- Any promotion of the six course allocation claims in research/claims.json: no adaptive-allocation comparison or signal-to-future-progress test was conducted here.
- Preference generalization, dynamics-shift robustness, or final-test performance.
- Universal impossibility of successful replay, HPR, one-step PCQN, or Minecart learning.
- Treating 9600 repeated evaluation cases as 9600 independent experimental replicates; the experimental unit is the paired training seed.
- Treating source-audit PASS, evidence-existence verification, or successful training execution as learner qualification or scientific acceptance.

## Missing evidence

- Independent semantic integrity audit and any subsequent cross-family scientific assessment. Acceptance remains provisional. Attach the pending integrity assessment and downgrade confidence if it identifies material integrity failures.
- The predeclared B1 Mine-action, cargo, and action-margin diagnostics are absent from the reviewed validation artifacts and evaluator output. Positive/zero delivered ore is sufficient to resolve the frozen expression gate, but cannot distinguish failure to mine, acquire cargo, return to base, or choose actions with adequate margins.
- A1R0 and A0R1 are absent, as required after the failed F1 entry gate. Component decomposition remains untested; this is not permission to execute F2.
- No broader-seed, held-out preference, shifted-environment, or final-test evidence exists within F1. Restrict all conclusions to this predeclared simulation screen. No additional evidence is needed to determine that its positive primary claim failed.

## Next action

Stop F1 and preserve/report the negative result. Attach the pending integrity report and synchronize evidence records. Do not add seeds, extend budgets, tune, restart, run F2, lock checkpoints, revive matrix v1, or access final test. Any materially different future research requires separately authorized predeclaration; none is proposed for execution here.

Full reviewer result: `CLAIMS_FROM_RESULTS.json`. Original trace: `.aris/traces/result-to-claim/2026-10-18_run01/`.

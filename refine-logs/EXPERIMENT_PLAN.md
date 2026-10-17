# Experiment Plan: Minecart Replay Sufficiency Amendment

**Problem:** Successful exploratory ore episodes do not become stable greedy
Minecart behavior.  
**Method thesis:** Successful-episode-stratified transition sampling and a fixed
episode-level HPR preference map may be sufficient under the unchanged one-step
PCQN.  
**Date:** 2026-10-17  
**Status:** user-authorized under `aris-full-workflow-20261017`; implementation
and training begin only after the versioned amendment is committed and the new
stacked review PR exists.

## Claim Map

| Claim | Why it matters | Minimum convincing evidence | Blocks |
|---|---|---|---|
| C1: bounded sufficiency | Minecart must qualify before allocation arms are interpretable | All three A1R1 seeds satisfy expression and two-checkpoint retention under matched budgets and source audit | B1, B2 |
| C2: exploratory decomposition | If F1 passes, identify whether stratified exposure, relabeling, or their combination is associated with the result on the same seeds | Complete 2x2 paired cells with exact replay manipulation checks; interpret conditionally | B3 |

**Anti-claims:** The study does not identify delayed credit causally, prove broad
replay novelty, establish publication-level performance, or unlock final test.

## Paper Storyline

- Main evidence, if authorized: source-valid manipulation plus stable ore
  expression across all paired seeds.
- Supporting evidence: acquisition/exposure/expression/retention decomposition.
- Conditional appendix evidence: the selection-conditioned F2 2x2 comparison.
- Intentionally cut: n-step returns, Envelope, PCN, reward shaping, hyperparameter
  sweeps, shifted environments, final test, and adaptive allocation arms.

## Experiment Blocks

### B0: Deterministic contract qualification

- **Claim tested:** the implementation exactly realizes the frozen proposal.
- **Data/task:** synthetic buffers and recorded-format fixtures only; no
  environment rollout.
- **Checks:** HPR Equation (1) map, finite-pool projection/tie break, episode
  completion/truncation, eligibility, empty-stratum fallback, 32/32 allocation,
  all four cells, effective preference in prediction and bootstrap, RNG-stream
  independence, generation-safe indices, and budget counters.
- **Success:** all analytic and regression tests pass; uniform A0R0 is bitwise or
  numerically equivalent to the current uniform path under controlled inputs.
- **Failure:** do not run training.
- **Priority:** MUST-RUN after implementation authority.

### B1: F1 matched-budget sufficiency screen

- **Claim tested:** A1R1 is sufficient for retained greedy ore behavior.
- **Compared systems:** A0R0 baseline versus A1R1 full intervention.
- **Seeds:** `20264021`, `20264022`, `20264023`, paired across cells.
- **Per-run budget:** 1,000,000 training interactions; 995,001 updates; batch 64;
  unchanged architecture, optimizer, exploration, targets, buffer capacity,
  preference pool, and checkpoint cadence.
- **Total F1 budget:** six runs, 6,000,000 training interactions and 5,970,006
  updates. Validation is separate: ten checkpoints × 32 preferences × 5
  episodes per run, capped at 9,600,000 nominal-validation environment steps
  across F1 by the 1,000-step episode limit.
- **Primary metrics:** eligibility and fallback counts; sampled-origin counts;
  attempted and actual relabel counts; projection distance and label diversity;
  `Mine`, cargo, delivery, positive-ore episodes/values; action margins.
- **Secondary metrics:** scaled hypervolume and expected utility.
- **Success:** every A1R1 seed first passes by 800k and passes the next two
  checkpoints; both ore objectives have at least 8/160 positive episodes and at
  least two distinct positive values at each required checkpoint.
- **Failure interpretation:**
  - no eligible episode: acquisition-limited insufficiency;
  - eligible exposure but no expression: replay-expression insufficiency;
  - isolated or late pass: retention failure or late-inconclusive;
  - source/budget drift: invalid run, not a scientific result.
- **Priority:** MUST-RUN only after approval.

### B2: Independent source and budget audit

- **Claim tested:** B1 evidence follows the frozen amendment.
- **Checks:** commit/config hashes, seeds, interactions, updates, batch positions,
  RNG identities, checkpoints, validation seeds/preferences, return tensors,
  replay counters, time/memory/storage, and final-test firewall.
- **Success:** all checks pass with no final-test or shift access.
- **Failure:** no claim; repair plumbing only under separate authority.
- **Priority:** MUST-RUN after B1.

### B3: F2 selection-conditioned 2x2 decomposition

- **Entry gate:** all A1R1 seeds pass B1 retention and B2 audit.
- **Compared systems:** add A1R0 and A0R1 on the same three seeds; combine with
  existing A0R0/A1R1 for a four-cell paired analysis.
- **Budget:** six additional runs, so the proposed maximum becomes 12,000,000
  interactions and 11,940,012 updates; separately capped at another 9,600,000
  nominal-validation steps.
- **Interpretation:** exploratory and conditional on selecting seeds after A1R1
  success. It can describe these paired cells, not independently confirm a
  general main/interaction effect.
- **Stop:** no further component or run is added regardless of result.
- **Priority:** MUST-RUN only if the entry gate and separate continuation
  authority are both satisfied.

## Run Order and Milestones

| Milestone | Goal | Runs | Decision gate | Cost | Current status |
|---|---|---:|---|---|---|
| M0 | Record authority and create stacked review PR | 0 | PR exists with versioned amendment plan | none | AUTHORIZED_IN_PROGRESS |
| M1 | Implement and qualify B0 | 0 training | Deterministic/code/source review pass | resource estimate required | AUTHORIZED_PENDING_PR |
| M2 | Execute F1 B1 | 6 | exact completion, then B2 | 6M interactions + 5,970,006 updates | WAITING_M1 |
| M3 | Audit and retention decision | 0 training | all A1R1 seeds retained or stop | validation separately accounted | WAITING_F1 |
| M4 | Conditional F2 B3 | 6 | exploratory decomposition then stop | additional 6M + 5,970,006 | CONDITIONAL_F1_PASS |
| M5 | Result-to-claim review | 0 training | evidence-bounded verdict | cross-family review desired | WAITING_EVIDENCE |

## Compute and Data Budget

- Exact training interaction/update budgets are above.
- Before M1 approval, derive wall time, peak RAM/VRAM, and aggregate-log storage
  from verified prior run logs; no estimate is silently invented here.
- Training and nominal validation remain separate ledgers.
- No human evaluation, annotation, shifted environment, or final-test data.
- F1 and F2 do not alter the course matrix or reuse their runs as course evidence.

## Risks and Mitigations

- **No acquisition:** classify separately and stop; replay cannot reuse absent
  successful episodes.
- **Map collapse:** audit projection distances, distinct labels, and actual
  preference changes.
- **Hidden random-stream coupling:** dedicate named seeded RNG streams.
- **Logging blow-up:** store immutable trajectory summaries and aggregate
  counters every 10,000 updates/checkpoint, not 63,680,064 full rows per run.
- **Selection overclaim:** label F2 exploratory and selection-conditioned.
- **Late checkpoint ambiguity:** first pass after 800k is inconclusive and does
  not extend budget.

## Final Checklist

- [x] Primary claims are bounded and falsifiable.
- [x] Novelty is limited relative to HPR and DER.
- [x] Training, validation, and final-test budgets are separated.
- [x] Uniform, sampling-only, relabel-only, and full cells are defined.
- [x] All-seeds and retention rules are frozen at proposal level.
- [x] User/supervisor authority `aris-full-workflow-20261017` exists.
- [ ] Versioned executable amendment exists.
- [ ] Measured resource estimate exists.
- [ ] Implementation/source review passes.


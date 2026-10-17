# Round 2 Refinement

## Problem Anchor

- **Bottom-line problem:** The shared preference-conditioned value learner must
  express non-degenerate Minecart ore behavior before any adaptive allocation
  comparison can be scientifically interpreted.
- **Must-solve bottleneck:** Successful ore trajectories occur during
  exploration but are not converted into stable greedy behavior across
  preferences and checkpoints.
- **Non-goals:** No final-test tuning, course-matrix revival, broad replay
  novelty, causal identification of delayed credit, or multi-backbone stack.
- **Constraints:** Preserve the frozen Minecart protocol, PCQN, budgets,
  checkpoint cadence, nominal-validation split, and final-test firewall. No
  implementation or run without an approved versioned amendment.
- **Success condition:** A future authorized paired-seed study must show that the
  bounded replay intervention is sufficient for every seed to pass the existing
  ore gate and retain it at two subsequent predeclared checkpoints.

## Anchor Check

- The original bottleneck remains exploratory success without stable greedy
  expression.
- The revised method does not claim buffer eviction: capacity already spans the
  full run.
- The revised method does not claim to solve or identify delayed credit: it keeps
  one-step targets fixed and tests sufficiency under that learner.

## Simplicity Check

- **Dominant intervention:** successful-episode-stratified transition exposure
  plus an episode-level HPR-style preference map.
- **Removed:** suffix-return labels, reference-point translation, implied
  sequence replay, and causal retention-versus-credit language.
- **Still excluded:** n-step returns, reward shaping, Envelope, PCN, new
  networks, and trainable relabelers.

## Revised Proposal

### Method thesis

Test whether a fixed, audited share of transition updates from successful ore
episodes, optionally relabeled by one deterministic episode-level achieved-return
preference, is sufficient to produce stable greedy ore behavior under the
otherwise unchanged one-step PCQN.

### Data and relabel contract

1. Baseline insertion remains immediate. Each transition receives an immutable
   `trajectory_id`; its original reward, termination flags, behavior preference,
   and bootstrap mask never change.
2. At `terminated` or `truncated`, compute the protocol-scaled discounted
   episode return `G`. An episode is eligible when it contains a positive
   delivered-ore return; a partial episode is never eligible. A truncated
   episode can be eligible only if delivery occurred before truncation.
3. Compute the continuous HPR return-aligned episode label
   `w_hpr = softplus(G) / sum(softplus(G))`. This is the formula in Shianifar,
   Schukat, and Mason (2026), Section 3.1, Equation (1); Algorithm 1 lines 14–15
   applies it after episode completion to every episode transition. Primary
   source: `https://arxiv.org/html/2601.11604#S3.SS1`. This proposal differs by
   using protocol-scaled discounted episode return and then projecting to a
   finite pool; those are project-specific heuristic choices, not claimed HPR
   equivalence. Project the label once per episode to the existing
   32-point training pool by minimum Euclidean distance, breaking exact ties by
   ascending pool index. All transitions in the episode share this effective
   relabel preference. The frozen hypervolume reference point is not used.
4. Before any training, deterministic tests enumerate synthetic negative,
   zero, ore-dominant, and fuel-dominant return vectors to document the map. The
   map is never selected from validation or final-test outcomes.

### Exact 2x2 design

Let `A` enable successful-episode-stratified sampling and `R` enable relabeling.

| Cell | Sampling | Effective preference |
|---|---|---|
| A0R0 | 64 uniform buffer draws with replacement | behavior preference |
| A1R0 | 32 eligible-success draws + 32 uniform draws | behavior preference |
| A0R1 | 64 uniform draws | episode relabel only when the sampled transition belongs to an eligible episode; otherwise behavior preference |
| A1R1 | 32 eligible-success draws + 32 uniform draws | episode relabel for every eligible sampled transition, regardless of branch; otherwise behavior preference |

Eligible-success draws choose a trajectory uniformly, then a transition within
that trajectory uniformly. If no eligible trajectory exists, all 64 positions
fall back to the uniform branch and the fallback is counted. Duplicate indices
are allowed, matching the existing with-replacement uniform sampler. A successful
transition reached through the uniform branch is treated identically to the same
transition reached through the success branch for relabeling.

### Learning semantics and limitation

Environment dynamics and vector rewards are preference-independent. The
effective preference is supplied consistently to current-value prediction,
next-action selection, and target-network evaluation; recorded vector rewards
and termination flags remain unchanged. This is a deliberate outcome-conditioned
reweighting heuristic. The proposal does not claim an unbiased Bellman estimator,
guaranteed policy support, or equivalence to CAPQL HPR.

### Randomness, storage, and audit

- Use separate deterministic random streams for environment/action exploration,
  bootstrap masks, uniform replay draws, success-stratum draws, and any
  evaluation process.
- Preserve exact interaction, update, and batch-position counts. With batch 64
  and 995,001 updates, each run has 63,680,064 sampled positions.
- Store compact immutable trajectory metadata and aggregate counters per 10,000
  updates/checkpoint, not one text row per sampled position.
- Audit sampled origins, eligible counts, relabel attempts, actual
  changed-preference updates, projection distances, distinct effective labels,
  fallback counts, preference-index histograms, unique trajectory coverage,
  time overhead, and memory overhead.
- The existing 1,000,000-capacity buffer should not evict during a 1,000,000-step
  run; generation counters must nevertheless protect indices from stale reuse.

### Staged decision budget

- **Proposed fresh paired seeds:** `20264021`, `20264022`, `20264023`.
- **Stage F1:** A0R0 and A1R1 only, three paired seeds each: six runs, each
  1,000,000 interactions and 995,001 updates. This is a sufficiency screen, not
  attribution.
- **Stage F2:** Only if all A1R1 seeds satisfy the retained-ore rule and source
  audit passes, run A1R0 and A0R1 on the same three seeds: six additional runs.
  The proposed maximum is therefore twelve runs. F2 is a
  selection-conditioned exploratory decomposition on seeds for which A1R1
  already succeeded. It compares sampling and relabeling cells for those paired
  seeds, but does not independently confirm a general effect or remove selection
  bias. It does not alter credit propagation.
- **Validation:** the existing ten checkpoints at 100k increments, 32 fixed
  preferences, and 5 episodes per preference. Final test and shifts stay closed.

### Decision rules

- **Manipulation valid:** when an eligible trajectory exists, A1 batches contain
  exactly 32 success-branch positions; realized counters must match the contract.
- **Acquisition-limited:** a seed never creates an eligible episode. This fails
  sufficiency under the budget but is reported separately from replay-expression
  failure.
- **Expression pass:** both ore objectives meet the existing minimum 8/160
  positive episodes and two distinct positive values.
- **Retention pass:** the earliest expression-pass checkpoint must be at or
  before 800k and the same seed must pass at the next two checkpoints. A first
  pass at 900k or 1M is `late_inconclusive`, not retained success, and does not
  authorize extending the budget.
- **Study pass:** all three A1R1 seeds pass retention and all source/budget audits
  pass. Otherwise stop and preserve the negative or inconclusive result.
- **Attribution:** F2 can provide only a selection-conditioned exploratory
  decomposition of exposure and relabeling on the three paired seeds. No result
  in this design independently confirms a general factorial effect or identifies
  delayed credit causally.

### Claims and novelty boundary

The only prospective primary claim is bounded sufficiency of a precisely defined
replay intervention under matched budgets. A supporting claim may attribute an
effect to stratification, relabeling, or their interaction only as an
exploratory, selection-conditioned result if F2 is executed. The method borrows
HPR's `softplus(G)` episode-level heuristic and
DER's cross-preference replay motivation. Any novelty is limited to the audited
discrete-PCQN failure-mode integration and cannot be claimed before results and
cross-family review.

### Authority gate

This refinement is a design artifact only. It does not authorize code changes,
training, new protocol files, remediation v3, matrix execution, checkpoint lock,
final-test access, or paid review.

Before any execution amendment can be approved, measured wall time, peak memory,
and aggregate logging storage must be estimated from verified prior runs. F1
would contain 6,000,000 training interactions and 5,970,006 gradient updates;
the proposed twelve-run maximum would contain 12,000,000 interactions and
11,940,012 updates. Evaluation interactions remain a separately accounted
budget.


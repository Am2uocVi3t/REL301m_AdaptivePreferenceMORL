# ARIS Idea Report: Bounded Minecart Continuation

**Date:** 2026-10-17  
**Run:** `aris-minecart-offline-continuation-20261017`  
**Evidence status:** proposal-only; no new training, rollout, checkpoint selection, or final-test access

## Research contract

The current study cannot establish a Minecart course comparison because the
shared PCQN backbone failed qualification. Primary validation produced zero ore
for all Minecart arms, and the authorized proportional-TD-error PER remediation
also produced zero greedy ore at all 30 checkpoints. Existing training archives
nevertheless contain successful ore trajectories. The next defensible question
is therefore narrower:

> Can a fixed-budget replay mechanism that preserves complete successful
> trajectories and conditions updates on their achieved vector returns convert
> exploratory Minecart success into stable preference-conditioned greedy
> behavior?

This report reuses the 22-paper registered literature map, the completed v1/v2
qualification evidence, and the 2026-10-17 Minecart failure investigation. It
does not restart literature discovery and does not treat metadata, smoke tests,
or planned experiments as empirical support.

## Evidence boundary

- V1 showed transient acquisition followed by loss for some seeds.
- V2 exact proportional one-step TD-error PER was correctly configured but was
  insufficient: 30/30 checkpoints and 4,800 validation episodes had zero ore.
- All audited primary runs and all three V2 seeds contain positive ore points in
  their cumulative training archives.
- The leading explanation is long-horizon credit plus
  preference/trajectory-alignment and retention failure, not a proven causal
  mechanism.
- Final test, shifted environments, new training, and protocol mutation remain
  closed.

## Ranked candidate routes

| Rank | Route | Why it matches the failure | Scope cost | Current verdict |
|---|---|---|---|---|
| 1 | Achieved-Return Trajectory Replay (ARTR) | Keeps complete successful trajectories visible and relabels a sampled update toward a frozen training preference aligned with achieved vector return | Moderate; replay metadata and sampling logic, PCQN retained | Selected for a finite proposal |
| 2 | Envelope value updates | Shares value information across preferences in a discrete value-based learner | High; backbone and target objective change | Reserve pivot if ARTR is falsified |
| 3 | PCN-style return/horizon conditioning | Trains directly from successful trajectory archives | Highest; new archive, model inputs, and supervised objective | Reserve redesign, not a near-term amendment |

GPI-LS remains a comparator or allocator after the base learner qualifies. It is
not selected as the first remedy because weight prioritization does not itself
retain or propagate a rare successful trajectory.

## Selected idea: Achieved-Return Trajectory Replay

### Method thesis

Retain the current PCQN and frozen Minecart protocol, but replace a fixed share
of ordinary replay positions with transitions drawn from successful delivery
episodes. Optionally relabel any sampled transition belonging to such an episode
with one deterministic episode-level HPR-style preference projected onto the
existing 32-point training pool. The total interactions, gradient updates,
batch positions, and validation episodes remain unchanged.

### Minimal mechanism

1. Insert transitions immediately and assign immutable trajectory identifiers;
   compute a single protocol-scaled discounted episode return only when an
   episode terminates or truncates.
2. Mark an episode eligible only when it contains a positive ore delivery; do
   not infer success from TD error, mining alone, or an incomplete episode.
3. Compute `softplus(G)` and normalize it onto the simplex, following the
   return-aligned HPR heuristic in Shianifar et al. (2026), Section 3.1,
   Equation (1), then project once per episode to the closest member of the
   existing training pool. Protocol scaling and finite-pool projection are
   project-specific heuristic choices.
4. Predeclare four cells: uniform/original preference, stratified/original,
   uniform/episode relabel, and stratified/episode relabel. For stratified cells,
   32 of 64 batch positions use uniform-episode then uniform-transition
   sampling from eligible episodes; empty strata fall back to uniform replay.
5. Preserve the vector reward, one-step target, network, optimizer, exploration
   schedule, target-update schedule, interaction budget, update budget, and
   validation split.

The method is intentionally not described as novel or successful. It tests
bounded sufficiency of successful-experience exposure and relabeling under the
unchanged one-step learner; it cannot identify delayed credit causally.

## Claim candidates and falsifiers

### C1 — mechanism feasibility

**Candidate claim:** Under matched interaction and update budgets, ARTR can make
successful exploratory trajectories more available to preference-conditioned
updates than uniform replay or transition-level TD-error PER.

**Required evidence:** per-seed counts of successful trajectories, eligible
transitions, sampled successful transitions, relabeled positions, and preference
assignments, with exact budget accounting.

**Falsifier:** the configured sampling share or audit contract is not met, or
source/provenance audit cannot distinguish eligible episodes, attempted
relabels, actual preference changes, and projection distances.

### C2 — expression and retention

**Candidate claim:** Increased trajectory exposure can produce stable greedy ore
behavior, rather than a single lucky checkpoint.

**Required evidence:** all paired seeds pass the frozen ore gate at a
predeclared checkpoint and at two subsequent checkpoints, with nonzero `Mine`,
cargo, delivery, and positive-ore counts.

**Falsifier:** exposure rises but every seed remains at zero greedy ore, or the
earliest positive checkpoint is after 800k or is not retained at the next two
checkpoints. In that case the bounded intervention is insufficient under this
budget; no component stacking is allowed within the same plan.

## Novelty boundary

The proposal is grounded in Diverse Experience Replay, Hindsight Preference
Replay, Envelope Q-learning, and Pareto Conditioned Networks. The defensible
contribution, if later supported, is a carefully isolated Minecart failure-mode
test under matched budgets—not broad novelty for replay across preferences, nor
a new MORL paradigm. HPR is especially close prior art; any paper must describe
the difference as trajectory retention and a discrete PCQN integration under
this frozen study, not as invention of hindsight preference relabeling.

## Decision gate

The selected route is ready for a versioned scope-amendment proposal and
experiment plan only. Implementation, new training, remediation-v3 naming,
course-matrix execution, checkpoint locking, final-test access, paid review,
commit/push, and submission require separate authority.


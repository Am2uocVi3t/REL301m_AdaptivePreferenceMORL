# Research Proposal: Achieved-Return Trajectory Replay for Minecart PCQN

## Problem Anchor

- **Bottom-line problem:** The shared preference-conditioned value learner must
  express non-degenerate Minecart ore behavior before any adaptive allocation
  comparison can be scientifically interpreted.
- **Must-solve bottleneck:** Successful ore trajectories occur during
  exploration but are not converted into stable greedy behavior across
  preferences and checkpoints.
- **Non-goals:** This proposal does not optimize the final test, revive the
  blocked course matrix, claim broad adaptive-allocation novelty, or combine
  multiple backbone changes.
- **Constraints:** Keep the frozen Minecart environment, reward scale, training
  preference pool, validation split, network, optimizer, exploration schedule,
  interaction budget, update budget, checkpoint cadence, and final-test
  firewall. No implementation or execution occurs without a versioned amendment
  and supervisor approval.
- **Success condition:** In a future authorized, paired-seed feasibility study,
  every seed must satisfy the existing ore qualification gate and retain it for
  two subsequent predeclared checkpoints while all exposure and budget counters
  pass source audit.

## Technical Gap

The current learner stores a behavior preference per transition and performs a
one-step Double-DQN vector update under that preference. V1 occasionally learned
ore behavior and then lost it. V2 prioritized individual transitions by TD error
but remained zero at all greedy-validation checkpoints. Neither path preserves a
complete successful trajectory as a sampling unit or reassigns its transitions
to a preference supported by the achieved vector return. The training archive
shows acquisition is possible, so another undirected interaction increase is not
the smallest evidence-matched intervention.

## Method Thesis

- **One-sentence thesis:** Replaying a fixed share of complete successful
  trajectories under a frozen achieved-return-aligned preference can test
  whether cross-preference trajectory retention is the missing link between
  exploratory success and stable greedy Minecart behavior.
- **Why smallest adequate:** It retains PCQN and changes only replay metadata,
  sampling, and the preference attached to selected replay positions.
- **Why timely:** It directly tests the gap between classic diverse replay and
  recent hindsight preference relabeling without adding an LLM, world model, or
  unrelated modern component.

## Contribution Focus

- **Dominant contribution:** A predeclared, provenance-complete ARTR mechanism
  and falsification test for successful-trajectory retention in discrete
  preference-conditioned MORL.
- **Optional supporting contribution:** Acquisition/expression/retention
  diagnostics that separate replay exposure from policy behavior.
- **Explicit non-contributions:** Hindsight relabeling in general, Envelope
  learning, PCN, reward shaping, n-step returns, new allocation signals, or a
  complete course comparison.

## Proposed Method

### Complexity Budget

- **Frozen/reused:** PCQN architecture, vector rewards, masked Huber loss,
  bootstrap heads, optimizer, exploration, target updates, protocol pools,
  budgets, and validation evaluator.
- **New trainable components:** none.
- **New deterministic data path:** episode identifiers, discounted vector
  return-to-go, delivery-success flag, relabel-preference identifier, and
  replay-origin counters.
- **Excluded:** reward shaping, demonstrations, n-step targets, new networks,
  trainable relabelers, hyperparameter sweeps, Envelope/PCN stacking.

### System Overview

```text
environment transition + behavior preference
            |
            v
temporary episode buffer -- episode ends --> discounted vector return-to-go
            |                                  + delivery-success flag
            v
general replay store <---------------- successful-trajectory index
            |                                  |
            +------ fixed-size mixed batch ----+
                               |
                  deterministic relabel map
                               |
          existing PCQN one-step vector update
```

### Core Mechanism

- **Input/output:** The buffer receives the existing transition plus
  `episode_id` and step index; at episode end it writes return-to-go and success
  metadata. Sampling returns the existing tensors plus `sample_origin`,
  `trajectory_id`, and `relabel_preference_id`.
- **Success definition:** a completed episode containing positive delivered ore
  in either ore objective. Mining without delivery is logged separately but is
  not eligible for the success stratum.
- **Relabel map:** let `G_t` be discounted vector return-to-go in protocol-scaled
  units and `r_ref` the frozen reference point. Set
  `z_t = max(G_t - r_ref, 0)`. If `||z_t||_2 > 0`, choose the member of the
  existing 32-preference training pool with maximum cosine similarity to
  `z_t`; otherwise keep the behavior preference. Ties use ascending pool index.
- **Sampling:** a single frozen mixture coefficient controls the fraction of
  batch positions selected uniformly from eligible successful trajectories;
  remaining positions use the baseline replay sampler. Successful-trajectory
  positions are sampled uniformly first by trajectory and then by transition so
  long episodes cannot dominate solely through length.
- **Budget matching:** the batch size and number of optimizer steps are
  unchanged. Relabeled positions replace baseline positions; they never add
  extra updates.
- **Training objective:** unchanged vector Double-DQN target and masked Huber
  loss, evaluated under the relabeled preference for eligible positions and the
  behavior preference otherwise.

### Integration

The change attaches at replay insertion and sampling. Environment interaction,
action selection, model inputs, optimizer stepping, checkpointing, and the
validation evaluator remain frozen. Every sampled position must log its origin,
trajectory identifier, behavior preference, effective preference, and whether
the two differ.

### Failure Modes and Diagnostics

- **No successful trajectory acquired:** ARTR has nothing to reuse; report an
  acquisition failure rather than a replay failure.
- **Successful trajectories exist but are rarely replayed:** source counters
  reveal a sampling implementation or capacity problem.
- **Exposure increases without greedy expression:** reject the relabeling remedy
  if `Mine` margins and ore counts remain zero.
- **Expression appears once then disappears:** fail the retention gate; do not
  select the isolated checkpoint.
- **Relabeling collapses to a few preferences:** report pool-index entropy and
  per-preference counts; do not tune from final-test data.

### Novelty and Elegance Argument

Abels et al. share experiences across preferences; HPR relabels preferences from
achieved vector returns; Envelope updates and PCN provide larger alternative
backbones. The proposal's value is not ownership of those ideas. Its focused
contribution would be a minimal discrete-PCQN integration with complete
trajectory provenance and a falsifier that distinguishes acquisition, exposure,
expression, and retention. This is deliberately narrower and more defensible
than adding Envelope or PCN in parallel.

## Claim-Driven Validation Sketch

### Claim 1: ARTR changes successful-trajectory exposure under matched budgets

- **Minimal experiment:** paired fresh seeds, frozen protocol and budgets,
  baseline replay versus full ARTR.
- **Ablations:** trajectory-stratified replay without preference relabeling, and
  preference relabeling without trajectory stratification, only after source
  audit passes.
- **Metrics:** eligible successful trajectories, successful batch positions,
  unique trajectories replayed, relabel rate, effective-preference distribution,
  exact interactions and updates.
- **Expected evidence:** ARTR increases auditable successful-trajectory exposure
  without increasing compute accounting. This is an expectation, not a result.

### Claim 2: Exposure produces retained greedy ore behavior

- **Minimal experiment:** nominal validation only at 100k-step intervals using
  the existing 32 preferences and 5 episodes per preference.
- **Metrics:** `Mine` selections, cargo acquisitions, deliveries, positive ore
  episodes and values, per-preference action margins, scaled hypervolume and
  expected utility as secondary metrics.
- **Success:** all seeds meet the existing 8/160 positive-episode and two-value
  gate for both ore objectives and pass the same gate at two subsequent
  checkpoints.
- **Failure:** if exposure rises but expression or retention fails, stop and
  reject ARTR as the main remedy for this scope.

## Experiment Handoff Inputs

- **Must-prove:** matched-budget exposure and stable greedy expression.
- **Must-run controls:** frozen uniform replay and the minimum 2x2 replay/relabel
  decomposition if the main comparison is promising.
- **Critical data:** training and nominal validation only; final test and shifted
  environments remain forbidden.
- **Highest-risk assumptions:** enough successful trajectories are acquired in
  every seed, and one-step updates can use them once their preference alignment
  is repaired.

## Compute and Timeline Estimate

No compute is authorized by this proposal. A future amendment should retain the
existing 1,000,000 interactions and 995,001 updates per run for comparability,
start with a bounded paired three-seed feasibility block, and predeclare a hard
stop before any larger matrix. Exact wall time and total CPU/GPU hours must be
estimated from verified prior run logs before approval.


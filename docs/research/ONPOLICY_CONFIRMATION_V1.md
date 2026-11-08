# Minecart PPO G confirmation v1

Base `e266da4`; user authorized starting confirmation after audited C pass.
Prospective scope: three fresh seeds20264311/12/13, same frozen conditional
candidate and original32 episode-uniform training weights, fresh initialization,
4M interactions each. No optimizer/model/entropy/normalization tuning, warm start,
seed replacement, extension or original final-test access.

## Decisions frozen before implementation

- Separate G runner and protocol preserve all S/C/P2 source and evidence.
  C's evidence hash and full gate pass are prerequisites.
- New development preference set:32 Dirichlet(alpha1) weights from seed20264421,
  explicitly stored. Anchors are the original pool's first7 weights (corners,
  center, edge midpoints), evaluated as a SEPARATE kind, never pooled into the
  new-preference mean. Original test split is not copied into the new protocol.
- Task cases: both existing task profiles x10 NEW environment seeds20264431..440.
  Validation and anchors: each x3 environment seeds20264431..433.
  Both sampled and argmax at500k/1M/2M/4M. 274 episodes/checkpoint,
  1,096/job,3,288 overall, <=3,288,000 development steps. No final-test steps.
- Final4M only: every seed must meet>=8/10 deliveries and utility above frozen
  idle at BOTH task profiles in BOTH inference modes. No selecting a preferred
  mode/seed/checkpoint after observing confirmation. Preference coverage/utility
  and native vectors reported regardless of gate. Training seeds are the
  replication units, not repeated episodes.
- Same7,815 rounds,250,080 actor /500,160 critic updates/job; cohort12M training,
  750,240 actor /1,500,480 critic updates. Each stream's sampler uses
  SeedSequence([its training seed,20]), preserving C semantics.
- Evaluation isolates all training RNG; per-case seed uses environment seed,
  preference index, and explicit kind code task0/validation1/anchor2. No geometry
  or dynamics changes: confirmation is about seed/preference stability only.
- Three concurrent independent local CUDA workers, with OS leases and launcher
  duplicate checks. Per-job source-bound exact resume is explicit only. No
  retries, unattended follow-on stages or automatic scientific gate unlock.
  Native terminal must recognize all three G jobs before dispatch.
- F0 engineering: each seed continuous1088 vs512 + process-tree kill + resume576,
  including final64-sample minibatch;6528 total interactions. Prior engineering
  S+C25,472 gives32,000 before new unit executions, within original50k ceiling.
  Also test full274-case evaluation matrix/RNG isolation and concurrency.
- Source hashes, runtime/environment/protocol, sampling state, exposure counts,
  raw/discounted/scaled returns and task traces retained as in C. All managed
  storage remains D:. No paid service or remote machine used.

The algorithm/source mapping is unchanged from ONPOLICY_IMPLEMENTATION_V1 and
ONPOLICY_CONDITIONAL_V1. This confirms a conditional backbone, not adaptive
allocation benefit, optimality, arbitrary preference or dynamics robustness.

## Executed engineering qualification (3 November 2026)

`research/qualification/minecart_onpolicy_confirmation_v1.json` records all three
seeds: concurrent continuous1088 vs512 + actual process-tree kill + resume576,
exact model/optimizers/eight environments/global and preference RNG/exposure,
training losses/returns and final64-sample partial batch. Initial parameter
hashes are distinct. Runtime binding includes the resolved training seed so a
different seed's checkpoint cannot be accepted under the same cohort plan.

Qualification cost6528 training interactions and7372 development-evaluation
steps. Shared reset unit execution adds64; cumulative engineering training
32,064 stays below50k. The full274-case evaluation/RNG-isolation fixture uses
horizon1 and is NOT task competence evidence. All226 tests pass/4 existing
skips, with format/lint/types/Bandit/compile/diff checks passing. Native tests
track three independent seed commands, per-seed logs and completed state.
This is executor-only technical evidence, not independent semantic review.

Launch from clean qualified committed source:
`powershell -File scripts/start_minecart_confirmation.ps1`.
Completed jobs are immutable. If all workers have stopped, an inspected
individual recovery can use `-ResumeSeed 20264311` (or another frozen seed).
No automatic restarts or retries. Outputs stay under
`artifacts/minecart-onpolicy-confirmation-v1` on D:.

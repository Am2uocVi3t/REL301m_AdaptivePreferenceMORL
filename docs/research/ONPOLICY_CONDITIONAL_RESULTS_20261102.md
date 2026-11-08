# Minecart PPO conditional C — completed pilot

Frozen4M job completed normally from clean source660aa97, fresh initialization,
one training seed20264111, uniform episode sampling of32 original training
weights. Both inference modes pass BOTH final task-profile gates. This is
bounded conditional feasibility, not multi-seed or arbitrary-weight competence.

Evidence: `research/evidence/minecart_onpolicy_conditional_v1.json`, including
all928 development episode records, milestone summaries, source/artifact hashes
and exact preference exposure accounting. Audit is executor-only; no independent
semantic-review PASS is claimed. Original final-test locks remain unchanged.

## Prospectively selected final4M checkpoint

| Profile | Mode | Deliveries | Mean utility | Mean steps |
|---|---|---:|---:|---:|
| Balanced `[.45,.45,.1]` | sampled |10/10| .455617 |17.3|
| Balanced `[.45,.45,.1]` | argmax |10/10| .463566 |17.0|
| Ore1-heavy `[.8,.1,.1]` | sampled |10/10| .765890 |19.9|
| Ore1-heavy `[.8,.1,.1]` | argmax |10/10| .829602 |15.0|

All four utilities exceed the frozen idle utility-.164942 and meet>=8/10.
The final result uses the declared4M checkpoint, not a selected intermediate.

At balanced weights, final mean raw ore1/ore2 deliveries were approximately
.115/1.374; at ore1-heavy weights they were1.355/.145 in both modes. The
observed outputs differ with conditioning. These are descriptive means over
ten development cases/profile; case RNG is profile-dependent, so this is not a
new controlled causal test of preference response or an optimality claim.

## Checkpoint trajectory

| Steps | Sampled p0/p1 deliveries | Argmax p0/p1 deliveries |
|---:|---|---|
|500k|4/10,6/10|0/10,0/10|
|1M|10/10,10/10|0/10,10/10|
|2M|10/10,10/10|10/10,10/10|
|4M final|10/10,10/10|10/10,10/10|

Each checkpoint also evaluates32 frozen validation weights x3 seeds x2 modes.
Final ore-positive episodes are76/96 sampled and81/96 argmax; corresponding
mean utility.223307/.252553. Some weights prioritize fuel, so absent ore alone
is not necessarily a failure there. Neither these counts nor positive mean
utility establish correct behavior at every weight or broad generalization.

## Executed audit

- Training4,000,000;7,815 rounds;250,080 actor /500,160 critic updates.
- Development928 episodes /88,828 steps; final-test0; no retry or extension.
- Clean manifest/source/protocol match qualified hashes; final checkpoint hash,
  initial parameter hash and saved optimizer counters match completion.
- All4 evaluation receipts/file hashes and928 vector/utility/case records
  checked. All160 task NPZ hashes, lengths, actions and per-step raw/discounted
  returns rechecked using the runtime's frozen float32 scale representation.
- Reconstructed exposure from158,616 completed episodes plus8 active streams
  matches sampler state and the saved preference_exposure.json exactly.
- All32 weights sampled:4,835–5,132 episode draws each. Actual interaction
  counts67,760–228,489 each because episode lengths differ. Uniform episode
  sampling must not be described as uniform interaction allocation.
- Model tensors and recorded loss diagnostics finite. Worker exited, native
  monitor complete, GPU idle at inspection. No new training launched.

## Scope and next gate

C's same-seed feasibility is supported at both frozen task profiles. This does
not establish adaptive-allocation benefit, superiority, dynamics robustness or
independent-seed stability. S and P2 remain preserved; Lunar is unchanged.

Next useful stage is prospectively frozen G confirmation: three fresh training
seeds and new development preferences/cases, with source/resume/monitor and
exact budgets qualified before dispatch. No automatic G, Lunar or original
final-test access follows this audit. Phase4 remains active.

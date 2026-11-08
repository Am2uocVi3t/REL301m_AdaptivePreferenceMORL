# Minecart PPO G confirmation — completed

All three fresh training seeds completed their fixed4M budgets normally.
Every final checkpoint meets BOTH task profiles in BOTH inference modes:
10/10 deliveries per cell and utility above the frozen idle reference.
This confirms the predeclared task gate across three training seeds on the
fixed nominal Minecart geometry and new development cases. It does not prove
optimality, arbitrary-preference competence, dynamics robustness or adaptive
allocation benefit. Lunar is unchanged.

Evidence: `research/evidence/minecart_onpolicy_confirmation_v1.json` includes
all3,288 episode records, separate anchor/new-preference summaries, source and
artifact hashes, exposure accounting and executor audit outcome. Source at
dispatch: clean a316d4a. No independent semantic-review PASS is claimed.

## Final4M checkpoint, no selection

Each success entry is for10 new task environment cases. The two profiles are
balanced `[.45,.45,.1]` and ore1-heavy `[.8,.1,.1]`.

| Training seed | Sampled p0/p1 deliveries | Argmax p0/p1 deliveries | Sampled utility p0/p1 | Argmax utility p0/p1 |
|---|---|---|---|---|
|20264311|10/10,10/10|10/10,10/10|.4462,.8177|.4646,.8271|
|20264312|10/10,10/10|10/10,10/10|.3595,.8293|.4666,.8344|
|20264313|10/10,10/10|10/10,10/10|.4492,.8067|.4609,.8401|

Idle utility at both profiles is-.164942. All12 final task cells pass; the
three independently trained models are the replication units. The120 final
task episodes are not120 independent training replicates or a universal100%
success guarantee. No seed was substituted or checkpoint/mode chosen afterward.

## New development preferences, separate from anchors

32 fresh Dirichlet preferences, three new episode cases per weight/mode.
Expected utility uses each policy's discounted-scaled return at its own weight.
Mean and sample SD below are over THREE training seeds.

| Mode | EU per seed | Seed mean +/- SD | Ore-positive episodes per seed /96 |
|---|---|---|---|
|sampled|.210591,.158454,.226004|.198350 +/- .035400|83,82,82|
|argmax|.191416,.096828,.242163|.176802 +/- .073761|80,76,84|

Hypervolume of mean vector returns over these32 weights uses the unchanged
frozen reference: sampled .112830/.119614/.109573; argmax
.092382/.120217/.110362. No reference-point tuning or significance/superiority
claim. Seven training anchors are evaluated and summarized separately in the
evidence, never pooled into the new-weight average. Some preferences prioritize
fuel; ore occurrence alone is not an appropriate universal success metric.

## Audit and accounting

-12,000,000 training interactions;750,240 actor /1,500,480 critic updates.
-3,288 development episodes /372,775 steps;0 original final-test steps.
- All3 clean manifests/source/protocol/runtime/seed bindings match qualified
  code. Final checkpoint hashes, initial hashes, saved optimizer counters and
  training trace chain match completion; initial hashes distinct across seeds.
- All12 milestone file receipts,3,288 episode vectors/utilities/case counts
  checked; all480 task NPZ hashes, per-step rewards, discounted/raw returns,
  lengths and action counts rechecked with the runtime float32 fixed scale.
- Completed + active episode lengths reconcile exactly to4M per seed.
  Draw/interaction counts per training weight match saved sampler state and
  preference_exposure.json. All32 weights sampled in every job. Episodes were
  sampled uniformly; interaction exposure differs because episode lengths differ.
- Model tensors and recorded losses finite. No training workers remain; GPU
  idle at inspection. No retry, extension or subsequent training launched.

## Interpretation and next work

The frozen conditional backbone's two-profile task competence replicated in
three fresh seeds and new development cases. This is materially stronger than
the single-seed C pilot. Uniform sampling and PPO are existing methods; the
confirmation does not establish the original adaptive-allocation hypotheses.
All earlier failures, S/C pilots and original scientific locks are retained.

Use this bounded evidence in the course report/demo. Further work should have
a separate declared scope: Lunar task feasibility and/or a matched
uniform/random/adaptive allocation comparison. Do not extend G or treat this
as permission to access the original final test. Phase4 remains active.

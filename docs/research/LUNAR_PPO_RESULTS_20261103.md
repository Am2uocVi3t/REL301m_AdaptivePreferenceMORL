# Lunar PPO specialist — completed single-seed pilot

Fixed4M job20265311 completed normally. Final-only gate passes in both modes
at the trained landing-heavy preference[.7,.1,.1,.1]:10/10 native+100 AND pad-x
success. The uniform secondary diagnostic also has10/10 in both modes. This
is one trained seed at one preference, not independent replication or arbitrary
preference control. No new training has been launched.

## Final4M checkpoint

| Profile | Mode | Native+100 and pad-x /10 | Mean utility | Mean steps |
|---|---|---:|---:|---:|
| Landing-heavy | sampled |10| .097226 |227.0|
| Landing-heavy | argmax |10| .080849 |238.7|
| Uniform secondary | sampled |10|-.025937|224.7|
| Uniform secondary | argmax |10|-.045538|251.5|

Original scalar score means273.65/271.90 for the trained profile are descriptive;
the predeclared gate is native+100 AND inside pad, not a standard-Gym solved
guarantee. Negative uniform utility despite landing illustrates why task and
trade-off performance must be kept distinct. Final validation32 preferences
x3 cases:79/96 pad successes sampled,73/96 argmax; those were not all trained
preferences or a uniform-performance guarantee.

Primary profile milestone pad successes sampled/argmax:500k0/0,1M0/0,2M4/3,
4M10/10. Only4M selects the outcome; no favorable checkpoint substitution.

## Audit/accounting

Evidence: `research/evidence/lunar_onpolicy_specialist_v1.json` contains all928
development episode records, stage summaries and source/checkpoint hashes.
-4M interactions,3909 rounds,125088 actor/250176 critic updates.
-928 development episodes /315564 steps;0 final test,0 main-run restoration steps.
- Source/runtime/Box2D binary bindings match technical qualification and clean
  launch d5ff9e6. Final checkpoint, optimizer counters, completed+partial episode
  lengths, finite model/losses and four evaluation receipts match.
- All160 task NPZ hashes, native vectors, discount/scaling, utilities, action
  counts and case sets checked. All160 action traces were also replayed in the
  pinned Box2D engine: every observed state/reward, final end flags, pad x,
  original score, angle and velocity matched exactly.
- Physical replay cost67807 steps is additional diagnostic verification of the
  same recorded actions/cases, not new independent episodes or extra training.
- Audit is executor-only, not an independent semantic-review PASS. GPU is idle.

## Next gate

Use the result in the working course report with its single-seed scope. A
separately frozen independent-seed confirmation and/or conditional pilot is
needed for stronger Lunar claims. Existing demo release still uses legacy Lunar
until a new, behavior-verified package explicitly promotes the audited model.
Minecart confirmation remains three seeds; original final-test/allocation
locks remain unchanged. No automatic extension, replay retraining or seed switch.

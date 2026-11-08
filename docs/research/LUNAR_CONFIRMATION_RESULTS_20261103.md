# Lunar prospective confirmation results — 3 November 2026

COMPLETE, executor-audited. Two fresh training seeds; observed pilot20265311
is excluded from the prospective n=2 group. No completed research was restarted.

| Seed | Final steps | Sampled pad success | Argmax pad success | Sampled utility | Argmax utility |
|---|---:|---:|---:|---:|---:|
| 20266311 |4,000,000|10/10|10/10|0.195926|0.174052|
| 20266312 |4,000,000|10/10|10/10|0.141293|0.129792|

Both fresh seeds pass the frozen primary gate in BOTH modes: at least8/10
native+100 terminations with final lander x inside the native pad, at the
TRAINED preference [.7,.1,.1,.1] and final4M only. Uniform-profile landings
were10/10 for20266311 and9/10 for20266312, in both modes. Uniform is secondary.
Across-seed primary utility mean/sample SD: sampled .168610 / .038632;
argmax .151922 / .031297. These are two training replication units, not40.
No significance, exact success-probability or arbitrary-preference claim.

The second seed was0/10 at2M but10/10 in both modes at4M. The learning curve
was not monotonic; intermediate checkpoints were not selected or substituted.
This observation does not imply that extending failed studies always works,
or establish a unique cause. No extra budget or retries were used.

Final32-weight validation: sampled pad75/96 and71/96; argmax69/96 and67/96.
EU sampled .054943/.032815, argmax .036807/.023628 respectively. These results
do not establish reliable behavior at every preference. The previous frozen
actor corner diagnosis remains valid for its recorded pilot/demo models.

Accounting:8M training interactions,250176 actor/500352 critic updates,
1856 development episodes /630302 evaluation steps;0 final-test steps and
0 training-restoration steps. Separately, engineering qualification used8448
training interactions,684 reconstruction and964 development steps.
All320 task traces replayed exactly in the pinned physics for112508 additional
diagnostic replay steps; these are reused actions/cases, not independent episodes.

Audit checked source/runtime/seed/clean launch bindings, distinct initial hashes,
final checkpoint/pointer checksums, optimizer/training budgets, episode-length
accounting, finite parameters/losses, all1856 raw/scaled/utility records and
evaluation-file receipts. Every task trace reproduced observations, rewards,
original score, end flags, native outcome, pad position, angle and velocity.
Executed auditor: scripts/audit_lunar_confirmation.py. Evidence:
research/evidence/lunar_onpolicy_confirmation_v1.json. Executor-only review;
no independent semantic/scientific-review PASS is claimed.

No active training remains. Preserve final checkpoints, pilot and released ZIP.
No automatic training, seed extension, test access or best-seed promotion.
The existing demo continues to use the labelled pilot; the working report now
includes confirmation separately. Phase4/original adaptive-allocation locks
remain unchanged. Lecturer rubric/deadline is still an external question.

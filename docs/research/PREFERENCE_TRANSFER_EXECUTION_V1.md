# Preference transfer execution — 2026-11-02

User authorized the staged plan on 2 November: “cứ thực hiện theo kế hoạch đi”.
This permits P1 and conditional preparation/qualified execution of P2, not an
automatic run of every proposed stage or an original scientific-gate unlock.

## P1 frozen inference factorial

Protocol: `configs/experiments/preference_transfer_p1_v1.json`.
The 12 previous final checkpoints and both environment protocols remain pinned.
960 episodes, at most 960k diagnostic steps, zero training/update/final test.
The existing 32 training weights form the fixed source bank, recorded explicitly.
GPI takes the best target-weight head-mean value over source weights per action;
one entire source vector is retained, not separate coordinate maxima. Source
ties use first bank index; action ties use first action. No theorem guarantee
is claimed for these approximate conditional values.

Qualification: `research/qualification/preference_transfer_p1_v1.json`:
20 engineering episodes / 9,801 steps, 378 retained probes checked against
literal source-by-source CUDA calls, exact mean baseline replication in both
environments, immutable input checkpoints. These episodes are separate from
the 960-case matrix. New unit tests check batch semantics, source/target roles
and indivisible vector selection. Required quality gate: 191 passed / four
existing skips; format/lint/types/Bandit/compile/diff checks pass.

Dispatch from a clean committed tree after qualification:

```powershell
. scripts/use_d_runtime.ps1
. scripts/start_preference_transfer.ps1
```

This reuses the qualified local Windows independent-process mechanism; no
runtime rebuild, remote/paid provider, ARIS paid dispatch or scheduler is used.
The coordinator checks its Windows Job independence and qualified actor hashes,
launches at most three workers and refuses to overwrite/retry an existing run.
All outputs and caches are on D:. Do not edit tracked files while P1 runs:
each worker requires clean identical start/end Git provenance.

Inspect `artifacts/preference-transfer-p1-v1/execution_status.json`, worker
`progress.json`, logs, process birth/liveness and GPU; raw stale flags alone
are not a live-process witness. After all 12 jobs complete:

```powershell
. scripts/use_d_runtime.ps1
artifacts/gpu-runtime/Scripts/python.exe scripts/audit_preference_transfer.py
```

Audit retains native raw/discounted/scaled returns and traces, paired utility
differences, every seed/profile/policy outcome, and prospectively defined gates.
Minecart requires both task preferences; Lunar's landing-heavy is task-oriented,
while its uniform profile remains secondary, matching the original task gate.
8/10 outcomes plus positive utility difference against mean-greedy are required
for every seed of one fixed n-step arm. No best-seed selection. If Minecart
does not qualify, P2 may proceed only after its own executable freeze and
source/loss/RNG/resume qualification. Final test remains inaccessible.

## P1 completed; conditional P2 prepared

P1 completed all 960 episodes /443,192 steps. All predeclared gates failed;
Lunar n20 has a bounded positive response to GPI, but Minecart is not qualified.
See `PREFERENCE_TRANSFER_P1_RESULTS_20261102.md`. User authorization therefore
permits the next planned Minecart study, after the qualifications below.

P2 protocol: `configs/experiments/preference_recovery_p2_v1.json` pins the P1
evidence hash and unchanged environment protocol. Four cells A/B/C/D cross
stored versus uniform counterfactual update weights with vector-only versus
fixed .5/.5 vector/scalar Huber. Three paired new seeds, n=1, 500k/job: 12 jobs,
6M training interactions /1,485,012 updates. Behavior sampling and mean-greedy
evaluation remain common. Independent named RNG streams prevent relabel draws
from consuming behavior/head/replay/mask randomness; all streams are saved.

Validation is 32×3 episodes at each of 100k/250k/500k (3,456 total); separate
task traces are only at 500k (240 episodes). Train/validation/task/engineering
counts remain separate. Raw and discounted validation vectors are retained in
scaled coordinates and converted back using the fixed scale; task traces retain
actual native per-step rewards and checked sums. Frozen HV reference is unchanged.
Only final checkpoint task/paired utility decides the gate, not intermediate HV.

Source isolation: the old runners, learners, protocols and completed artifacts
are unchanged. New runner snapshots model/target/optimizer, replay, discounts,
sampler and all RNGs at reconstructible fresh-episode boundaries using the
qualified two-generation atomic checkpoint helper. No arbitrary mid-episode
engine serialization or old-training numerical equivalence is claimed.

Before dispatch, `scripts/qualify_preference_recovery.py` must pass all four
CUDA cells, identical paired initialization, exact fresh-process forced-kill /
resume comparisons and active-duplicate rejection, with source hashes recorded
in `research/qualification/preference_recovery_p2_v1.json`. These engineering
runs are not evidence of task competence. One pre-lint engineering attempt was
stopped to correct two overlong documentation strings; partial output is retained
under `artifacts/preference-recovery-p2-qualification-v1-pre-lint` with a separately
recorded conservative upper bound of 42,782 training interactions. It is not a
replacement scientific seed. The clean qualification is a separate 96k compute
allocation and both amounts stay outside the 6M study.

Qualification completed: all four cells passed exact kill/resume and duplicate
rejection; paired initial parameters match, final parameter hashes differ as
expected across treatments. The clean engineering cohort used 96,000 training
interactions and 8,000 validation steps. An additional two-episode /2,000-step
native task-trace witness passed the actual final-task evaluator and trace audit.
All required repository checks pass: 194 tests passed /four existing skips.
These are engineering outcomes, not empirical task qualification of P2.

Main invocation after a clean source commit and PASS receipt:

```powershell
. scripts/use_d_runtime.ps1
. scripts/start_preference_recovery.ps1
```

The independent coordinator verifies P1 insufficiency and qualification source
hashes, records process identities and dispatches at most three finite workers.
It stops new dispatch on a technical failure; no automatic retry. Existing
execution cannot be overwritten. Operator-controlled exact resume is supported
by the Python coordinator's `--resume-existing` after inspecting live identities,
source binding and recovery snapshots; launch outside Windows Jobs using the
same documented WMI/base-interpreter environment, not a plain session process.

Observe `artifacts/preference-recovery-p2-v1/execution_status.json`, worker
heartbeats and process birth/liveness. On normal completion, the coordinator
runs `scripts/analyze_preference_recovery.py` and writes bounded numeric/source
analysis to `artifacts/preference-recovery-p2-v1/analysis.json`. Version/register
that evidence after inspecting the completed run. No automatic claim, phase,
checkpoint-lock, P3, final-test or report-success transition follows. P3/P4 still
need their separately frozen protocols; a failing P2 stops at its fixed budget.

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

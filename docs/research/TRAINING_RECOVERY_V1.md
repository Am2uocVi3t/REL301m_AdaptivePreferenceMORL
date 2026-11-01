# Durable local training recovery

This technical amendment is authorized by the user's 1 November 2026 instruction
to implement the discussed launch/resume repairs before continuing training.
It changes process/checkpoint handling, not the learning hypothesis or budgets.
Original matrix/F1/final-test gates remain locked. There is no paid dispatch,
scheduled task, installed service, automatic seed replacement or automatic retry.

## Preserved study and accounting

The parent is `configs/experiments/credit_assignment_v1.json`. Its three completed
Lunar jobs remain in their original directories and are hash-bound in
`research/qualification/credit_recovery_retained_jobs_v1.json`. The three
interrupted runs remain intact for forensics and are not exact-resume inputs.
They restart once from their original seeds in new recovery directories; the
six unstarted Minecart jobs use the unchanged parent plan. The recovery dispatch
therefore contains nine jobs / 4.5M logical training interactions / 1,113,759
updates. Together with the three retained jobs, the final cohort has 12 complete
500k jobs, if execution succeeds. Completion is not task qualification.

Interrupted original work is additional cost: at least 925k interactions were
recorded. Use a conservative upper bound of 1M, including interruption at a
progress-write boundary (the amendment's 999997 interval estimate excludes up to
three such boundary steps). Do not add partial runs as extra independent seeds.
Engineering qualification, replayed work, checkpoint validation and task
diagnostics have separate accounting. Unobserved tail work is bounded, not
invented as an exact counter.

## Why the launch changed

The original interruption trigger remains unknown. Reproduction established a
Windows lifetime hazard: a process may keep membership in a kill-on-close Job
even with a detached console and breakaway flags. The Windows venv redirector
also introduces a kill-on-close Job. Failed witnesses v1/v2 remain on D:.

The launcher now asks the existing local Windows WMI provider to create a
hidden, immediately launched process with explicit breakaway flags and the
D-drive environment. It invokes the same base Python interpreter with the venv
marker, preserving the qualified CUDA site-packages. It then verifies that the
worker has no Job membership. A fresh invocation observed the witness surviving
its launching parent's kill-on-close Job teardown. The independent process also
passes a seeded CUDA backward witness. This establishes the tested process
lifetime behavior; it does not promise survival of reboot, logout or power loss.

Primary implementation references:

- [Microsoft process creation flags](https://learn.microsoft.com/en-us/windows/win32/procthread/process-creation-flags)
- [Microsoft WMI process creation](https://learn.microsoft.com/en-us/windows/win32/cimwin32prov/create-method-in-class-win32-process)
- [Microsoft process startup environment](https://learn.microsoft.com/en-us/windows/win32/cimwin32prov/win32-processstartup)
- [CPython Windows launcher source](https://github.com/python/cpython/blob/v3.11.9/PC/launcher.c)

## Checkpoint contract

The first completed episode after each 10k interval commits a recovery snapshot.
The n-step queue must be empty and the next episode must have just reset. Save:
online/target parameters, optimizer, replay arrays and all replay Generators,
per-transition discounts, sampler state, exploration/action/global NumPy/Python/
Torch/CUDA RNGs, preference/head, counters and histories. Reconstruct the reset
from its pre-reset RNG state, assert the initial observation exactly matches,
then restore the post-reset RNG state before taking the next action.

Snapshots are flushed to disk before atomically replacing a checksum-bound
latest pointer; two generations remain. Source, protocol, amendment, runtime and
device bindings must match on resume. These are trusted local pickle files.
True mid-episode simulation serialization is not claimed. An abrupt interruption
rewinds to the last boundary; discarded/replayed compute must be reported
separately. Three legacy partial jobs lack this state and cannot use this contract.

The learner compatibility witness compares old/new runners on both environments
and both n-step arms. Fresh-process forced-kill/resume tests compare complete
models, targets, optimizer tensors, episode summaries, losses and evaluation
returns against continuous controls. Additional tests kill after unsaved updates
to verify deterministic rewind/replay, rather than only a clean checkpoint exit.
Qualification is engineering evidence, not evidence of landing or ore competence.

Required repository checks pass with 186 tests and four existing skips. The new
recovery files also pass a Windows-targeted type check. A whole-repository
Windows-targeted check still reports 14 pre-existing Unix-only ARIS/F1 API
errors; those execution paths remain outside this local recovery workflow.
The standard required type-check configuration passes all source/scripts.
Qualification receipts transparently record AST-equivalent comment and
unreachable-POSIX typing changes made after the GPU witnesses; raw witness
snapshots and their original bindings remain preserved.

## Operating commands

From the repository on D:, after committed source and passing qualifications:

```powershell
. scripts/use_d_runtime.ps1
& scripts/start_credit_recovery.ps1
.venv/Scripts/python.exe scripts/check_credit_recovery.py
```

The launcher rejects an already-live coordinator using PID plus creation time.
OS-held byte leases exclude duplicate coordinators and workers and release on
process death. Live heartbeat/PID checks supersede stale status labels.

After an actual interruption, inspect the evidence first. The explicit command
below may adopt still-live workers and resume recoverable jobs; it never resumes
a completed job or silently retries a job without a recovery checkpoint:

```powershell
& scripts/start_credit_recovery.ps1 -ResumeExisting
```

The new root is `artifacts/credit-assignment-recovery-v1/`. Read
`execution_status.json`, `worker.stderr.log`, per-job logs and `resume_latest.json`.
No new jobs are dispatched after a technical failure; already-live workers may
finish. After all 12 jobs complete, the coordinator runs the recovery-aware
numerical audit and retains `postprocess.log`. Scientific interpretation and
the final report update remain subsequent work.

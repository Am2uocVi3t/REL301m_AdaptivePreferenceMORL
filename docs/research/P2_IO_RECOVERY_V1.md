# P2 I/O recovery amendment — 2026-11-02

User explicitly requested continuing the jobs. Before dispatch, this amendment
must qualify a bounded fix for the reproduced Windows heartbeat replacement
failure. It does not reopen a completed experiment or alter the learning study.

## Fixed scope

`configs/experiments/preference_recovery_p2_io_v1.json` freezes 252 retained-file
hashes for nine completed jobs and the remaining three job identities. Resume
D seed20263212 at checksum-verified step297188; start only C/D seed20263213.
Remaining logical training is1,202,812 interactions under the original6M total;
the failed job's additional unsaved tail is separately bounded at5,812–6,811
interactions. Earlier interruption/engineering compute remains separate.
No normalization, checkpoint selection, seed, network, optimizer, loss, RNG,
evaluation matrix, scientific claim or final-test gate changes.

## Why a new execution adapter

An open reader reproduced WinError5 during `os.replace`, even with delete
sharing. Monitor now avoids rotating JSON; the coordinator and external readers
can still race a writer. `scripts/preference_recovery_io.py` delegates to the
original JSON serializer/fsync/replace and retries only PermissionError with
Windows code5/32/33. Eight attempts sleep at most1.575 seconds in total.
Permanent locks and other I/O failures propagate; no training-job auto retry.

Historical learner, recovery helper, coordinator and analyzer files remain
byte-for-byte unchanged. The worker wrapper explicitly installs the adapter
for heartbeat/progress writes and recovery-pointer publication, retaining the
original model/RNG/source binding. This runtime substitution is disclosed in
separate `io_segments` receipts, never disguised as clean original execution.
Each segment records wrapper/adapter/amendment hashes, Git provenance and retry
count. The new coordinator also records the amendment/source commit per segment.

Qualification requires four-cell original/adapted CUDA comparisons at12k steps
(96k engineering interactions), plus a held-boundary forced-kill/resume and
duplicate-job rejection for D (12k additional,108k total). Compare model, target,
optimizer, episode histories, losses and evaluation returns exactly. Actual
Windows transient-lock and persistent-lock/target-preservation witnesses must
pass. This is numerical/operational qualification, not learned task success.

## Dispatch and audit

After PASS in `research/qualification/preference_recovery_p2_io_v1.json` and a
clean source commit:

```powershell
. scripts/use_d_runtime.ps1
. scripts/start_preference_recovery_io.ps1 -ResumeExisting
```

The existing independent WMI/base-interpreter mechanism is reused, with no
service or scheduler. It rejects a live duplicate coordinator and checks
qualified source, the original qualification, frozen parent plan and all nine
retained jobs before dispatch. Failed jobs stop subsequent dispatch; all data
and caches remain D:. The native terminal recognizes both original and adapted
worker/coordinator commands; reopen it to load the updated collector.

After normal completion the original P2 numeric/provenance audit runs, followed
by the amendment audit in `scripts/analyze_preference_recovery_io.py`: retain
all nine prior results unchanged and validate the three runtime adapter receipts.
Analysis still goes to `artifacts/preference-recovery-p2-v1/analysis.json`.
The result remains provisional executor review. Full study completion does not
automatically qualify a model, trigger P3/P4, lock checkpoints or access final test.


## Executed qualification

All four old/adapted CUDA cells match exactly and D forced-kill/resume plus
active-duplicate rejection pass. Transient/persistent real Windows locks pass;
engineering training totals108k interactions, counted separately. The combined
postprocessor was then refined to capture the original numeric result in memory
and publish only the complete numeric+I/O audit once. Its updated source hash
and independent unit validation are explicitly recorded under
`postprocessor_qualification` in the qualification receipt; the learner, I/O
adapter and coordinator CUDA witness sources did not change and no extra
training was used. Required quality gate:205 passed/four existing skips.

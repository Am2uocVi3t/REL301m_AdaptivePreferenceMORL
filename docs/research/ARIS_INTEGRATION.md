# REL301m × ARIS integration

## Authority and current state

ARIS is the skill/orchestration layer, not a replacement for the executable
protocols or `research/` registries. The 22-source literature work and completed
experiments are inputs; never restart W1 or experiments just to populate ARIS.
Minecart v2 failed. On 2026-10-17 the user explicitly authorized a full ARIS
continuation beyond read-only work: create a dedicated branch and review PR,
prepare a versioned Minecart F1 scope/protocol amendment, implement the reviewed
successful-episode replay design, run its deterministic qualification, and then
execute the predeclared local training plus nominal-validation audit. This is
execution authority, not evidence that the method works. Checkpoint locking and
final-test access remain conditional on the frozen F1 all-seeds retention gate
and an independently valid source audit; final-test data still cannot select or
tune anything. The initial progress report does not move the project to Phase 5.

### Authorization record `aris-full-workflow-20261017`

- **Immediate:** scope/protocol amendment preparation, implementation, offline
  tests, same-family code review, local sanity qualification, F1 training,
  nominal validation, evidence analysis, Git commit/push, and PR creation.
- **Conditional:** F2 only after all A1R1 F1 seeds pass retention and the F1
  source audit passes; checkpoint lock/final test only after the amendment's
  explicit unlock gate passes.
- **Still bounded:** use paired seeds and matched interaction/update budgets;
  preserve raw/discounted returns and provenance; keep training and validation
  budgets separate; stop on source drift, failed qualification, low/unknown
  quota, or ambiguous process state.
- **Paid providers:** full workflow authority does not mean unmetered spending.
  Every paid review still needs a fresh finite batch record, packet hash,
  invocation count, timeout, and the existing `$1/batch`, `$0.25/call`, no
  auto-reload limits. The consumed earlier batch cannot be reused.
- **Unattended operation:** foreground autonomous work in this chat is allowed;
  scheduler/heartbeat dispatch remains off until the documented lifecycle and
  confinement gates pass.

Pinned source: `26b95cfa0d8747078e9e43b42e20952709e561b8` at
`/home/hei/.local/share/rel301m-aris-runtime` (MIT license). The 84 Codex skills,
eight Claude-review overlays and shared references are installed as copies in
`.agents/skills/`; this filesystem rejects symlinks. Existing skills were preserved.
The interrupted symlink installer wrote only an incomplete temporary manifest;
it is not evidence of successful installation. Copy content is verified against
the pinned checkout by the preflight. Never auto-update the upstream checkout.

## Team: six roles, on demand

| Role | Responsibility |
| --- | --- |
| Coordinator/state steward | Dependencies, bounded dispatch, single writer for shared state/handoff |
| Literature researcher | Legal primary full text, antecedents, citation evidence and access blockers |
| Research engineer | Implementation, invariant tests, approved runners only |
| Evidence analyst | Per-seed raw results, budgets, uncertainty and negative results |
| Paper/artifact editor | Evidence-bounded manuscript, template, visuals and local demo/video |
| Independent Claude reviewer | Artifact-grounded cross-family review, no mutation/unlocks |

Start with coordinator plus one worker when useful; never treat role count as
permission to run six processes. Runtime has four Codex slots. Same-family
consensus is provisional, never cross-family scientific acceptance. Preserve
skill reasoning floors; use actual configured models in traces, not assumed aliases.

## Workflow routing

- W1: reuse literature/claim map; legal literature updates can run routinely.
- W1.5: the F1 amendment, implementation and local execution are authorized by
  `aris-full-workflow-20261017`; the amendment must be versioned and qualified
  before its six training runs start.
- W2: independent evidence/result-to-claim review; a failed result stays failed.
- W3: draft background/methods and course report now; final paper needs evidence
  gates and a confirmed template/venue, not invented results.
- W4–W6: rebuttal/resubmission/talk only when applicable and authorized.
- Demo: the frozen-checkpoint interactive app is implemented; see the current presentation app in README.

## Preflight and resume

`configs/aris/project.json` records project policy. From repo root:

```bash
python scripts/research_harness.py doctor
python scripts/aris_preflight.py --action offline-tests --remaining-percent 34 \
  --quota-observed-at 'YYYY-MM-DDTHH:MM:SS+00:00' --write-snapshot
```

Replace `34` with the **fresh minimum remaining percentage across both usage
windows**, obtained through the app usage tool/dashboard, not a guessed value.
This script is read-only except the optional `.aris/preflight.json` snapshot;
it dispatches nothing and is not an OS sandbox or a universal CLI enforcement layer.
Missing quota, less than 10%, missing/drifted skills, or an action absent from
both the routine list and the active authorization returns exit 2. A PASS covers
bootstrap/quota/recorded-action preflight only, never research quality.
The observation timestamp must include a timezone, must not be in the future,
and expires after 300 seconds. The CLI cannot authenticate an operator snapshot.

Resolve helpers explicitly for this copy install:

```bash
ARIS_REPO=/home/hei/.local/share/rel301m-aris-runtime
python "$ARIS_REPO/tools/run_state.py" status . RUN_ID
python "$ARIS_REPO/tools/run_state.py" resume . RUN_ID
```

Record actual executor at run creation; do **not** enable `--provisional-advances`.
`done` is execution, not acceptance. Pending reviews remain open on resume.
Only a recorded deterministic mechanical check or independently traced
cross-family verdict may accept its appropriate gate. The research harness
alone owns phases/claims. Do not retroactively accept W1–W3.
The distinct user-authorized F1 execution run records implementation checks and
same-family code review separately. Its review stays provisional; local training
is authorized by the explicit F1 authority and source-bound qualification, not by
promoting that verdict to scientific acceptance. On resume, inspect live F1
execution status before interpreting the run helper's first outstanding review
obligation; never re-dispatch work already running or complete.
Use one orchestrator per run; upstream locks are best-effort, not distributed scheduling.

Before each dispatch and after each task, persist task state, artifacts/traces,
cost reservations and handoff. On quota/auth/timeout or unknown spend, stop new
dispatch and preserve state. No account rotation, blind retries or guaranteed
post-quota notification. User manually changes authentication if needed; resume
from disk after rechecking live processes so completed work is not duplicated.

## Paid bridge and unattended limits

Existing MCP bridge remains in the external sandbox at
`/home/hei/.local/share/rel301m-aris-setup`. Its policy remains disabled; installing
skills does not enable paid calls or make its sandbox the research workspace.
Approved nominal envelope: $1/defined batch, $0.25/invocation, auto-reload off.
Reservations from earlier calls must never be reset to manufacture capacity.
These are authorization limits, not guaranteed provider-side billing caps.

Before unattended enablement: persist actual cost/token/model metadata; reconcile
historical Console spend; test process-group cleanup and concurrent reservations
offline; test allowlisted review packets against path/symlink/secret leakage;
then run a defined bounded cross-family batch. Eight overlays are not full
mainline parity: unsupported semantic audits remain BLOCKED/provisional, and
full integrity-forensics may require a dedicated Claude Code session.
No scheduler is enabled by this bootstrap. Do not invoke unrestricted
`/research-pipeline` with defaults against the frozen study.

## Offline hardening v1

The versioned bridge implementation is `scripts/aris_review_guard.py`; it replaces
the external guard only after a separately approved filesystem deployment. Its
production path and Claude executable are fixed, not caller-supplied. Policy stays
disabled. Existing `reserved-calls.txt` is preserved byte-for-byte; `import_legacy`
idempotently imports each old reservation into the private SQLite ledger at its
full $0.25 reservation, with unknown actual cost and reconciliation required.
That deployment has now completed, with guard/launcher backups retained and both
installed source hashes verified. The finite audit passes 160 tests plus the full
quality gate; the installed launcher remains disabled. The external bootstrap
`test_setup.py` is historical; use the versioned tests/runner below for the new
tools-off contract.

Finite offline verification: obtain a fresh usage snapshot, run the timestamped
preflight above, then run `python scripts/audit_aris_offline.py` using the pinned
Python 3.11 environment. The report records source hashes, exact commands,
test names per gate and explicit remaining blockers in
`research/qualification/aris_offline_hardening_v1.json`. All provider responses
are synthetic; real MCP discovery/disabled calls and async restart are exercised.

The new guard stores provider `total_cost_usd`, token usage, `modelUsage`, actual
model identities and session ID before returning a review. Requested alias and
packet hash are recorded separately. Missing/non-finite metadata, provider errors,
timeouts, interruptions and budget overshoot retain reservations and block further
dispatch. Reservations use SQLite `BEGIN IMMEDIATE` and full synchronous commits;
successful calls also retain their full reserved budget. Only one active review
is allowed. SIGKILL leaves the persisted reservation unsettled, never retryable
by assumption. A pipe guardian kills the provider process group if the wrapper
dies, including outer MCP timeout killing the wrapper. Simultaneous guardian kill
or descendants escaping via `setsid` needs OS-level isolation; this gate does
not certify arbitrary untrusted executable confinement.

Review packets require explicit relative files under public artifact roots,
allowed text extensions, bounded sizes, hashes and a credential scan. Descriptor
walking rejects symlink ancestors, last-component symlinks and hardlinks.
The packet is embedded inline in a temporary empty cwd with tools disabled,
strict empty MCP configuration and session persistence disabled. Old `--resume`
is refused: use a newly reviewed packet for follow-up. The upstream async job
status remains resumable, and `done` or provisional scientific review remains
unaccepted by the upstream run-state CLI. Packet scanning is heuristic, not
proof of no secrets or an OS sandbox. The upstream stores prompts in private
local job state; select only artifacts approved for disclosure.

Production Console reconciliation remains blocked. The historical CLI estimates
are $0.0117487 and $0.2251555 (sum $0.2369042), not verified billing. A future
`console-reconciliation.json` must bind the legacy source hash, enumerate each
stable imported reservation ID with a unique historical session ID, Console
record ID and numeric `console_cost_usd`, declare source
`anthropic_console_export` and status `reconciled`, and match the explicitly
configured SHA-256. Do not create that file from the CLI estimates. Reconciliation
updates the new ledger without deleting the old file or refunding reservations.
A fresh, explicitly authorized finite batch must separately specify its ID,
call count, <=$1 batch / <=$0.25 call budgets, approved packet hash, timeout and
fresh quota observation. None is enabled by offline PASS. A bounded real
cross-family batch and OS confinement assessment remain prerequisites for any
unattended decision; no scheduler is authorized here.

The external `ARIS_WORKFLOW_AUDIT.md` records the original audit; its statement
that training was running is historical. Canonical repository state now records
the completed failed qualification. Report edits did not erase these decisions.

## One supervised batch completed; authority consumed

The user directly supplied the Console display `$0.24 spent` after providing
daily token usage, $4.77 balance and auto-reload off. The bridge now accepts this
honestly labeled user-provided aggregate evidence at cent precision, as well as
the original export format. `reconciled_aggregate` records the amount at group
level with a shared group ID, retains both historical reservations and leaves
individual actual costs null. It does not fabricate an export or split the total.
Original v1 verification remains historical; current source-bound verification
is `research/qualification/aris_single_batch_offline_v1.json` (168 tests and the
full project quality gate).

`configs/aris/batch_20261017.json` defines the only authorized supervised batch:
one tools-off review, $0.25 invocation/batch reserve, retained $0.50 historical
reservations, total $0.75 within the $1 envelope. It completed once with CLI cost
$0.0954889, model `claude-sonnet-5-5`; see
`research/qualification/aris_single_batch_result_v1.json`. The runtime paid policy
is false again. `scripts/run_aris_review_batch.py` persists dispatch intent before
calling MCP, saves the job ID, polls that same job, refuses ambiguous retries and
reopens completed state without dispatch. It never starts a scheduler.

Do not run another paid batch using the consumed authorization. A new paid batch
requires its own finite record under `aris-full-workflow-20261017`. Review receipt
acceptance in ARIS run state is limited to the independent reporting-consistency
review, not empirical claim promotion, raw-result re-audit or research unlocks.
Remaining unattended limits and conditional scientific gates still apply.

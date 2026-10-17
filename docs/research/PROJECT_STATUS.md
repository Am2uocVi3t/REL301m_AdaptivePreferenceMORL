# Project Status and Handoff

Last verified: **2026-10-18**
Current phase: **Phase 4 — paired-seed course experiment matrix (active; matrix v1 blocked; F1 replay screen completed and failed; no F2/final-test unlock)**
Publication state: **no multi-seed empirical claim established**

Cross-chat workflow: **Git-native research harness with evidence-gated Phase 0–7 roadmap**

## Research direction

F1 executed outcome (2026-10-18 local time; supersedes prelaunch wording below):
all six paired jobs completed on clean source commit `0660ecc865f3a3823f248f1f1955d70c2faf5936`.
The source audit passed six jobs and 60 checkpoints. Independent nominal-validation
re-evaluation retained 9,600 episodes / 8,654,847 environment steps and all 60
referenced validation artifact hashes were verified. A1R1 had zero positive
raw ore episodes for both objectives at all 30 checkpoints (4,800 episodes);
all three retention decisions are `never_expressed`. A0R0 had 79 positive
episodes per ore objective across its 4,800 checkpoint-evaluation episodes,
not 79 independent training runs. These are repeated fixed validation cases,
not a course allocation comparison or a causal replay decomposition.
`research/qualification/minecart_pcqn_replay_f1.json` records `failed`, with
F2, matrix v1, checkpoint locking and final test all still locked. Preserve this
negative result; no extra seeds, budget, tuning or restart is authorized to seek
a positive result. Fresh same-family experiment-integrity review returned WARN
and result-to-claim returned NO; both remain provisional. Reports are
`EXPERIMENT_AUDIT.{md,json}` and `CLAIMS_FROM_RESULTS.{md,json}`. Warnings cover
protocol-scaled raw-return naming, separate evaluation costs, missing
Mine/cargo/action-margin measurements and absent termination flags. These limit
mechanism localization, not the verified failed F1 decision. The installed
Claude review loop is blocked before dispatch by paid batch and heartbeat
lifecycle/confinement gates; no cross-family acceptance is claimed.

User hold (2026-10-18): do not update the course or conference manuscript,
TeX or PDF until the user lifts the hold. Evidence analysis, review and state
synchronization continue. Venue research is advisory; no venue or external
submission has been authorized by the discussion.

F1 implementation qualification (2026-10-17): PR #6 is open on
`codex/aris-full-workflow`, stacked on PR #5. The executable amendment is
`configs/remediations/minecart_pcqn_replay_f1.json`; implementation qualification
is recorded in `research/qualification/minecart_pcqn_replay_f1_implementation.json`.
The complete Python 3.11 gate passed 214 tests. Fresh same-family code review
passed after RNG isolation, strict prelaunch checks, retry rejection and replay
audit fixes; the verdict remains provisional. A final 1,000-interaction,
997-update completed-episode sanity under seed 9196 passed with both RNG flags.
It used zero curriculum/validation steps and produced no eligible ore episode.
Two documented compute witnesses were independently executed verbatim.

Historical prelaunch state: the six-job F1 batch was ready for bounded dispatch
after fresh quota preflight. Its completed execution source is
`artifacts/minecart-pcqn-replay-f1/execution_status.json`, with separate per-cell
logs and `.aris/runs/aris-minecart-f1-20261017.json`. Read those and check live
processes on resume; do not duplicate a running job or retry a partial attempt.
Source files must stay unchanged throughout the batch. These engineering checks
did not establish an empirical F1 result or complete the course matrix. The
completed failed F1 outcome above supersedes this prelaunch state; do not relaunch.

ARIS execution authority update (2026-10-17): the user explicitly authorized
the full foreground ARIS continuation beyond read-only analysis. The immediate
scope is a dedicated branch and stacked review PR, a versioned F1 Minecart
scope/protocol amendment, implementation and deterministic qualification of the
reviewed successful-episode replay design, followed by six paired local training
runs and nominal-validation/source audit. This does not pre-accept the method or
unlock the final test. F2 remains conditional on all A1R1 seeds passing the
retention gate and a valid F1 source audit; checkpoint lock/final-test access
remain conditional and cannot be used for tuning. Paid review still requires a
new finite batch record under the existing `$1/batch`, `$0.25/call`, no-auto-
reload envelope. Scheduler-based unattended dispatch remains disabled. The new
PR is stacked on open PR #5 to avoid duplicating its harness diff; PR #2 and #3
remain unsuitable bases because they have unresolved requested changes.

ARIS bounded continuation (2026-10-17): a fresh quota snapshot and project
preflight passed for routine `evidence-analysis` and `paper-draft` actions, with
paid dispatch and unattended execution still disabled. A resumable ARIS run
reused the existing 22-paper map and Minecart v1/v2 evidence rather than
restarting literature or research. It ranked replay, Envelope and PCN routes,
then refined the smallest route into a successful-episode-stratified,
episode-level HPR-style replay proposal. Three traced same-family review rounds
scored 6.65 (REVISE), 8.70 (REVISE), then 9.10 (READY for amendment planning).
The final verdict is explicitly provisional, not scientific acceptance or
execution authority. `idea-discovery` is persisted as provisional because the
project disables provisional phase advances; `experiment-bridge` remains
pending. The claim-driven plan proposes a six-run paired F1 screen and an
optional six-run selection-conditioned F2 decomposition, but every tracker row
was originally `BLOCKED_AUTHORITY`; that specific authority blocker is now
resolved by `aris-full-workflow-20261017`. No implementation or new training had
occurred at the time of the proposal review. Canonical
artifacts: `idea-stage/IDEA_REPORT.md`, `refine-logs/FINAL_PROPOSAL.md`,
`refine-logs/EXPERIMENT_PLAN.md`, `refine-logs/EXPERIMENT_TRACKER.md`, and
`NARRATIVE_REPORT.md`/`.html`. Run state:
`.aris/runs/aris-minecart-offline-continuation-20261017.json`.

Minecart failure investigation (2026-10-17): a bounded read-only ARIS/Codex
audit synthesized existing code, raw validation evidence, safe checkpoint
archives and five registered full-text primary-paper notes. It ran no training,
environment rollout, final test or paid review. The best-supported hypothesis is
not a broken reward path or absent exploration: successful ore trajectories
occur in every audited primary/v2 training archive, yet they do not become a
stable greedy policy. V1 showed transient acquisition followed by loss; exact
proportional one-step TD-error PER v2 was insufficient at all 30 checkpoints.
This supports, without proving causality, a combined long-horizon-credit and
preference/trajectory-alignment failure. The prioritized future proposal is a
predeclared trajectory-aware achieved-return preference-replay feasibility test;
Envelope and PCN-style backbones are larger alternatives. All require a
versioned scope amendment and supervisor approval. V3, new training, matrix
execution, checkpoint lock and final test remain prohibited. Memo:
`docs/research/MINECART_FAILURE_INVESTIGATION_20261017.md`; evidence:
`research/evidence/minecart_failure_investigation_20261017.json`.

Output organization (2026-10-17): `outputs/` now contains only the current
`REL301m_Interactive_Demo.zip`, its runnable directory and `README.md`. Existing
report/guide PDFs remain under the app's `docs/`. Superseded packages/videos and
runtime caches moved recoverably into `artifacts/presentation-archive/2026-10-17-output-cleanup/`;
verification traces/screenshots into `artifacts/presentation-verification/2026-10-17/`;
guide build input into `artifacts/presentation-build/interactive-docs/`.
Historical paths resolve through the archive's `RELOCATION.json`; all 131
inventoried file hashes were preserved. The delivered ZIP is unchanged. Current
build scripts now use the canonical report source and relocated guide; temporary
rebuild and 195-test/full quality gate passed. No permanent deletion or server
interruption. Evidence: `research/evidence/output_cleanup_20261017.json`.

Interactive-demo correction (2026-10-17, supersedes the presentation entry below):
the user explicitly rejected video/replay as the primary demo and approved a
real website with same-checkpoint reference versus slider preference. Implemented
`src/demo/`, `demo/interactive/` and `outputs/REL301m_Interactive_Demo.zip`: local
Python 3.11 backend, frozen network inference, paired reset, explicit live weight
switching, pause/step/speed, raw rewards, trace download and styled/native sprites.
No training/final-test/locking or paid dispatch. All 195 tests and quality checks
pass, 80 fake-DOM frontend assertions pass; extracted ZIP runs both environments
without repository imports. LunarLander browser interaction and artwork were
verified before Work browser control was disabled. Minecart UI, fullscreen,
mobile and Windows/macOS remain unverified; both real engines/weights passed
backend checks. Evidence: `research/qualification/interactive_model_demo_v1.json`.
This is a presentation tool, not new qualification or comparative evidence.

Presentation update (2026-10-17): the user requested native sprites instead of
the earlier text/slider-first explorer. `outputs/monday-visual/` now holds the
12-page updated report, 2-page Vietnamese guide, local video player and two
actual MO-Gymnasium checkpoint replays. The fixed LunarLander example shows
landing components -100/+100 at 50k/500k; both Minecart 100k/1M examples time out
with zero ore. These four predeclared nominal-validation episodes are presentation
only, not new comparative evidence. No training, final test, locking, paid calls
or scheduler. All 178 tests and quality checks passed; MP4s decoded and updated
PDF pages visually checked. Browser playback on the team laptop remains to be
checked. Evidence: `research/qualification/visual_policy_demo_v1.json`. The older
caption/slider package is preserved but superseded as the presentation entry.

The current defensible question is not whether preference-conditioned MORL or adaptive weight selection is new. The project asks which signal—conditioning gap, masked-ensemble disagreement, local coverage/recency, or observed learning progress—best predicts and improves future performance in weak preference regions under matched budgets.

The editable proposal v2 and executable repository now describe the same controlled empirical study. Preference generalization and environment/dynamics generalization remain separate evaluation axes.

The systematic mapping registers 22 primary/authoritative works, all with verified full-text notes. A focused 2026 refresh added five peer-reviewed works and two explicitly labeled preprints. PBMORL is direct prior art for reallocating scalarized optimization tasks from learned human utility/uncertainty, and MPFT directly targets sparse Pareto regions; CAPQL, MORL-FB, and D³PO use fixed preference sampling or conditioning rather than this repository's four-signal scheduler. The resulting verdicts remain incremental for the four individual signals and environment-shift application; exact novelty of the combined factorial study is unresolved, while broad adaptive-allocation novelty is indefensible. No empirical benefit is inferred from that mapping.

## Implemented and verified

- Fixed protocol manifests for preference generation, return semantics, environment metadata, and provenance.
- Preference-conditioned vector Q-network with per-head Double-DQN targets.
- Replay semantics for behavior preference, termination, truncation, and per-transition bootstrap masks.
- Curriculum signals for empirical conditioning gap, head disagreement, local coverage/recency, and observed learning progress.
- `rollout_only`, `update_only`, and `rollout_and_update` allocation modes.
- Uniform and compute-matched random curriculum controls.
- Safe checkpoint loading, fixed-preference evaluation, deterministic metrics, raw-result output, and dependency/Git hashes.
- Qualification-aware paired-seed execution with exact study acknowledgement, bounded selection, atomic job-level status, and completed-artifact hash verification.
- Constructor-level LunarLander shift construction; unsupported Minecart shifts fail explicitly.
- Standard-library research CLI for project health, claim status, literature metadata/BibTeX, experiment registration, append-only session closure, and generated handoff prompts.
- Versioned JSON research registries and schemas with semantic gates for completed reading, experiment artifacts, and empirically supported claims.
- Explicit literature access tracking: metadata/abstract-only papers remain screened, inaccessible full text is surfaced in the handoff, and `read` requires verified full-text evidence.
- Machine-readable Phase 0–7 roadmap with deliverables, entry/exit criteria, go/no-go rules, evidence paths, blockers, and allowed transitions.
- Claim-to-paper antecedent mapping with closest antecedent, known mechanism, project difference, bounded novelty verdict, differentiating experiment, and falsifier.
- Focused ICLR/ICML/arXiv 2026 sweep with exact queries, inclusion/exclusion criteria, seven full-text notes, and explicit separation of peer-reviewed work from preprints.
- Predeclared two-environment pilot-calibration plan, deterministic calibration proposal, provenance checks, and a dry-run/execute runner with a permanently non-freezable smoke mode.
- Uniform-PCQN rollout sampling now uses the same protocol-seeded finite candidate pool as adaptive methods; regression tests cover uniform and `update_only` behavior.
- Source-aware calibration v2 with a deterministic Minecart geometry extractor, independent fixed-pool LunarLander pilot, versioned proposal/freeze record, and frozen protocol values.
- Frozen 150-job course matrix spanning 13 PCQN arms, two qualification-gated comparator slots, two environments, and five paired seeds; generation cannot execute jobs.
- Static geometry-only preference allocation and per-objective Spearman controllability.
- Bounded Python 3.11 Envelope and GPI-LS behavioral qualification on both course environments and controlled behavioral qualification of all three enabled LunarLander shifts.
- Deterministic resumable validation-audit workflow with frozen-input, checkpoint, budget, TensorBoard-log, return-tensor, missingness, and degeneracy checks.
- Versioned Minecart failure diagnosis separating exploratory training ore events from greedy validation behavior, using no final-test or shifted data.
- Study-specific post-validation executor gate that permanently blocks additional non-smoke matrix-v1 jobs after the failed Minecart audit.
- Completed, independently audited Minecart Uniform-PCQN backbone qualification with fresh seeds, fixed hyperparameters, explicit pass/fail rules, and a failed all-seeds decision.
- Predeclared validation-only action/cargo/delivery diagnosis and single-factor prioritized-replay remediation v2.
- Exact proportional prioritized replay with maximum-priority insertion, a fixed beta schedule, pre-update vector/head TD priorities, sampled-batch-normalized importance weights, and a plan-specific weighted loss while preserving the uniform path.
- V2-aware fail-closed remediation preview/execution/audit plumbing that hash-binds predecessor evidence and verifies exact replay arguments, budgets, checkpoints, protocol, logs, and validation returns.

## Verification evidence

The remediation execution tree passed the following checks under Python 3.11.17. The current v2 implementation-qualification tree passed the complete 103-test suite, Ruff, MyPy, Bandit, compileall, and whitespace checks under Python 3.11.17; course execution remains restricted to Python 3.11.

- The complete pinned dependency set installed in a clean environment; `pip check` reported no broken requirements.
- `pytest -q`: 103 tests passed in the current tree, including analytic PER probability/priority/importance-loss tests, non-finite parameter rejection, exact Huber equivalence under unit weights, uniform-replay regressions, v2 runner/auditor drift rejection, research-harness, calibration, course-matrix/executor, behavior-diagnosis, and validation-audit coverage.
- State, claims, literature, and roadmap documents passed their Draft 2020-12 JSON Schemas.
- Ruff formatting and lint checks.
- MyPy over `src` and `scripts`.
- Bandit medium/high severity scan over `src` and `scripts`.
- Python compileall and `git diff --check`.
- MO-Lunar-Lander and Minecart reset/step smoke tests with 4- and 3-objective vector rewards, respectively.
- Envelope and GPI-LS dependency imports, including `pycddlib==2.1.6`.
- PCQN train → safe checkpoint → evaluation end to end.
- One isolated 20-step Minecart executor smoke completed, wrote a final checkpoint, and was hash-verified and skipped on a second invocation. Its ignored status explicitly records `smoke_only: true` and `course_evidence: false`.
- All 30 full-budget primary PCQN jobs completed: Uniform-PCQN, matched-random curriculum PCQN, and the full four-signal adaptive method across both environments and five paired seeds. The executor reported zero failures and all final checkpoints passed SHA-256 verification.
- The primary source audit verified the frozen study/manifest/protocol hashes, atomic execution status, all 30 final checkpoints, all 300 periodic checkpoints, 30 run manifests, TensorBoard validation curves, and budget counters. All 300 checkpoints were then re-evaluated on the nominal validation split with fixed preferences and seeds; raw and discounted vector returns, episode lengths, metrics, checkpoint hashes, and provenance are versioned in the compact aggregate.
- Validation aggregation failed closed: objectives 0 and 1 were constant zero in every episode at all ten saved checkpoints for all 15 Minecart primary runs. All 15 LunarLander runs were non-degenerate, but partial locking is prohibited. The checkpoint-lock decision therefore contains 30 diagnostic selections, zero locks, `unlocks_final_test: false`, and 15 explicit blockers. No test split or shifted environment was accessed.
- The subsequent non-test diagnosis inspected all 14,400 Minecart primary validation episodes: 13,308 (92.42%) hit the 1,000-step limit and every ore return remained zero. In contrast, all 15 diagnostically selected training checkpoints contained positive ore returns in their Pareto archives. A localization probe over one selected checkpoint per arm and all ensemble/head action modes made 345,417 validation action decisions without one `Mine` action or collected ore. This supports a common sparse delayed-credit/backbone failure, not a broken reward channel or an allocation-arm effect.
- Remediation v1 completed exactly three 1,000,000-interaction Uniform-PCQN runs and independently audited all 30 predeclared checkpoints over 4,800 nominal-validation episodes. The source audit passed, but the all-seeds decision failed: seeds `20264001` and `20264002` had 0/160 positive episodes for each ore objective at their selected checkpoints, while seed `20264003` passed with 28/160 for each objective. No test or shifted-environment data was accessed.
- Across all checkpoints, seed `20264001` never delivered ore; seed `20264002` briefly reached 3/160 and 2/160 at steps 200,000 and 800,000; seed `20264003` reached 4/160, 28/160, and 2/160 at steps 500,000, 600,000, and 900,000 before returning to zero. This supports seed-sensitive, transient acquisition/retention rather than a claim that more interactions alone solve the backbone failure.
- The predeclared v1 behavior probe then evaluated seven hash-bound checkpoints over 1,120 nominal-validation episodes. At seed `20264003`, step 600,000, 40 episodes selected `Mine`, 35 acquired cargo, and 27 delivered ore; steps 700,000 and 1,000,000 selected `Mine` zero times. Seed `20264002` showed smaller successful pockets separated by zero-delivery checkpoints. This satisfies the frozen rare-transition-retention criterion for prioritized replay; the probe accesses no test or shifted data and unlocks nothing.
- Remediation v2 was predeclared with three fresh seeds and proportional prioritized replay as the only change from v1. It fixes `alpha=0.6`, importance-sampling `beta=0.4→1.0`, epsilon `1e-6`, vector/bootstrap TD priorities and masked Huber weighting. The pre-execution amendment retained v1 loss/active-head reduction exactly. Review and seed-9192 non-evidence smoke are recorded in `research/qualification/minecart_pcqn_backbone_v2_implementation.json`.
- After explicit user authorization, all three v2 seeds completed on clean commit `25328e8`, with 1,000,000 training interactions and 995,001 updates each. Source audit passed all 30 checkpoints. Independent nominal-validation audit retained 4,800 episodes / 4,710,905 environment steps; all raw/discounted ore returns at all 30 checkpoints were zero, with 4,710 timeouts (98.125%). Selected step-1M checkpoints for seeds `20264011`, `20264012`, `20264013` each had 0/160 positive episodes and zero distinct positive values in each ore objective. `research/qualification/minecart_pcqn_backbone_v2.json` records `failed` with no unlocks. This is backbone evidence only, not a course comparison or allocation-benefit claim.
- Completed v2 runs consumed 3,000,000 training interactions, 2,985,003 updates, 6,310,626 curriculum-evaluation steps and 4,710,905 training validation steps; independent audit adds 4,710,905 evaluation steps separately. Interrupted first seed11 attempt is preserved with at least 27,044 logged training interactions and 32,000 curriculum-evaluation steps; exact unflushed expenditure unknown. Plan/source/checkpoint/log/validation hashes and counters were rechecked without rerunning training or audit.
- The pilot pipeline completed 20-step train → checkpoint → validation evaluation → calibration proposal smoke jobs for both course environments. The proposal is marked `smoke_only_not_freezable`; Minecart's untrained smoke returns correctly reported two degenerate objectives without weakening the real-pilot fail-fast rule.
- The six real v1 pilot jobs completed 600,000 training interactions, 142,506 gradient updates, and 960 validation episodes with no final-test access. MO-Lunar-Lander was non-degenerate; all 480 Minecart validation returns had exactly zero reward in both sparse ore objectives, so the calibrator failed closed and wrote no proposal.
- A post-run audit found and repaired unmatched Uniform-PCQN rollout sampling. A separate 100,000-interaction fixed-pool Minecart diagnostic retained nonzero training-archive ore returns but again produced zero ore reward in all 160 final validation episodes. The outcome and source hashes are recorded in `research/experiments/pilot-protocol-freeze.md`.
- Calibration v2 executed three independent LunarLander seeds for 300,000 interactions and 480 validation episodes. Minecart's 20-point environment reference front reproduced exactly across three declared seeds under the pinned package/config. Both sources were finite and non-degenerate, all proposed references passed strict domination, and the versioned freeze record links plan, proposal, source, and protocol hashes.
- Fresh 20-step checkpoints trained and evaluated under both frozen protocols. Exact high-dimensional hypervolume executed successfully; the resulting smoke metrics are explicitly non-comparative.
- The frozen course config and schema generated exactly 150 unique jobs with common seeds, protocol hashes, and expected final-artifact paths; embedded `execution_authorized` remains false. Separately authorized execution completed the 30-job primary block; 120 frozen ablation/comparator jobs remain.
- GPI-LS completed 200 interactions per course environment under Python 3.11.17, filled replay, crossed learning starts, and changed network parameters.
- Envelope completed the same bounded behavioral checks on both course environments; both frozen comparator slots are runtime-qualified.
- Heavy gravity, strong wind, and extreme turbulence each changed LunarLander observation, reward, and termination traces for all three controlled probe seeds. Minecart still has no enabled non-nominal shift.

These checks establish executable integration and local scientific invariants. They do not establish convergence, superiority, calibration, robustness, or publication readiness.

The Python 3.11 dependency blocker is resolved: NumPy and SciPy are pinned to the newest resolver-selected Python 3.11-compatible releases (`numpy==2.4.6`, `scipy==1.17.1`), while all other direct pins remain unchanged. Ruff and MyPy now explicitly target Python 3.11. PyTorch and TorchVision were installed from their official CPU wheel index for this CPU-only verification host; the requirements pins accept those local-version wheels.

The research CLI deliberately runs without third-party dependencies, so a fresh chat can execute `doctor` and `status` before installing the RL stack. Literature PDFs and large experiment artifacts remain outside Git; metadata, structured notes, schemas, and provenance are versioned.

## Open blockers

### ARIS integration bootstrap (2026-10-17)

On `codex/aris-integration`, installed 84 pinned Codex skills with eight Claude-review
overlays via upstream copy-install; the shared filesystem rejects symlinks.
Preserved existing skills and report changes. `docs/research/ARIS_INTEGRATION.md`
and `configs/aris/project.json` record the six on-demand roles, authority boundaries,
resume semantics and outstanding paid-bridge hardening. `scripts/aris_preflight.py`
checks copied content against the pinned checkout and canonical harness state;
it dispatches nothing and is not an OS sandbox. Unknown/low quota or authority-only
actions fail closed. Paid and unattended execution remain disabled. No new
research result, phase transition or experiment authorization follows from installation.
Bootstrap verification: 118 project tests and 29 upstream resume/audit-helper tests
passed; full Ruff/MyPy/Bandit/compileall/whitespace gate passed. CLI resume in a
temporary workspace preserved unreviewed `done` and skipped only a deterministically
accepted mechanical fixture. See `research/qualification/aris_bootstrap_v1.json`.

### ARIS offline hardening (2026-10-17)

On `codex/aris-offline-hardening`, the source-bound finite audit at
`research/qualification/aris_offline_hardening_v1.json` passed 160 tests under
Python 3.11.17, plus the complete Ruff/MyPy/Bandit/compileall/whitespace gate and
launcher syntax check. The guard and launcher were deployed to the external
setup with prior versions preserved as `*.pre-hardening-v1.*`; hashes match the
versioned sources. The installed launcher returns a disabled-review error without
dispatching Claude. Project and runtime paid policies remain false; no scheduler
was enabled, no provider request was issued and no scientific gate changed.

| Gate | Verified evidence and scope |
| --- | --- |
| Cost/model metadata | Synthetic object/array/NDJSON results persist actual CLI-reported cost, tokens, actual models and session separately from requested alias; missing metadata and overshoot stop further dispatch. |
| Timeout/process cleanup | Pipe guardian cleans the provider group on timeout, SIGTERM, SIGINT, wrapper SIGKILL, output overflow and parent exit with pipe-holding children. Escaping process groups or guardian kill remains outside this local guarantee. |
| Reservations | SQLite transactional concurrency, no budget refund on success/failure, idempotent migration and unresolved-spend blocking verified. Two historical reservations remain, $0.50 reserved; legacy bytes are unchanged. |
| Quota freshness | Unknown/low/non-finite quota, missing/naive/stale/future observation timestamps fail closed; observation lifetime is 300 seconds. Snapshot authenticity remains operator supplied. |
| Review packets | Explicit paths, content hash, bounded text, symlink/hardlink/traversal rejection, heuristic credential scan and changed-packet rejection verified. Tools-off inline review is not an OS sandbox. |
| Interruption/resume | Real pinned MCP → guard → synthetic provider → ledger → restarted MCP status passed. Separate-process upstream resume retains unreviewed `done` and same-family provisional work; completed jobs are not redispatched. |
| Console reconciliation / real paid batch | BLOCKED / NOT RUN. Historical CLI estimates total $0.2369042, with no Console export available. No paid or unattended readiness follows from offline PASS. |

Next tooling gates: obtain and hash-bind authorized historical Console records;
review a specifically defined finite cross-family batch and its packet; assess
OS isolation before any unattended proposal. Do not reset reservations or enable
paid calls merely to complete these records. The historical external
`test_setup.py` described the old Read/Grep/Glob guard; the canonical hardening
tests and runner are now in this repository. Minecart scope decision, matrix-v1,
checkpoint locking and final-test blockers remain unchanged.

### Single supervised ARIS batch authorization and blocked preflight (2026-10-17)

The user explicitly authorized one bounded end-to-end batch with independent
Claude review, nominal $1 total / $0.25 per invocation, auto-reload off, no
scheduler, and a mandatory stop on uncertain spend. This conditional authority
is recorded in `research/qualification/aris_single_batch_attempt_v1.json`; it
does not enable recurring work or change any scientific gate.

Read-only verification matched all nine prior qualification source hashes and
both installed runtime files; the existing 160-test evidence was reused, not
rerun. Fresh routine preflight passed with 66% minimum Codex quota remaining.
An on-demand same-family read-only audit found no additional mandatory offline
gate for a supervised tools-off inline-packet batch. It recorded the need for
durable task/job IDs when a batch is eventually defined: call-count enforcement
alone does not prevent re-dispatching a completed task. This provisional review
does not replace independent Claude review or establish unattended readiness.

Paid dispatch stopped before batch definition or reservation. The SQLite ledger
still contains exactly two historical $0.25 reservations, both
`console_reconciliation_required`, with actual cost null. Historical CLI
estimates sum to $0.2369042, but no Console reconciliation file exists. Browser
access to Console billing was declined by the browser permission gate; no
workaround was attempted. Actual remaining spend capacity is unknown. New paid
calls, new reservations and paid cost for this attempt are all zero. Paid
policies remain disabled; no scheduler was enabled.

Resume requires authorized redacted Console cost evidence for the two historical
sessions, preserving both ledgers. After reconciliation, reuse this attempt
state and the user's existing one-batch authorization; define and ledger the
finite batch, persist its task/job IDs before dispatch, review existing artifacts
with Claude, then stop. Do not infer a completed batch or repeat a completed job.

The user subsequently supplied the daily Console token-usage row for
2026-10-17 UTC, model `claude-sonnet-5-5`, and reported $4.77 credit balance
with auto-reload off. Evidence is saved at
`research/evidence/aris_console_usage_20261017_partial.json`; the API-key label
is omitted. Both historical ledger rows now reference that evidence. Their
IDs, $0.25 reservations, unresolved status and null actual costs are preserved,
and the legacy text ledger is byte-identical. The export contains token counts
but no Cost USD field or invocation cost mapping, so historical billed spend
remains unknown. Do not derive exact spend from a rounded balance or list-price
token calculation. No paid dispatch occurred; only Console cost evidence is
still missing from the supplied billing/usage material.

### Completed single supervised ARIS batch (2026-10-17)

The user supplied Console display **$0.24 spent**, completing aggregate historical
reconciliation at cent precision. This is user-provided Console evidence, not an
independently downloaded export. `research/evidence/aris_console_spend_20261017.json`
records the total once; individual historical costs remain null. Both original
$0.25 reservations are retained and the legacy text ledger remains byte-identical.

Exactly one finite batch, `aris-existing-evidence-20261017-one-batch`, was defined,
ledgered and executed on `codex/aris-one-batch`. One independent
`claude-sonnet-5-5` invocation reviewed four existing research artifacts with all
tools disabled. CLI cost/token/model metadata records **$0.0954889** (`costBasis:
list`, not a later Console bill), below the $0.25 invocation cap. Old and new
reservations total **$0.75** within the $1 authorization; reservations were not
refunded to create capacity. Paid policy was disabled again after the one guard
loaded its policy. No scheduler or scientific gate was enabled.

New aggregate-reconciliation and duplicate-dispatch/resume behavior passed
**168 tests** plus the full quality gate; source-bound evidence is
`research/qualification/aris_single_batch_offline_v1.json`. Live coordinator
restart recovered the same MCP job, and reopening completed state retained exactly
one ledger call. Job `ea01538f417b451d82941abad2899c0c`, session
`24b6593d-2d26-41de-b1b7-aaceb1918367`; full local prompt/response traces are under
`.aris/traces/research-review/2026-10-17_one_batch/`.

Claude found packet reporting internally consistent with caveats: source-audit
success is separate from failed learner qualification; old v1 gate wording is
historical; raw tensors/audit contents were not supplied and were not independently
re-audited. Coordinator rejected a suggestion that the negative result was absent
from the registry: `research/experiments/registry.json` already records v2 failed,
while `claims.json` correctly promotes no allocation claim. No research artifacts
or protocols were amended in response to the review. The final report and precise
scope/cost evidence are `research/reviews/aris_batch_20261017.md` and
`research/qualification/aris_single_batch_result_v1.json`.

The single-batch authority is consumed. Stop paid dispatch. Unattended remains
unready: OS isolation for group escape/guardian kill is not demonstrated and one
supervised packet review is not general workflow qualification. Research phase,
Minecart failure, matrix locks, checkpoint locks and final-test prohibition remain.

### Monday teammate-review package (2026-10-17)

Prepared a portable internal-review ZIP for the 19 October progress checkpoint:
`outputs/monday-team/REL301m_Team_Review_2026-10-19.zip`. It contains the updated
12-page English report with retained approved template/roster, a 2-page Vietnamese
brief, an offline evidence explorer, a 72-second captioned H.264 summary video,
speaker notes, supervisor questions, a team checklist, selected small JSON evidence
and editable LaTeX/BibTeX sources. It excludes credentials, private ledgers,
checkpoints, raw experiment outputs and third-party paper PDFs.

The explorer shows actual qualification counts separately from synthetic reward
vectors and all-seeds examples. It loads no model and performs no environment
rollout, training, final-test evaluation or paid call. The silent backup video is
a summary of recorded evidence, not an agent screen recording. A live trained-policy
demonstration remains future work; the supervisor should confirm whether this
evidence presentation meets the initial-demo requirement.

Verification: `research/qualification/monday_team_package_v1.json` records 173
passing tests plus the full repository quality gate, 14 offline DOM assertions,
29 manifest hashes, 17 local-link checks, ZIP byte equality, rendered inspection
of both PDFs and full video decoding. In-app file-URL browser preview was blocked;
no workaround was attempted. Desktop/mobile rendering remains explicitly unverified
and is included in the team's presentation-laptop checklist. The package is ready
for teammate review, not automatic submission or unconditional presentation approval.
No external message was sent, no new paid review occurred, and Phase 4/failed
Minecart/matrix/checkpoint/final-test gates remain unchanged.

### Before course conclusions

1. V2 failed. Stop current-scope remediation; obtain a supervisor decision on a versioned Minecart scope amendment versus reporting the blocked negative result. No v3 or additional batch is authorized.
2. Keep checkpoint locking, all unexecuted matrix-v1 jobs, and final-test evaluation blocked; matrix v1 is permanently non-resumable.
3. Retain the non-degenerate LunarLander diagnostic selections as audit evidence only; do not treat them as a completed comparison.
4. Retain raw results and report negative outcomes without converting difficulty or uncertainty into a learning-progress claim.

### Before workshop or journal submission

1. Add broader environments or MORL-Generalization tasks and an appropriate continuous-control family if broad claims are retained.
2. Compare with close allocation and preference-conditioned antecedents compatible with each action space.
3. Establish whether allocation scores predict subsequent learning progress or hypervolume improvement.
4. Check venue scope and deadlines only against current official calls.

## Next execution sequence

```text
source-aware calibration v2 and protocol freeze complete
  -> paired-seed course matrix and analysis choices frozen
  -> GPI-LS and enabled dynamics shifts qualified
  -> fail-closed course executor and isolated non-evidence smoke qualified
  -> Phase 4 active; bounded primary PCQN block complete
  -> source audit and 300-checkpoint validation re-evaluation complete
  -> Minecart degeneracy blocks primary checkpoint lock (zero locks)
  -> retain Minecart; non-test diagnosis and remediation v1 complete
  -> matrix v1 permanently blocked by post-validation execution gate
  -> remediation v1 fails all-seeds gate (2/3 selected checkpoints have zero ore)
  -> validation-only behavior diagnosis localizes loss of rare successful trajectories
  -> proportional prioritized-replay remediation v2 predeclared as a single-factor change
  -> v2 implementation qualified; user authorized three fresh seeds
  -> three 1M-interaction jobs complete; source audit passes all 30 checkpoints
  -> independent validation fails the all-seeds gate (zero ore at all checkpoints)
  -> stop current-scope remediation; preserve evidence and obtain supervisor scope decision
  -> keep v3/new study execution/checkpoint locking/final test blocked
  -> deliver initial progress report on 19 October 2026 without claiming completed comparison
```

## Cross-chat handoff

Start a fresh chat with the complete code block in `docs/research/HANDOFF_PROMPT.md`. The prompt is generated from the registries and latest append-only session entry. Always compare its Git snapshot with the live worktree; regenerate it after a substantial session with `session close --write-handoff`.

## Historical note

The submitted Vietnamese proposal PDF is retained under `docs/proposal/` as an immutable historical record. It is not evidence that a feature exists or an experiment has run.

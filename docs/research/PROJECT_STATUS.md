# Project Status and Handoff

Last verified: **2026-10-17**
Current phase: **Phase 4 — paired-seed course experiment matrix (active; matrix v1 blocked and Minecart remediation v2 implementation qualified for authorization review)**
Publication state: **no multi-seed empirical claim established**

Cross-chat workflow: **Git-native research harness with evidence-gated Phase 0–7 roadmap**

## Research direction

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
- Remediation v2 is predeclared with three fresh seeds and proportional prioritized replay as the only change from v1. It fixes `alpha=0.6`, importance-sampling `beta=0.4→1.0`, priority epsilon `1e-6`, vector/bootstrap TD-error aggregation, and importance-weighted masked Huber semantics. Before execution, a dated plan amendment corrected the original squared-TD wording so unit weights reproduce v1's loss and active-head reduction exactly. The implementation and fail-closed runner/auditor passed analytic and integration tests. A non-evidence seed-9192 smoke completed 20 interactions and all 17 expected prioritized updates with zero curriculum or validation steps. `research/qualification/minecart_pcqn_backbone_v2_implementation.json` records the review evidence. No v2 qualification seed ran, and execution remains unauthorized.
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

### Before course conclusions

1. Review the qualified v2 implementation and evidence before separately authorizing only seeds `20264011`–`20264013`.
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
  -> v2 buffer, loss, runner, and auditor qualified with analytic tests and a non-evidence smoke; zero qualification seeds executed
  -> review/authorize only the three v2 qualification seeds
  -> aggregate validation results
  -> lock checkpoints/hyperparameters
  -> run final test once
  -> write evidence-bounded conclusions
```

## Cross-chat handoff

Start a fresh chat with the complete code block in `docs/research/HANDOFF_PROMPT.md`. The prompt is generated from the registries and latest append-only session entry. Always compare its Git snapshot with the live worktree; regenerate it after a substantial session with `session close --write-handoff`.

## Historical note

The submitted Vietnamese proposal PDF is retained under `docs/proposal/` as an immutable historical record. It is not evidence that a feature exists or an experiment has run.

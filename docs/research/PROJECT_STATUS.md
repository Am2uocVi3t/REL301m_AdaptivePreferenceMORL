# Project Status and Handoff

Last verified: **2026-10-16**
Current phase: **Phase 4 — paired-seed course experiment matrix (active; primary PCQN block complete, validation audit pending)**
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

## Verification evidence

The current working tree passed the following checks on 2026-10-16 under Python 3.11.17:

- The complete pinned dependency set installed in a clean environment; `pip check` reported no broken requirements.
- `pytest -q`: 65 tests passed, including 18 research-harness tests, 11 calibration tests, course-matrix/executor safety tests, and fixed-pool control regressions.
- State, claims, literature, and roadmap documents passed their Draft 2020-12 JSON Schemas.
- Ruff formatting and lint checks.
- MyPy over `src` and `scripts`.
- Bandit medium/high severity scan over `src` and `scripts`.
- Python compileall and `git diff --check`.
- MO-Lunar-Lander and Minecart reset/step smoke tests with 4- and 3-objective vector rewards, respectively.
- Envelope and GPI-LS dependency imports, including `pycddlib==2.1.6`.
- PCQN train → safe checkpoint → evaluation end to end.
- One isolated 20-step Minecart executor smoke completed, wrote a final checkpoint, and was hash-verified and skipped on a second invocation. Its ignored status explicitly records `smoke_only: true` and `course_evidence: false`.
- All 30 full-budget primary PCQN jobs completed: Uniform-PCQN, matched-random curriculum PCQN, and the full four-signal adaptive method across both environments and five paired seeds. The executor reported zero failures and all final checkpoints passed SHA-256 verification. Validation aggregation and checkpoint locking have not yet been performed, so this establishes execution completeness only, not a comparison.
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

1. Audit and aggregate validation evidence from the completed primary block, then lock checkpoints using validation data only.
2. Run the remaining signal-only, pairwise, and allocation-target ablations plus qualified MORL baselines.
3. Retain raw results and report effect sizes, uncertainty intervals, exact paired tests, and multiplicity correction.
4. Report negative results without converting difficulty or uncertainty into a learning-progress claim.

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
  -> audit primary validation evidence and lock checkpoints
  -> execute remaining signal/target ablations and qualified baselines
  -> aggregate validation results
  -> lock checkpoints/hyperparameters
  -> run final test once
  -> write evidence-bounded conclusions
```

## Cross-chat handoff

Start a fresh chat with the complete code block in `docs/research/HANDOFF_PROMPT.md`. The prompt is generated from the registries and latest append-only session entry. Always compare its Git snapshot with the live worktree; regenerate it after a substantial session with `session close --write-handoff`.

## Historical note

The submitted Vietnamese proposal PDF is retained under `docs/proposal/` as an immutable historical record. It is not evidence that a feature exists or an experiment has run.

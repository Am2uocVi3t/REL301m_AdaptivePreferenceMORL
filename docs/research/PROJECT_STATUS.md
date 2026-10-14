# Project Status and Handoff

Last verified: **2026-10-15**
Current phase: **course pilot preparation**
Publication state: **no multi-seed empirical claim established**

Cross-chat workflow: **Git-native research harness implemented and verified**

## Research direction

The current defensible question is not whether preference-conditioned MORL or adaptive weight selection is new. The project asks which signal—conditioning gap, masked-ensemble disagreement, local coverage/recency, or observed learning progress—best predicts and improves future performance in weak preference regions under matched budgets.

The editable proposal v2 and executable repository now describe the same controlled empirical study. Preference generalization and environment/dynamics generalization remain separate evaluation axes.

## Implemented and verified

- Fixed protocol manifests for preference generation, return semantics, environment metadata, and provenance.
- Preference-conditioned vector Q-network with per-head Double-DQN targets.
- Replay semantics for behavior preference, termination, truncation, and per-transition bootstrap masks.
- Curriculum signals for empirical conditioning gap, head disagreement, local coverage/recency, and observed learning progress.
- `rollout_only`, `update_only`, and `rollout_and_update` allocation modes.
- Uniform and compute-matched random curriculum controls.
- Safe checkpoint loading, fixed-preference evaluation, deterministic metrics, raw-result output, and dependency/Git hashes.
- Paired-seed matrix generation and execution with resumable per-job status.
- Constructor-level LunarLander shift construction; unsupported Minecart shifts fail explicitly.
- Standard-library research CLI for project health, claim status, literature metadata/BibTeX, experiment registration, append-only session closure, and generated handoff prompts.
- Versioned JSON research registries and schemas with semantic gates for completed reading, experiment artifacts, and empirically supported claims.

## Verification evidence

The following passed on the current working tree on 2026-10-15:

- `pytest -q`: 32 tests passed, including 11 research-harness tests.
- Ruff formatting and lint checks.
- MyPy over `src` and `scripts`.
- Bandit medium/high severity scan over `src` and `scripts`.
- Python compileall and `git diff --check`.
- MO-Lunar-Lander and Minecart reset/step smoke tests.
- PCQN train → safe checkpoint → evaluation end to end.
- A real 20-step matrix job completed and wrote its final checkpoint and manifest status.

These checks establish executable integration and local scientific invariants. They do not establish convergence, superiority, calibration, robustness, or publication readiness.

The research CLI deliberately runs without third-party dependencies, so a fresh chat can execute `doctor` and `status` before installing the RL stack. Literature PDFs and large experiment artifacts remain outside Git; metadata, structured notes, schemas, and provenance are versioned.

## Open blockers

### Before course experiments

1. Run pilot-only trajectories to choose reward scaling and a dominated hypervolume reference point.
2. Freeze those values in a versioned protocol before final runs.
3. Validate GPI-LS in the supported Python 3.11 environment with native `libcdd-dev` available.
4. Behaviorally validate that each enabled dynamics shift changes the intended transition distribution.

### Before course conclusions

1. Run paired seeds for Uniform-PCQN, random-curriculum-PCQN, Adaptive-PCQN, and appropriate MORL baselines.
2. Run signal-only, pairwise, full-method, and allocation-target ablations.
3. Retain raw results and report effect sizes, uncertainty intervals, exact paired tests, and multiplicity correction.
4. Report negative results without converting difficulty or uncertainty into a learning-progress claim.

### Before workshop or journal submission

1. Add broader environments or MORL-Generalization tasks and an appropriate continuous-control family if broad claims are retained.
2. Compare with close allocation and preference-conditioned antecedents compatible with each action space.
3. Establish whether allocation scores predict subsequent learning progress or hypervolume improvement.
4. Check venue scope and deadlines only against current official calls.

## Next execution sequence

```text
dependency validation
  -> pilot runs
  -> freeze scale/reference point
  -> smoke the frozen protocol
  -> review paired-seed matrix manifest
  -> execute course matrix
  -> aggregate validation results
  -> lock checkpoints/hyperparameters
  -> run final test once
  -> write evidence-bounded conclusions
```

## Cross-chat handoff

Start a fresh chat with the complete code block in `docs/research/HANDOFF_PROMPT.md`. The prompt is generated from the registries and latest append-only session entry. Always compare its Git snapshot with the live worktree; regenerate it after a substantial session with `session close --write-handoff`.

## Historical note

The submitted Vietnamese proposal PDF is retained under `docs/proposal/` as an immutable historical record. It is not evidence that a feature exists or an experiment has run.

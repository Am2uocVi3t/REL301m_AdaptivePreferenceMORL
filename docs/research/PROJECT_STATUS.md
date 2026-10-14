# Project Status and Handoff

Last verified: **2026-10-15**
Current phase: **Phase 1 — claim and antecedent mapping (active)**
Publication state: **no multi-seed empirical claim established**

Cross-chat workflow: **Git-native research harness with evidence-gated Phase 0–7 roadmap**

## Research direction

The current defensible question is not whether preference-conditioned MORL or adaptive weight selection is new. The project asks which signal—conditioning gap, masked-ensemble disagreement, local coverage/recency, or observed learning progress—best predicts and improves future performance in weak preference regions under matched budgets.

The editable proposal v2 and executable repository now describe the same controlled empirical study. Preference generalization and environment/dynamics generalization remain separate evaluation axes.

The systematic mapping currently registers 15 primary/authoritative works: 14 have verified full-text notes and one (CAPQL) remains screened at abstract level because authorized full text could not be retrieved. The resulting verdicts are incremental for the four individual signals and environment-shift application; novelty of the combined rule is unresolved. No empirical benefit is inferred from that mapping.

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
- Explicit literature access tracking: metadata/abstract-only papers remain screened, inaccessible full text is surfaced in the handoff, and `read` requires verified full-text evidence.
- Machine-readable Phase 0–7 roadmap with deliverables, entry/exit criteria, go/no-go rules, evidence paths, blockers, and allowed transitions.
- Claim-to-paper antecedent mapping with closest antecedent, known mechanism, project difference, bounded novelty verdict, differentiating experiment, and falsifier.

## Verification evidence

The current roadmap/literature working tree passed the following checks on 2026-10-15:

- `pytest -q`: 39 tests passed on the available CPU host environment, including 18 research-harness tests.
- The 18 harness tests, focused Ruff checks, and focused MyPy checks also passed under Python 3.11.17.
- State, claims, literature, and roadmap documents passed their Draft 2020-12 JSON Schemas.
- Ruff formatting and lint checks.
- MyPy over `src`, `scripts`, and `tests`.
- Bandit medium/high severity scan over `src` and `scripts`.
- Python compileall and `git diff --check`.
- MO-Lunar-Lander and Minecart reset/step smoke tests.
- PCQN train → safe checkpoint → evaluation end to end.
- A real 20-step matrix job completed and wrote its final checkpoint and manifest status.

These checks establish executable integration and local scientific invariants. They do not establish convergence, superiority, calibration, robustness, or publication readiness.

The full pinned dependency set is not currently installable on the declared Python 3.11 target: `numpy==2.5.4` requires Python 3.12 or newer. The full suite therefore ran in the available Python 3.14 CPU environment, while the dependency-free harness was additionally verified on Python 3.11. This mismatch is now a P0 blocker rather than an implicit success.

The research CLI deliberately runs without third-party dependencies, so a fresh chat can execute `doctor` and `status` before installing the RL stack. Literature PDFs and large experiment artifacts remain outside Git; metadata, structured notes, schemas, and provenance are versioned.

## Open blockers

### Before course experiments

1. Obtain an uploaded or authorized CAPQL full text, or review and explicitly exclude it from the essential set, before closing Phase 1.
2. Repair and lock dependency versions that install on Python 3.11, then rerun the complete quality gate there.
3. Run pilot-only trajectories to choose reward scaling and a dominated hypervolume reference point.
4. Freeze those values in a versioned protocol before final runs.
5. Validate GPI-LS in the supported Python 3.11 environment with native `libcdd-dev` available.
6. Behaviorally validate that each enabled dynamics shift changes the intended transition distribution.

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
resolve Phase 1 full-text gate
  -> dependency validation
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

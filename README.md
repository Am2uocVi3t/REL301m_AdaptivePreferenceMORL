# Preference Allocation in Preference-Conditioned MORL

REL301m course research project, Fall 2026.

**Repository status:** course-pilot-ready, scientifically repaired prototype. Core invariants and end-to-end train/evaluate integration are tested; publication claims require completed multi-seed experiments. No result in this repository should be described as experimentally supported unless a versioned raw-result artifact is cited.

New contributors and coding agents should start with [`AGENTS.md`](AGENTS.md), then read the [current project status](docs/research/PROJECT_STATUS.md). The [documentation map](docs/README.md) identifies the authoritative document for each concern.

For work spanning multiple chats, use the [AI-assisted research workflow](docs/research/AI_RESEARCH_WORKFLOW.md), inspect the [evidence-gated roadmap](docs/research/ROADMAP.md), and copy the generated [cross-chat handoff prompt](docs/research/HANDOFF_PROMPT.md). The Git-native harness tracks phases, claims, literature metadata, experiments, blockers, and session summaries without storing paper PDFs.

## Research question

Under matched interaction, update, evaluation, and tuning budgets, which signal—conditioning gap, masked-ensemble disagreement, local coverage and recency, or observed learning progress—best predicts and improves future performance in weak preference regions?

The project studies these signals rather than claiming that preference-conditioned policies or adaptive weight selection are new. See the editable [revised protocol](docs/proposal/REL301m_Research_Project_Proposal_MORL_V2.md). The [original submitted PDF](docs/proposal/REL301m_Research_Project_Proposal_MORL_VI.pdf) is retained as an immutable record.

## Implemented versus planned

| Capability | Status |
|---|---|
| Preference-conditioned vector Q-network | Implemented; unit tested |
| Per-head Double-DQN targets | Implemented; analytic unit test |
| Behavior preference and termination-aware replay | Implemented; unit tested |
| Masked multi-head replay diversity | Implemented; calibration not yet established |
| Empirical conditioning gap | Implemented; requires curriculum rollouts |
| Local coverage, recency, and learning progress | Implemented; empirical value unvalidated |
| Fixed validation/test preference manifests | Implemented |
| Checkpoint evaluation and raw-result provenance | Implemented; end-to-end smoke tested |
| LunarLander constructor-level shifts | Implemented; all enabled shifts behaviorally qualified |
| Minecart dynamics shifts | Planned; no unsupported mutation is enabled |
| Paired-seed experiment matrix | 30 primary jobs complete; matrix v1 is blocked permanently after Minecart backbone degeneracy |
| Minecart remediation | Diagnosed and predeclared; three validation-only qualification runs are planned but not authorized/executed |
| Qualification-aware course executor | Implemented; isolated non-evidence smoke passed |
| Envelope/GPI-LS baseline runtime | Behaviorally qualified on both course environments under Python 3.11 |
| Multi-seed course results | Primary validation audit failed closed; no comparative result |
| Workshop/journal evidence | Not yet established |

## Repository layout

```text
configs/
  algo/                 algorithm defaults
  protocols/            immutable preference-generation specifications
  shifts/               verified shift construction specifications
docs/
  audit/                repeatable research-audit procedure
  proposal/             original PDF and editable proposal v2
  research/             canonical current status and handoff
  tasks/                implementation/status guides
AGENTS.md                mandatory context bootstrap for coding agents
scripts/
  research_harness.py   research state, literature, experiment, and handoff CLI
  train.py              PCQN training and curriculum ablations
  train_baseline.py     MORL-Baselines adapter
  evaluate.py           fixed-protocol checkpoint evaluation
src/
  baselines/ core/ curriculum/ envs/ evaluation/ models/ research_harness/ utils/
research/                versioned claims, literature, experiments, sessions, and schemas
tests/                   scientific invariant and metric tests
```

## Research harness

Validate and inspect the durable state before starting work:

```bash
python scripts/research_harness.py doctor
python scripts/research_harness.py status
python scripts/research_harness.py roadmap list
```

Key workflows are available under `roadmap`, `paper`, `claim`, `experiment`, and `session`. Run `python scripts/research_harness.py --help` or see the [full workflow](docs/research/AI_RESEARCH_WORKFLOW.md). End a substantial chat with `session close --write-handoff` so the next chat receives a current, copyable prompt.

For literature work, agents may search and read legally accessible full text automatically. Metadata or abstract-only access remains `screened`; the handoff identifies papers that require the user to provide an uploaded PDF or authorized full-text link.

## Installation

Use Python 3.11 in an isolated environment. Direct dependencies are pinned in `requirements.txt`; record the full resolved environment with every experiment. GPI-LS additionally needs the system `cddlib` headers to build its pinned `pycddlib` dependency.

```bash
sudo apt-get install libcdd-dev
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pytest -q
```

Box2D installation may require platform build tools. A failed dependency install is not a passed environment smoke test.

## Course workflow

### 1. Run a short end-to-end smoke experiment

```bash
python scripts/train.py \
  --env mo-lunar-lander-v3 \
  --protocol configs/protocols/course_mo_lunar_lander_v3.json \
  --algo adaptive-pcqn \
  --allocation-target rollout_and_update \
  --total-timesteps 10000 \
  --learning-starts 1000 \
  --output-dir artifacts/smoke
```

### 2. Run required controls

Use the same training and protocol seeds for:

```bash
--algo uniform-pcqn
--algo random-curriculum-pcqn
```

For the mechanism ablation, run `--allocation-target rollout_only`, `update_only`, and `rollout_and_update`. Signal-only and pairwise ablations are selected by setting the four signal weights to zero or a predeclared positive value.

Reproduce and inspect the frozen paired-seed matrix without launching it:

```bash
python scripts/build_course_matrix.py
```

The authoritative config is `configs/experiments/course_paired_matrix_v1.json`; the versioned manifest contains 150 jobs and sets `execution_authorized` to `false`. Execution requires a separate Phase 4 action after review.

Inspect the 30-job primary block through the qualification-aware executor without launching it:

```bash
python scripts/execute_course_matrix.py \
  --arm uniform \
  --arm matched-random \
  --arm full
```

Actual execution additionally requires `--execute`, the exact `--acknowledge-study-id`, at least one explicit selector, and a positive `--max-jobs`. The executor rechecks the frozen study, protocol hashes, qualification artifacts, and manifest hash before launching anything. It resumes only between complete seeded jobs: a completed artifact is skipped after its SHA-256 is verified, while failed or interrupted jobs require an explicit retry and no existing untracked final artifact.

After primary validation, non-smoke execution also requires a passed, hash-bound post-validation gate. Matrix v1's gate is blocked, so its remaining jobs cannot be resumed. The planned Minecart backbone qualification and its fail-closed continuation rule are documented in `configs/remediations/minecart_pcqn_backbone_v1.json`; it is not authorized by being present in the repository.

Audit completed primary checkpoints and reproduce their validation evidence without exposing a test-split option:

```bash
python scripts/audit_course_validation.py
```

The workflow is checkpoint-level resumable, verifies frozen inputs and training logs, and fails closed on missing, malformed, non-finite, budget-incompatible, hash-mismatched, shifted, test-split, or degenerate evidence. Its current Minecart audit is intentionally blocked; rerunning it verifies and reuses the existing ignored per-checkpoint artifacts but does not unlock final testing.

Preview the separately predeclared Minecart backbone qualification without launching it:

```bash
python scripts/run_minecart_remediation.py \
  --seed 20264001 \
  --seed 20264002 \
  --seed 20264003
```

Qualification execution requires Python 3.11, a clean committed worktree, the exact plan acknowledgement, explicit seed selection, and a positive seed cap. Adding `--audit` performs validation-only raw-return evaluation of all ten checkpoints per seed and writes a hash-bound pass/fail artifact. The runner has no final-test option and never unlocks matrix v1.

### 3. Freeze pilot-derived quantities

The course protocols now contain scales and reference points frozen by source-aware calibration v2. V1 is retained as a failed calibration because learner-derived Minecart returns were degenerate. V2 uses an independent fixed-pool validation pilot for LunarLander and the pinned environment's deterministic reference geometry for Minecart; neither source accesses final-test data.

The accepted evidence and exact hashes are recorded in `research/calibration/course_calibration_v2_freeze.json`. Reproduce the Minecart geometry after freeze without mutating the artifact:

```bash
python scripts/extract_reference_front.py \
  --plan configs/pilots/calibration_v2.json \
  --env-id minecart-v0 \
  --verify-existing
```

In a clean pre-freeze reproduction, the v2 LunarLander manifest and proposal commands are:

```bash
python scripts/run_pilot_calibration.py \
  --plan configs/pilots/calibration_v2.json \
  --output-dir artifacts/pilot-calibration-v2 \
  --execute

python scripts/calibrate_protocol.py \
  --plan configs/pilots/calibration_v2.json \
  --manifest artifacts/pilot-calibration-v2/pilot_manifest.json \
  --output research/calibration/course_calibration_v2_proposal.json
```

Do not rerun these commands to tune the frozen values. The calibrator rejects test/shifted inputs and never edits protocols; post-freeze diagnostics may qualify the learner but cannot change the calibration.

### 4. Evaluate a selected checkpoint

```bash
python scripts/evaluate.py \
  --model-path artifacts/<run>/final.pt \
  --protocol configs/protocols/course_mo_lunar_lander_v3.json \
  --split test \
  --episodes-per-preference 30 \
  --shift nominal \
  --output results/<run>_test_nominal.json
```

The test split is intended for one final evaluation after checkpoint and hyperparameter selection. Use `--split validation` during development.

## Budget contract

Each run records four separate counters:

- training environment interactions;
- gradient updates;
- curriculum diagnostic/evaluation interactions;
- validation or final-evaluation interactions.

Adaptive-PCQN must be compared with the compute-matched random curriculum as well as Uniform-PCQN. Wall-clock and peak memory remain reportable outcomes even when environment interactions are matched.

## Course and publication thresholds

- **Course-ready:** both core environments execute end to end, critical ablations and close baselines run with paired seeds, raw results are retained, and conclusions match the evidence.
- **Workshop-ready:** additional MORL-Generalization or continuous-control domains, modern mechanism baselines, and score-to-future-progress analysis.
- **Journal/main-track-ready:** broad domains and seeds, calibrated diagnostics, nonlinear utilities where claimed, and a general empirical or algorithmic insight beyond combining familiar modules.

A negative result can satisfy the course and support a paper if the protocol demonstrates why a signal prioritizes hard or uncertain regions without producing future learning progress.

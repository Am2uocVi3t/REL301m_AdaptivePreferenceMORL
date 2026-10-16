# Minecart v1 Behavior Diagnosis

## Goal

Localize why ore delivery appears transient across remediation-v1 checkpoints using validation-only behavior traces, without training or final-test access.

## Tasks

- [x] Freeze the checkpoint subset and trace fields from existing v1 evidence → Verify: the plan includes passing, transient, adjacent-loss, and never-positive checkpoints.
- [x] Add a read-only diagnostic runner with exact checkpoint/protocol hash checks → Verify: it exposes no training, shifted-environment, or test-split option.
- [x] Record action, cargo, base-return, episode-length, and ore-return summaries → Verify: unit tests cover event extraction and provenance failures.
- [ ] Execute the bounded probe under Python 3.11 → Verify: a versioned artifact accounts for every planned checkpoint and episode.
- [ ] Use the evidence to choose and predeclare one remediation-v2 mechanism → Verify: no v2 training runs are launched in this task.
- [ ] Run the repository quality gate and refresh the research handoff → Verify: all required commands pass.

## Done When

- [ ] The evidence distinguishes action-selection failure from post-mining return/retention failure strongly enough to justify a single v2 intervention.
- [ ] Matrix v1 and final test remain locked.

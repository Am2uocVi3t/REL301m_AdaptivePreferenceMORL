# Experiment Tracker

All rows are non-executable until the authority and versioned-amendment gates are
met. `BLOCKED_AUTHORITY` is not `TODO` and does not authorize dispatch.

| Run ID | Milestone | Purpose | Cell | Seed | Split | Priority | Status | Notes |
|---|---|---|---|---:|---|---|---|---|
| Q000 | M1 | deterministic contract qualification | 2x2 fixtures | — | synthetic | MUST | BLOCKED_AUTHORITY | no environment rollout |
| F1-01 | M2 | paired baseline | A0R0 | 20264021 | train+validation | MUST | BLOCKED_AUTHORITY | final test forbidden |
| F1-02 | M2 | paired full intervention | A1R1 | 20264021 | train+validation | MUST | BLOCKED_AUTHORITY | final test forbidden |
| F1-03 | M2 | paired baseline | A0R0 | 20264022 | train+validation | MUST | BLOCKED_AUTHORITY | final test forbidden |
| F1-04 | M2 | paired full intervention | A1R1 | 20264022 | train+validation | MUST | BLOCKED_AUTHORITY | final test forbidden |
| F1-05 | M2 | paired baseline | A0R0 | 20264023 | train+validation | MUST | BLOCKED_AUTHORITY | final test forbidden |
| F1-06 | M2 | paired full intervention | A1R1 | 20264023 | train+validation | MUST | BLOCKED_AUTHORITY | final test forbidden |
| AUD-1 | M3 | independent source/budget audit | F1 | — | artifacts | MUST | BLOCKED_AUTHORITY | no scientific verdict before pass |
| F2-01 | M4 | sampling-only decomposition | A1R0 | 20264021 | train+validation | CONDITIONAL | BLOCKED_AUTHORITY | only after all A1R1 retention passes |
| F2-02 | M4 | relabel-only decomposition | A0R1 | 20264021 | train+validation | CONDITIONAL | BLOCKED_AUTHORITY | selection-conditioned |
| F2-03 | M4 | sampling-only decomposition | A1R0 | 20264022 | train+validation | CONDITIONAL | BLOCKED_AUTHORITY | only after all A1R1 retention passes |
| F2-04 | M4 | relabel-only decomposition | A0R1 | 20264022 | train+validation | CONDITIONAL | BLOCKED_AUTHORITY | selection-conditioned |
| F2-05 | M4 | sampling-only decomposition | A1R0 | 20264023 | train+validation | CONDITIONAL | BLOCKED_AUTHORITY | only after all A1R1 retention passes |
| F2-06 | M4 | relabel-only decomposition | A0R1 | 20264023 | train+validation | CONDITIONAL | BLOCKED_AUTHORITY | selection-conditioned |
| AUD-2 | M5 | result-to-claim and cross-family review | all | — | artifacts | CONDITIONAL | BLOCKED_AUTHORITY | no final-test unlock implied |


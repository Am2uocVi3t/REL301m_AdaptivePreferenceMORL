# Experiment Tracker

Authority `aris-full-workflow-20261017` is recorded. Execution still follows the
ordered gates: stacked PR → versioned amendment/implementation → deterministic
qualification → F1 training → source audit. Conditional rows do not authorize
themselves.

| Run ID | Milestone | Purpose | Cell | Seed | Split | Priority | Status | Notes |
|---|---|---|---|---:|---|---|---|---|
| Q000 | M1 | deterministic contract qualification | 2x2 fixtures | — | synthetic | MUST | REVIEW_PENDING | 204 tests + 20-step non-evidence sanity pass; fresh-agent review required |
| F1-01 | M2 | paired baseline | A0R0 | 20264021 | train+validation | MUST | WAITING_Q000 | final test forbidden |
| F1-02 | M2 | paired full intervention | A1R1 | 20264021 | train+validation | MUST | WAITING_Q000 | final test forbidden |
| F1-03 | M2 | paired baseline | A0R0 | 20264022 | train+validation | MUST | WAITING_Q000 | final test forbidden |
| F1-04 | M2 | paired full intervention | A1R1 | 20264022 | train+validation | MUST | WAITING_Q000 | final test forbidden |
| F1-05 | M2 | paired baseline | A0R0 | 20264023 | train+validation | MUST | WAITING_Q000 | final test forbidden |
| F1-06 | M2 | paired full intervention | A1R1 | 20264023 | train+validation | MUST | WAITING_Q000 | final test forbidden |
| AUD-1 | M3 | independent source/budget audit | F1 | — | artifacts | MUST | WAITING_F1 | no scientific verdict before pass |
| F2-01 | M4 | sampling-only decomposition | A1R0 | 20264021 | train+validation | CONDITIONAL | CONDITIONAL_F1_PASS | only after all A1R1 retention passes |
| F2-02 | M4 | relabel-only decomposition | A0R1 | 20264021 | train+validation | CONDITIONAL | CONDITIONAL_F1_PASS | selection-conditioned |
| F2-03 | M4 | sampling-only decomposition | A1R0 | 20264022 | train+validation | CONDITIONAL | CONDITIONAL_F1_PASS | only after all A1R1 retention passes |
| F2-04 | M4 | relabel-only decomposition | A0R1 | 20264022 | train+validation | CONDITIONAL | CONDITIONAL_F1_PASS | selection-conditioned |
| F2-05 | M4 | sampling-only decomposition | A1R0 | 20264023 | train+validation | CONDITIONAL | CONDITIONAL_F1_PASS | only after all A1R1 retention passes |
| F2-06 | M4 | relabel-only decomposition | A0R1 | 20264023 | train+validation | CONDITIONAL | CONDITIONAL_F1_PASS | selection-conditioned |
| AUD-2 | M5 | result-to-claim and cross-family review | all | — | artifacts | CONDITIONAL | WAITING_EVIDENCE | no final-test unlock implied |


# Experiment Tracker

Authority `aris-full-workflow-20261017` is recorded. Execution still follows the
ordered gates: stacked PR → versioned amendment/implementation → deterministic
qualification → F1 training → source audit. Conditional rows do not authorize
themselves.

| Run ID | Milestone | Purpose | Cell | Seed | Split | Priority | Status | Notes |
|---|---|---|---|---:|---|---|---|---|
| Q000 | M1 | deterministic contract qualification | 2x2 fixtures | — | synthetic | MUST | COMPLETE | 214 tests, completed-episode sanity and same-family code-review PASS |
| F1-01 | M2 | paired baseline | A0R0 | 20264021 | train+validation | MUST | COMPLETE | 1M interactions; source audit passed; not a course comparison |
| F1-02 | M2 | paired full intervention | A1R1 | 20264021 | train+validation | MUST | COMPLETE_GATE_FAILED | never_expressed across 10 checkpoints |
| F1-03 | M2 | paired baseline | A0R0 | 20264022 | train+validation | MUST | COMPLETE | 1M interactions; source audit passed; not a course comparison |
| F1-04 | M2 | paired full intervention | A1R1 | 20264022 | train+validation | MUST | COMPLETE_GATE_FAILED | never_expressed across 10 checkpoints |
| F1-05 | M2 | paired baseline | A0R0 | 20264023 | train+validation | MUST | COMPLETE | 1M interactions; source audit passed; not a course comparison |
| F1-06 | M2 | paired full intervention | A1R1 | 20264023 | train+validation | MUST | COMPLETE_GATE_FAILED | never_expressed across 10 checkpoints |
| AUD-1 | M3 | independent source/budget audit | F1 | — | artifacts | MUST | COMPLETE | source audit PASS; retention gate FAILED |
| F2-01 | M4 | sampling-only decomposition | A1R0 | 20264021 | train+validation | CONDITIONAL | CONDITIONAL_F1_PASS | only after all A1R1 retention passes |
| F2-02 | M4 | relabel-only decomposition | A0R1 | 20264021 | train+validation | CONDITIONAL | CONDITIONAL_F1_PASS | selection-conditioned |
| F2-03 | M4 | sampling-only decomposition | A1R0 | 20264022 | train+validation | CONDITIONAL | CONDITIONAL_F1_PASS | only after all A1R1 retention passes |
| F2-04 | M4 | relabel-only decomposition | A0R1 | 20264022 | train+validation | CONDITIONAL | CONDITIONAL_F1_PASS | selection-conditioned |
| F2-05 | M4 | sampling-only decomposition | A1R0 | 20264023 | train+validation | CONDITIONAL | CONDITIONAL_F1_PASS | only after all A1R1 retention passes |
| F2-06 | M4 | relabel-only decomposition | A0R1 | 20264023 | train+validation | CONDITIONAL | CONDITIONAL_F1_PASS | selection-conditioned |
| AUD-2 | M5 | result-to-claim and cross-family review | all | — | artifacts | CONDITIONAL | PARTIAL | same-family integrity WARN and claim NO complete; Claude loop blocked before dispatch |

F1 and its nominal-validation audit completed on 2026-10-18 local time.
Source audit passed six jobs / 60 checkpoints. Qualification failed all three
A1R1 retention decisions; F2 rows remain conditional and are NOT eligible for
execution. The 9,600 validation cases are repeated fixed cases across checkpoints,
not independent training replicates. Canonical decision:
`research/qualification/minecart_pcqn_replay_f1.json`.
No final-test access, checkpoint lock, matrix-v1 restart, extra seed/budget or
tuning follows. Manuscript/TeX/PDF updates are held by user; evidence analysis
and review continue.


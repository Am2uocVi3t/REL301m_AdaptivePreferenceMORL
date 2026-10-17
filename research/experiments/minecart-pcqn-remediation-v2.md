---
experiment_id: minecart-pcqn-remediation-v2
plan: configs/remediations/minecart_pcqn_backbone_v2.json
status: failed
claim_ids: []
---

# Minecart PCQN backbone remediation v2

## Falsifiable question

Can proportional prioritized replay stabilize rare successful Minecart trajectories across three fresh Uniform-PCQN seeds while every other remediation-v1 training and evaluation choice remains fixed?

This is a backbone qualification and disclosed tuning expenditure. It is not a course comparison and cannot support an allocation-signal claim.

## Evidence selecting the intervention

Remediation v1 failed its all-seeds gate, but its validation-only behavior diagnosis localized a repeatable transition. At seed `20264003`, step 600,000 produced 40 episodes with a `Mine` action, 35 with successful cargo acquisition, and 27 with ore delivery. At step 700,000 and at the final checkpoint, all three values were zero. Seed `20264002` showed smaller positive pockets separated by zero-delivery checkpoints. The diagnosis therefore satisfied its predeclared criterion for a rare-transition retention intervention.

The authoritative evidence is `research/evidence/minecart_pcqn_backbone_v1_behavior_diagnosis.json`. It contains 1,120 nominal-validation episodes across seven hash-bound checkpoints, accesses no final-test or shifted data, and does not unlock matrix v1.

## Single-factor intervention

V2 changes only the replay strategy from uniform to proportional prioritized replay. It fixes `alpha=0.6`, linearly anneals importance-sampling `beta` from `0.4` to `1.0` over exactly 995,001 gradient updates, and uses priority epsilon `1e-6`. A transition priority is the mean absolute pre-update vector Double-DQN TD error across objectives and active bootstrap heads. Normalized importance weights multiply each transition's masked vector Huber loss before the unchanged active-head reduction.

Before any v2 seed executed, review found that the original `loss_weighting` sentence said squared TD even though v1 uses masked Huber loss. The plan now records a dated pre-execution amendment retaining Huber; with unit importance weights the v2 loss exactly equals v1. This removes the unintended loss-family change and restores the declared single-factor interpretation.

New transitions enter with the current maximum priority, or one when the buffer is empty. V2 does not add n-step targets, demonstrations, reward shaping, ore-specific sampling, or any other hyperparameter change. Training interactions, gradient updates, exploration, checkpoint cadence, fixed preference pool, and validation protocol remain identical to v1.

## Qualification gate

Only seeds `20264011`–`20264013` were authorized and executed. Each evaluates the same ten predeclared checkpoints and uses the unchanged checkpoint-selection and 5% per-objective pass rules. All three seeds must pass. The implementation and runner/auditor passed pre-execution review in `research/qualification/minecart_pcqn_backbone_v2_implementation.json`.

A pass requires a new course study ID, all 65 Minecart PCQN jobs rerun with the common backbone, and separate comparator-fairness qualification. A failure stops algorithmic remediation for the current course scope; remediation v3 or final-test access requires an explicit supervisor decision.

## Verified outcome — 17 October 2026

| Seed | Selected step | Ore 0 positive /160 | Ore 1 positive /160 | Distinct positive values, ore 0 / ore 1 | Result |
| --- | ---: | ---: | ---: | --- | --- |
| 20264011 | 1,000,000 | 0 | 0 | 0 / 0 | failed |
| 20264012 | 1,000,000 | 0 | 0 | 0 / 0 | failed |
| 20264013 | 1,000,000 | 0 | 0 | 0 / 0 | failed |

Source audit passed all 30 checkpoints. All raw and discounted ore returns were zero throughout 4,800 nominal-validation episodes at all 30 checkpoints; 4,710 episodes (98.125%) reached the time limit. This is a valid failed qualification, not a runner error or an adaptive-allocation result.

Completed runs consumed 3,000,000 training interactions, 2,985,003 gradient updates, 6,310,626 curriculum-evaluation steps and 4,710,905 training validation steps. Independent re-audit adds 4,710,905 evaluation steps. Preserved interrupted seed11 attempt: at least 27,044 recorded training interactions and 32,000 logged curriculum-evaluation steps; exact unflushed expenditure unknown. Keep these counters separate.

Source commit: `25328e8e0a8448e1f929251afc3a55c7b8a56978`; plan hash: `c28b0de87731d79af71ee5ee1c5fbbd4eab0e027b72ae3df7908fa170b1873ec`. Evidence: `research/evidence/minecart_pcqn_backbone_v2_source_audit.json`, `research/qualification/minecart_pcqn_backbone_v2.json` and linked ignored validation artifacts. Stop current-scope remediation; no v3, new study execution, checkpoint lock or final-test access is authorized.

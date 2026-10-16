---
experiment_id: minecart-pcqn-remediation-v2
plan: configs/remediations/minecart_pcqn_backbone_v2.json
status: planned
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

V2 changes only replay sampling from uniform to proportional prioritized replay. It fixes `alpha=0.6`, linearly anneals importance-sampling `beta` from `0.4` to `1.0` over exactly 995,001 gradient updates, and uses priority epsilon `1e-6`. A transition priority is the mean absolute pre-update vector Double-DQN TD error across objectives and active bootstrap heads. Normalized importance weights multiply the per-transition masked squared-TD loss.

New transitions enter with the current maximum priority, or one when the buffer is empty. V2 does not add n-step targets, demonstrations, reward shaping, ore-specific sampling, or any other hyperparameter change. Training interactions, gradient updates, exploration, checkpoint cadence, fixed preference pool, and validation protocol remain identical to v1.

## Qualification gate

Only seeds `20264011`–`20264013` may run. Each evaluates the same ten predeclared checkpoints and uses the unchanged checkpoint-selection and 5% per-objective pass rules. All three seeds must pass. The runner and auditor still need implementation and verification before execution can be considered.

A pass requires a new course study ID, all 65 Minecart PCQN jobs rerun with the common backbone, and separate comparator-fairness qualification. A failure stops algorithmic remediation for the current course scope; remediation v3 or final-test access requires an explicit supervisor decision.

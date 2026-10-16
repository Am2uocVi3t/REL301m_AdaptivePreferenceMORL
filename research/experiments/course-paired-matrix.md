# Frozen Course Matrix v1

## Scope

The frozen course study is defined by `configs/experiments/course_paired_matrix_v1.json` and rendered without execution to `research/experiments/course_paired_matrix_v1_manifest.json`. It contains 150 unique paired jobs: 13 PCQN arms and 2 gated MORL comparators across two environments and five common training seeds. The manifest sets `execution_authorized` to `false`; generating it did not run a course job.

File SHA-256 values at freeze:

- study config: `569459e5fb6cad332b820e2deee18b30128746eb795ce6834c5407996c653fd0`;
- rendered manifest: `02cab77781832b1ce909036c12d9d56e54105b72f576ea91aa199b71a099c586`;
- LunarLander protocol canonical hash: `5c8abd59ad2b73a74fc59b700dd446519f708b09f21dc3556e5f8b63846bcb48`;
- Minecart protocol canonical hash: `7f350f1e45f609420b1a9c9f91d75f5d5b8cd0db9ae1867a994b691c8dc48afc`.

## Frozen choices

- Five seeds (`20262001`–`20262005`) are paired across every arm and environment.
- Every run receives 500,000 training interactions. Training, update, curriculum-evaluation, validation, and final-evaluation budgets remain separate.
- Controls are Uniform-PCQN and compute-matched random-curriculum PCQN.
- Signal arms isolate conditioning gap, masked-head disagreement, coverage/recency, and observed learning progress.
- A static geometry-only arm scores preferences by inverse kernel density of the fixed candidate pool and never uses visit history or learner outcomes.
- Selected pairs are gap+progress, disagreement+progress, and coverage/recency+progress; the equal-weight four-signal composite is the primary treatment.
- Rollout-only and update-only variants are compared with rollout-and-update for the full composite.
- Envelope and GPI-LS slots are frozen but remain conditional on their qualification evidence. Independent scalarized DQN is excluded because no audited, artifact-compatible adapter existed before freeze.
- Checkpoints are selected on validation hypervolume, then expected utility and earlier step for exact ties. Final-test evaluation occurs once only after the selection lock.
- Analysis is at seed level and estimation-first: paired mean differences, 95% seed-bootstrap intervals, paired `dz`, descriptive exact sign-flip tests, and Holm correction within environment/metric families. With five pairs, no equivalence or absence-of-effect claim is permitted.
- Per-objective Spearman controllability is mandatory; preference and dynamics-shift generalization are analyzed separately.

## Qualification evidence

`research/qualification/gpi_ls_python311_smoke.json` records one bounded 200-interaction GPI-LS training iteration on each course environment under Python 3.11.17. Both runs crossed learning starts, filled replay, and changed network parameters. This qualifies runtime behavior only, not performance or baseline fairness.

`research/qualification/envelope_python311_smoke.json` records the same bounded behavioral checks for Envelope on both environments. `research/qualification/course_matrix_gates_v1.json` binds both comparator artifacts and the shift artifact to the frozen manifest while leaving `execution_authorized` false.

`research/qualification/dynamics_shifts_v1.json` records controlled, identical action traces for nominal dynamics and all three enabled LunarLander shifts over three seeds. Every shift changed observations, rewards, and termination traces. Minecart retains no enabled non-nominal shift.

On 2026-10-16 the rendered manifest received an operational-only revision adding each PCQN job's expected `final_artifact`; the frozen study config, commands, budgets, seeds, and analysis choices did not change. The qualification gate was rebound to the manifest hash above. The executor dry-ran the 30-job primary block and completed one isolated 20-step Minecart smoke in an ignored directory. Its status records `smoke_only: true` and `course_evidence: false`; no course job was executed.

After the evidence stack was committed as `c4a90d6`, separately authorized course execution began on 2026-10-16. The first full-budget Uniform-PCQN LunarLander job completed 500,000 interactions, produced a hash-verified final checkpoint, and was skipped correctly when the complete 30-job primary selection resumed. The remaining primary jobs then ran serially under job-level resume.

The primary selection subsequently completed all 30 jobs: three arms (`uniform`, `matched-random`, and `full`) across both environments and five paired seeds, totaling 15,000,000 training interactions. The executor exited successfully with zero failed jobs, and an independent audit matched all 30 final-checkpoint SHA-256 values to atomic status records.

The validation audit then verified the frozen inputs, atomic execution status, 30 run manifests, all 30 final checkpoints, all 300 periodic checkpoint hashes and counters, and both validation scalar curves per run. A resumable validation-only evaluator reproduced every saved checkpoint on the fixed nominal split and retained preference IDs, raw and discounted vector returns, episode lengths, metrics, budget counters, hashes, and provenance. The source audit is versioned at `research/evidence/course_primary_execution_audit_v1.json`; the compact return aggregate is `research/evidence/course_primary_validation_v1.json`.

Aggregation failed closed. Every one of the 150 Minecart checkpoint evaluations—three arms, five seeds, ten checkpoints—had exactly zero variation in ore objectives 0 and 1. All 15 LunarLander runs were non-degenerate, but partial locking was not allowed. `research/evidence/course_primary_checkpoint_lock_v1.json` therefore records `status: blocked`, 30 diagnostic selections under the frozen hypervolume → expected utility → earlier-step rule, zero checkpoint locks, and `unlocks_final_test: false`. The remaining 120 jobs were not started.

The user subsequently chose to retain Minecart in the course study rather than take the bounded-exclusion path. This scope decision does not authorize a protocol change or any additional experiment by itself. The next session must diagnose the zero-return outcome from training, pilot, and validation evidence only and predeclare a scientifically justified remediation before resuming execution; final-test access remains prohibited.

That diagnosis is now versioned at `research/evidence/minecart_validation_diagnosis_v1.json`. All 15 selected Minecart checkpoints contain positive ore outcomes in their training archives, but all 14,400 primary validation episodes returned zero ore and 13,308 reached the 1,000-step limit. A validation-only localization probe over one representative selected checkpoint per arm, using both the ensemble policy and every individual head, made 345,417 action decisions without choosing `Mine` or collecting ore. The reward channel therefore works during exploratory training, while the greedy learned policy fails the environment's delayed departure → stop → mine → return sequence. This is a common-backbone sparse-credit failure, not evidence about an allocation arm.

`configs/remediations/minecart_pcqn_backbone_v1.json` predeclares one conservative Uniform-PCQN qualification bundle on three fresh validation-only seeds. It retains the environment, reward semantics, reward scale, return definition, network, optimizer, and fixed preference sets while increasing training to 1,000,000 interactions, retaining all transitions, extending epsilon decay to 500,000 steps, and using one update opportunity per interaction after learning starts. The fixed pass rule requires both ore objectives in at least 8/160 validation episodes per selected checkpoint for every seed, with two distinct positive values per objective. Failure prohibits opportunistic alternatives; success requires a new study ID and reruns all 65 Minecart PCQN jobs.

Matrix v1 will not resume. `research/qualification/course_matrix_post_validation_gate_v1.json` and the executor now fail closed on every additional non-smoke v1 job. The remaining v1 jobs are retained as an immutable plan, not a queue to continue. No remediation qualification run or final-test evaluation has been launched.

## Interpretation boundary

The freeze and qualification artifacts establish precommitment and executable plumbing. They establish no multi-seed comparative result, convergence, superiority, robustness benefit, or publication-level empirical claim.

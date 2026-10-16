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

The primary selection subsequently completed all 30 jobs: three arms (`uniform`, `matched-random`, and `full`) across both environments and five paired seeds, totaling 15,000,000 training interactions. The executor exited successfully with zero failed jobs, and an independent audit matched all 30 final-checkpoint SHA-256 values to atomic status records. Validation aggregation, checkpoint locking, and comparative analysis have not started; 120 frozen ablation/comparator jobs remain and final-test access stays prohibited.

## Interpretation boundary

The freeze and qualification artifacts establish precommitment and executable plumbing. They establish no multi-seed comparative result, convergence, superiority, robustness benefit, or publication-level empirical claim.

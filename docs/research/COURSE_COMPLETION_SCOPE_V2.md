# Course delivery scope v2 — 1 November 2026

Authority: the user requests the group's existing LaTeX template, local training
and completion of the undergraduate report/demo, with all managed storage on D:.
This delivery scope is recorded before the new feasibility cohort completes.

## Deliverable and stopping rule

The course artifact reports the already executed 30-run, five-paired-seed
primary block, its failed Minecart qualification and separately audited
remediation outcomes. It adds the exactly three-seed, 100k-interaction-per-seed
Envelope feasibility screen in `configs/experiments/envelope_feasibility_v1.json`.
The latter is not an adaptive-allocation arm or a matched-budget comparison.
No additional primary, ablation, F1/F2, seed, training extension, final-test
episode or paid reviewer call is included in this course-delivery budget.

Completion of this **delivery** means:

1. All three new jobs finish their fixed budgets, or a documented engineering
   failure is diagnosed without substituting successful seeds. Report failures.
2. Every completed validation record retains raw/discounted vectors, preferences,
   lengths, end flags and separate cost counters, with source/protocol/model hashes.
3. The real existing inference demo remains runnable with explicitly labeled
   newly trained Uniform-PCQN replacement weights. An Envelope checkpoint is
   not silently substituted or selected by validation performance.
4. The report uses the original FPT/group LaTeX template and correct roster,
   includes problem/method/protocol/results/limitations/references, and is
   compiled and visually checked. Deliver editable sources and evidence.
5. Repository quality checks and numerical audits pass, and the delivery records
   independent-review limitations instead of asserting a missing review PASS.

A negative feasibility outcome still completes this bounded screen. A positive
one does not automatically unlock the old studies or prove allocation benefit.
The original 150-job matrix, unexecuted factorial ablations and final-test
comparison remain **incomplete**. This course artifact is a scoped empirical
failure-analysis project, not a declaration that all original proposal objectives
were achieved. Do not mark research phases 4--7 complete on this basis.

The user's known course requirement is a report, demo and full information;
the lecturer's precise rubric and deadline are unknown. Therefore artifact
delivery can be completed here, but official academic acceptance cannot be
certified. No external submission is authorized or performed.

## Scientific claims permitted

- The implemented contracts are supported by executable tests and real smokes.
- Retained primary numerical evidence can be re-audited; missing historical
  weights cannot be reverified or rerun.
- The recovered primary Minecart block is degenerate in both ore objectives.
- The Envelope screen outcome is limited to its exact learner, three seeds,
  fixed budgets and validation cases; report each seed without substitution.
- RQ1/RQ3/RQ4 remain unanswered by this delivery; RQ2 has no qualified positive
  evidence. Never convert implementation, nonzero HV or a working slider into
  a convergence, superiority or environment-generalization claim.

## Primary implementation reference

The pinned upstream Envelope example is
<https://github.com/LucasAlegre/morl-baselines/blob/v1.3.0/examples/envelope_minecart.py>.
The explicit plan records deviations (protocol gamma/scales, fixed independent
validation, offline logging). A host-index transport bridge fixes the pinned
replay buffer's CUDA-index/NumPy-SumTree incompatibility without modifying its
sampled indices or priorities. The original failed GPU smoke remains on disk.

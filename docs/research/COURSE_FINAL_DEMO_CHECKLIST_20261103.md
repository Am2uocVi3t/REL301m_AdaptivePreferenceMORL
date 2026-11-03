# Course demonstration and reproduction checklist

## Current release already verified

- Package outputs/REL301m_Course_Project_20261103 and ZIP: preserve unchanged.
- Minecart model: lowest confirmation seed20264311, final4M, actor argmax.
-20 real presentation cases, portable/source action equivalence, native renderer
  and raw reward sums passed; see onpolicy_course_demo_20261103.json.
- Actual Edge desktop/mobile controls, live preference, PDF links and no page
  errors/overflow passed; see course_onpolicy_delivery_20261103.json.
- Lunar panel is LEGACY PCQN and explicitly unqualified. The separate running
  Lunar PPO is not silently substituted or described as already successful.

## Short presentation script

1. State the question: can a single policy respond to user trade-offs, and can
   allocation signals improve it? Explain that backbone competence comes first.
2. Show Minecart at balanced[.45,.45,.1] and ore1-heavy[.8,.1,.1], resetting between
   comparisons. Both panels use the same model and initial seed.
3. Show cargo delivered and raw vector returns, then the preference input. A
   different weighted score alone is not proof of task learning.
4. Mention3 fresh confirmation seeds and10/10 per task cell. Do not say100%
   universal success, optimality or adaptive superiority.
5. If changing weights mid-episode, explain retained history; reset for a new
   paired comparison. Export one trace and show observations/actions/rewards.
6. Show the current Lunar status truthfully; only promote a new Lunar model
   after its own final checkpoint/behavior audit.
7. Finish with the evidence-backed conclusion and remaining RQ1–4 gaps.

## Before final hand-in

- Check lecturer deadline, submission format and whether the original adaptive
  comparison is mandatory; current work proceeds without assuming acceptance.
- Record exact source commit, model/plan/evidence hashes and package filename.
- Build report on D: with scripts/build_course_latex_report.ps1.
- Run scripts/audit_course_report.py; inspect the PDF and check references.
- After Lunar final audit, synchronize abstract/results/conclusion/demo labels.
- Build a new versioned ZIP, not an overwrite of the current release. Start an
  extracted copy outside repo imports and verify both PDF and model routes.
- Keep a short local demo recording/backup trace; no external upload is implied.
- Reopen START_TRAINING_MONITOR.bat for training progress; demo is inference only.
- Do not enter original final-test split or reopen failed/completed studies.

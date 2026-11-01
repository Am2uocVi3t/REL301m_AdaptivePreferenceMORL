# Course continuation — 01 November 2026

Goal: continue from the recoverable 18 October source toward an honest undergraduate report and runnable inference demo. User authorized local execution on the current Windows laptop. Later recovered commits can be compared and merged/cherry-picked without rewriting this recovery history.

- [x] Recover latest pushed source on a dedicated branch; retain main and failed Minecart evidence.
- [x] Build isolated Python 3.11 PCQN runtime on D:. Full dependency installation remains incomplete: pycddlib missing; native Box2D 2.3.8 sourced from verified conda-forge binary. Torch CPU only.
- [x] Repair native-Windows training startup and evaluator defaults/protocol binding; add consequential regression tests and LF/path portability fixes.
- [x] Run quality checks (171 passed, 4 explicit skips), fresh-agent kernel witness and two non-evidence 200-step train/checkpoint/validation witnesses. Final test and matrix-v1 remain closed.
- [x] Locate and numerically re-audit embedded primary raw tensors: 300 checkpoint records, 28,800 episodes. All original checkpoint files still missing; no model hash re-verification.
- [ ] Prepare the course report and demo from verified evidence after the new study scope and runtime qualify. The user's current request authorizes working toward the final report; earlier manuscript hold is superseded for this course deliverable, not external submission.

An evidence-bounded report draft now exists at `docs/research/COURSE_REPORT_RECOVERED_DRAFT.md`. It explicitly does not claim the full course protocol, final test or trained-policy demo is complete. New training beyond engineering smokes remains a separate scope decision rather than a restart of the failed old studies.

Done when: the report states supported conclusions and missing evidence, the demo runs on the presentation machine, and reproduction commands have been executed. No requirement that adaptive allocation must outperform controls. Deadline and official rubric remain unknown.

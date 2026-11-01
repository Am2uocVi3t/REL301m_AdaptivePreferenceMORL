# Course continuation — 01 November 2026

Goal: continue from the recoverable 18 October source toward an honest undergraduate report and runnable inference demo. User authorized local execution on the current Windows laptop. Later recovered commits can be compared and merged/cherry-picked without rewriting this recovery history.

- [x] Recover latest pushed source on a dedicated branch; retain main and failed Minecart evidence.
- [x] Build isolated Python 3.11 PCQN runtime on D:. Full dependency installation remains incomplete: pycddlib missing; native Box2D 2.3.8 sourced from verified conda-forge binary. Torch CPU only.
- [x] Repair native-Windows training startup and evaluator defaults/protocol binding; add consequential regression tests and LF/path portability fixes.
- [x] Run quality checks (171 passed, 4 explicit skips), fresh-agent kernel witness and two non-evidence 200-step train/checkpoint/validation witnesses. Final test and matrix-v1 remain closed.
- [x] Locate and numerically re-audit embedded primary raw tensors: 300 checkpoint records, 28,800 episodes. All original checkpoint files still missing; no model hash re-verification.
- [x] Deliver an evidence-bounded report, guide and working real inference demo. Two replacement models followed the separate fixed-budget presentation plan; they are not historical models or a new comparative study. All managed storage is on D:.

Current deliverable: `outputs/REL301m_Course_Recovery_20261101.zip`; launcher: `START_COURSE_DEMO.bat`. Source report and explicit review status are under `paper/course-recovery/`. The pre-revision independent numeric review returned WARN; the final semantic review failed to run because its model usage limit was reached. Do not label this a final review PASS or claim the full original scientific protocol is complete.

Done when: the report states supported conclusions and missing evidence, the demo runs on the presentation machine, and reproduction commands have been executed. No requirement that adaptive allocation must outperform controls. Deadline and official rubric remain unknown.

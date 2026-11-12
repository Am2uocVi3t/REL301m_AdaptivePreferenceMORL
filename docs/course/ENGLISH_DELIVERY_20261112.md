# English demo and PDF report — 12 November 2026

## Confirmed scope

The user requested the complete demo in English and a detailed English report
for the course/department, with real visual material. They selected **PDF plus
editable source** and clarified that the apparent video request was a dictation
error. No video or additional slide deck is produced. No training, experiment
restart, final-test access, model selection or reward/protocol changes occur.

## Outputs and sources

- Report: `outputs/english-course-report-20261112/REL301m_English_Course_Report.pdf`.
- Editable archive: the same directory, `REL301m_English_Report_Editable_Source.zip`.
- Demo: `outputs/REL301m_English_Demo_20261112/`.
- LaTeX: `paper/REL301m/main.tex`, `Chapters/Final.tex`, `Chapters/EngineeringAppendix.tex`.
- UI: `demo/interactive/index.html`, `app.js`, `guide.html`, `README_EN.md`.
- Backend localization: `src/demo/runtime.py`, `server.py`; no policy changes.
- Packaging/build/delivery: `scripts/package_english_demo.py`,
  `scripts/build_english_report.py`, `scripts/deliver_english_course.py`.
- Screenshots and browser receipt: `paper/REL301m/Figures/english-demo/`.

The report covers motivation, antecedents, equations, implemented algorithms,
experimental design, negative results, PPO results, limitations, the actual demo,
software architecture, reproducibility and evidence paths. It includes existing
recorded-data curves/heatmap, architecture diagrams, result tables and genuine
English-demo screenshots. Screenshots use fixed presentation horizons and are
explicitly not a new task-performance study. Source archives include the vector
plots needed to compile without retraining or obtaining model checkpoints.

## Scientific and deployment boundaries

The package copies the same lowest-seed Minecart confirmation actor (20264311)
and Lunar specialist pilot (20265311). Prospective Lunar n=2 results are reported
separately. Export verifies checkpoint hashes and preserves numerical config
fields; objective/action labels are translated in the same order. The original
packages remain unchanged. Runtime errors and all active controls are English.

The root Windows launcher prefers the English package and supports explicit
`REL301M_PYTHON` or the existing standalone Python 3.11 interpreter. It no longer
requires an obsolete D:-checkout bootstrap to launch from the current WSL-hosted
repository. The batch launcher uses `pushd` for UNC compatibility. A clean clone
still needs an interpreter, dependencies and pretrained artifacts.

The report auditor is strict by default. Its explicit
`--allow-text-line-endings` option reconstructs exact historical hashes by LF/CRLF
conversion only and records any such case. It never removes whitespace, edits
evidence, accepts a substantive source change or unlocks a scientific gate.
A regression test verifies rejection of changed code even with the option.
This handles the historical Windows hash for `src/curriculum/sampler.py` without
modifying that frozen training source.

## Verification

- Real Edge: English visible UI, both real environments, matched resets,
  fixed-horizon policy steps, pending/live preferences, native frames without
  extra steps, no horizontal mobile overflow and no page errors.
- Frontend fake-DOM tests: 81 assertions pass; distinct from browser evidence.
- Python suite: 235 pass, 4 skipped (3 Unix-only ARIS, 1 absent historical artifact).
- MyPy: 148 source files pass. Bandit exits 0; compileall exits 0.
- Ruff format/lint: all 190 tracked/new Python files in this submission pass;
  preexisting user-only scripts remain outside this scope.
- Report source/numeric/reference audit: 12 LaTeX inputs, 21 cited keys pass;
  this is not independent full-text/semantic acceptance.
- Initial compiled PDF: 26 pages, approximately 8,370 extracted words, no
  unresolved `??` references. Every page rendered and inspected in contact
  sheets; report/screenshots inspected at readable size as needed.

Final byte-level package/archive checks are recorded after the final build.
Receipt: `research/qualification/english_course_delivery_20261112.json` records
policy/config invariance, final report/archive hashes, browser checks and copied
desktop file hashes.
The final PDF renders identically on all 26 pages to the inspected edition.
The editable ZIP was extracted into a separate ignored directory and compiled
successfully with Tectonic, using only its included sources and vector plots.
The final root launcher was exercised on port 18770; browser verification also
checked the English HTML guide and served PDF link.

The versioned desktop handoff is
`REL301m_Final_Defense/English_Submission_20261112/`. It contains the PDF,
editable-source ZIP, complete English demo and a laptop launcher. The original
standalone demo runtime and all earlier desktop files remain unchanged.
Uncommitted user presentation assets, memory and canonical handoff are preserved
and excluded from this change. Their preexisting whole-tree lint findings are
not silently corrected or reported as passes.

Latest delivery (3 November 2026): the separately versioned
outputs/REL301m_Course_Project_20261103_LunarPPO and ZIP are verified. Both
panels now use PPO actors: Minecart lowest confirmation seed20264311 (n=3),
Lunar final4M specialist seed20265311 (n=1). Extracted-package CPU checks passed
40 real task cases with source-action/probability equivalence and exact return
accounting; 5,221 additional presentation diagnostic steps, zero training/test.
Edge desktop/mobile, controls, native renderer and PDF links passed. Report14
pages and new guide1 page inspected. Old release preserved. Repository launcher
prefers the new package and selects a free port; verified live instance8766.
Receipt: research/qualification/course_lunar_delivery_20261103.json.
Fresh dependency installation was not repeated. No automatic new training;
Lunar multi-seed stability/adaptive advantage remain unestablished. Earlier
legacy-demo and pending-delivery notes below describe historical snapshots.

Latest verified update (3 November 2026): Lunar PPO specialist COMPLETE at
4,000,000 training interactions (seed 20265311; fixed preference [.7,.1,.1,.1]).
Final trained-profile sampled and argmax both achieved 10/10 native +100
terminations inside the helipad; utilities .097226 and .080849 respectively.
Uniform secondary profile also landed 10/10 in each mode, with negative utility.
Executor audit reconciled 928 development episodes /315,564 steps and replayed
all 160 task traces exactly (67,807 additional diagnostic replay steps).
Evidence: research/evidence/lunar_onpolicy_specialist_v1.json; interpretation:
docs/research/LUNAR_PPO_RESULTS_20261103.md. This is one training seed, unlike
Minecart's three-seed confirmation; no arbitrary-preference, adaptive-allocation
or dynamics-generalization claim. No new training or final-test access.
Working report includes this outcome. Previously released 3Nov demo/ZIP still
uses the legacy Lunar model and must not be represented as this new PPO model.
New portable Lunar delivery needs separate export and execution verification.
Earlier running snapshots below are historical. Phase 4 and original locks stay.

# REL301m course project report — current group-template edition

Current content is `Chapters/Final.tex`, with generated `PrimaryTable.tex` and
`EnvelopeResults.tex`, plus `OnpolicyResults.tex`. The FPT/group styling, roster and English are retained.
From the repository root run `. scripts/build_course_latex_report.ps1`.
It requires all three new Envelope jobs to be complete and numerically audited,
generates tables/figures from real records, and compiles with Tectonic/XeLaTeX.
Compiler/cache/outputs stay on D:. The PDF is
`outputs/course-report-latex/REL301m_Course_Project_Report.pdf`.
With another distribution, use XeLaTeX/BibTeX: fontspec replaces the archived
pdflatex setup below. See `docs/GPU_COURSE_RUNTIME.md`.

Finalization outline: `FINAL_REPORT_OUTLINE.md`; statement-level evidence map:
`CLAIM_EVIDENCE_MATRIX.md`; current paths: `EVIDENCE_INDEX.md`. The build now
regenerates the confirmation figure and runs `scripts/audit_course_report.py`.
Lunar PPO remains running-only text until its final checkpoint is audited.

Current evidence: `research/evidence/minecart_onpolicy_confirmation_v1.json`,
`research/evidence/course_primary_validation_v1.json`,
`research/evidence/course_primary_execution_audit_v1.json`,
`research/qualification/minecart_pcqn_replay_f1.json`, and the newly generated
`research/evidence/envelope_feasibility_v1.json` (created after all new jobs
pass the audit). Historical model files remain missing. Full proposal
ablations/final test remain incomplete and locked. See
`docs/research/COURSE_COMPLETION_SCOPE_V2.md` and `docs/COURSE_PRESENTATION_VI.md`.

The prior report's WARN/quota ERROR do not review this LaTeX report. No final
independent semantic PASS or official academic acceptance is claimed. The old
progress chapter and qualification figures are historical; EVIDENCE_INDEX now
separates current and archived provenance explicitly.
The Windows pre-edit template backup is under
`artifacts/report-backups/2026-11-01-before-completion-v2` on D:.

---

## Archived initial progress edition (17–19 October; superseded above)

The following commands/delivery descriptions concern the old edition only.
Availability of the original Linux-host backup path below is not asserted.

Reporting checkpoint: **19 October 2026**. Evidence cutoff: **17 October 2026, after completed Minecart remediation-v2 qualification**.
This is a progress report, not a final comparative paper or a Phase 5 completion claim.

## Build and edit

Main source is `main.tex`; report content is in `Chapters/Progress.tex` and styling in `General/Preamble.tex`.
Run from this directory:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

The same directory can be opened in the Codex LaTeX editor. `main.pdf` is the generated presentation copy; build intermediates should not be committed.
The report keeps English from the supplied template. The user confirmed reuse
of the SLP roster excluding Vo Tan Phat, ordered Huynh Quoc Viet (SE194225),
Le Nguyen Gia Hung (SE194127), Ngo Hoai Nam (SE194190). Lecturer is displayed
as the user-supplied "Nam Lưu"; a longer full name has not been verified.

## Cleanup and recovery

The original folder contents, including the embedded `multi-instrument-amt/.git` repository, old PDF, music-transcription chapters, YOLO images and build caches, were moved intact to:

`/home/hei/.local/share/rel301m-paper-backups/2026-10-17-original/`

The report reuses only the three FPT branding images from the original template: cover logo, gray watermark and orange campus footer. No old data was permanently erased. Do not move the embedded unrelated repository back into the research project.
The report adds no training, protocol mutation, checkpoint lock or final-test access.

## Evidence

See `EVIDENCE_INDEX.md` for traceable claims and snapshot hashes. Negative results are retained; no supported allocation-benefit claim exists.
The Monday package includes an offline evidence explorer, explicitly synthetic
preference/gate illustrations, and a captioned backup summary video. This is not
live policy inference or a successful Minecart-control demonstration.
Run `python scripts/build_monday_package.py` from the repository root after
compiling this PDF, using the bundled artifact Python with Pillow/ReportLab,
FFmpeg and the DejaVu fonts. No research dependency changes are required.
The generated ZIP under `outputs/monday-team/` is the file
to send teammates; it does not include private billing records or API credentials.

## Restored template and visuals

The original orange identity, cover composition, FPT branding, running header/footer,
and contents page are restored. Latin Modern substitutes for the unavailable
`mlmodern` package. The user replaced the logo bitmap with a complete version;
the cover now includes that image directly without clipping or a reconstructed
university wordmark.
The bibliography is generated from `../../research/literature/library.bib`:
all 22 sources are cited in the related-work synthesis, with preprint status explicit.
Three editable vector figures live under `Figures/`: the allocation loop,
evidence progression, and selected-checkpoint qualification counts.
The counts are qualification diagnostics, not a paired v1/v2 treatment comparison.

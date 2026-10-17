# REL301m initial progress report

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

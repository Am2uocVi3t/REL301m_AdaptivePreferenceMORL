# English course report — 12 November 2026

The report is `paper/REL301m/main.tex`. Its content includes `Chapters/Final.tex`
and `Chapters/EngineeringAppendix.tex`, with the shared FPT template, bibliography,
recorded-result plots and real English-demo screenshots. No video is required.

## Editable source archive

Extract the entire archive, preserving its directories. It contains the active
LaTeX sources, bibliography, branding and screenshot assets, plus the four
already-rendered vector result plots under `outputs/course-report-latex/`.
The active report can compile without running new experiments or downloading
model checkpoints. With an existing Tectonic installation, from the extracted root:

```bash
mkdir -p output
tectonic --outdir output paper/REL301m/main.tex
```

Tectonic may download TeX packages on its first run. XeLaTeX + BibTeX is an
alternative: run from `paper/REL301m`, with the included fonts/packages available.
The root archive README is this guide; source-relative paths must be preserved.

## Full repository rebuild

In a compatible Python environment with Matplotlib/NumPy and project dependencies:

```bash
python scripts/build_english_report.py --compiler /path/to/tectonic
```

This regenerates charts from existing versioned evidence, audits report inputs
and compiles the PDF. It performs no training, checkpoint selection or final test.
For the original recorded TeX bundle, Tectonic also accepts
`-b https://data1b.fullyjustified.net/tlextras-2022.0r0.tar`.

Historical source hashes can originate in Windows CRLF checkouts. The report
auditor remains strict by default. The build explicitly permits reconstructing
exact recorded hashes through LF/CRLF conversion only and records each case in
`source-audit.json`; it never normalizes code content or changes evidence hashes.
This is a report-provenance check, not a new scientific qualification.

The previous independent-review limitations remain. The deterministic source,
numeric/reference audit and visual PDF inspection are not independent academic
or semantic acceptance. Read the report's limitations before presenting results.

# Group 2 assessed submission

Course: **FPTU-AI1906-REL301m-HK12627**. Group number: **2**.

Project title: **Hard, Uncertain, or Learnable? A Controlled Study of Preference
Allocation in Preference-Conditioned MORL**.

[Download the assessed ZIP](REL301m_Group2_Submission.zip) (**6,617,031 bytes**, below
the decimal 10,000,000-byte limit) contains:

| File | Content |
|---|---|
| `REL301m_Report.pdf` | 26-page English report; all extracted text is identical to the original English release. Raster images are optimized; text and vector content remain intact. |
| `REL301m_Slides.pdf` | 12-page English defense deck, fixed 16:9 layout. Uses the team's existing visual system with claims aligned to the verified report. |
| `REL301m_Demo.mp4` | 4:24 narrated application demonstration, 1280x720 H.264, AAC mono. Picture/audio content is retained; a light peak limiter prevents clipping introduced during mono conversion. |
| `README.txt`, `MANIFEST.json` | Reading order, source link and per-file SHA-256 hashes. |

The [original narrated 1080p MP4](../media/REL301m_Narrated_Demo.mp4) is copied
byte-for-byte from the supplied recording and linked in the root README. The
source recording in Downloads remains unchanged. The unrelated meeting recording
was not included. No generated voice, fabricated gameplay or new research run.

## Editable sources and reconstruction

- Report: [LaTeX entry point](../../../paper/REL301m/main.tex) and
  [English build guide](../../../paper/REL301m/BUILD_ENGLISH.md).
- Slides: [English content JSON](../presentation/submission-en.json),
  [browser-editable source HTML](../presentation/submission-en.html) and
  [exporter](../../../scripts/build_course_submission_slides.cjs).
- Original team slide HTML and all preexisting user edits are preserved.
- Package assembly: [standard-library ZIP builder](../../../scripts/assemble_course_submission.py).

On the prepared Windows laptop, use the existing Python 3.11 demo interpreter,
external FFmpeg 7.1, bundled Playwright 1.62.1/Edge and bundled PDF libraries.
The assessment branch is `codex/course-submission-20261112`; this branch includes
the final README and assessed artifacts while earlier PRs await review.

```bash
python -m http.server 18782 --bind 127.0.0.1
# In a second terminal, with Playwright available:
node scripts/build_course_submission_slides.cjs <repository-root> <new-output-directory>
python scripts/assemble_course_submission.py --artifacts <prepared-files-directory> --target <new-package.zip>
```

To reproduce the compact video, encode the supplied original to 720p with
FFmpeg `libx264`, preset `slow`, CRF 28, then encode the original audio at 48 kHz
mono AAC 80 kb/s with mono conversion before `alimiter=limit=0.79:level=false`.
Keep the original 1080p recording unchanged. The report's eight raster images
were converted to RGB, bounded to 1800 pixels and encoded at JPEG quality 78;
PDF page count and every page's extracted text were checked against the original.

## Verification and submission state

All 26 report pages and all 12 slide pages were rendered and visually reviewed.
Slide assets load, content-overflow checks pass, ZIP CRC/content hashes pass,
and the packaged video decodes fully with audio. Measured compressed-audio
maximum is -1.1 dBFS. These are technical checks, not a word-by-word review of
the presenter's spoken narration.

The original final-test gate remains locked. No protocol, checkpoint or
scientific-claim changes were made. Submission completion is recorded separately
only after Google Forms displays its confirmation; a prepared ZIP is not proof
of submission.

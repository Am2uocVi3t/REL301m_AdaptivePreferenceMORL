# REL301m course submission

The current submission consists of an **English inference demo** and a
**26-page English PDF report with editable LaTeX source**, alongside the source
repository and versioned experimental evidence.

The user confirmed PDF plus editable source on 12 November 2026, then requested
PDF export of the existing slides and an English demonstration video with their
own narration. The [video workspace](video/README.md) includes a local Recording
Desk and editable script. Human narration and the video submission destination
remain pending. Keep the video separate from the Form's 10 MB report+slide ZIP.

## Current deliverables

| Item | Location | Purpose |
|---|---|---|
| Delivery and verification guide | [ENGLISH_DELIVERY_20261112.md](ENGLISH_DELIVERY_20261112.md) | Current package, checks and limitations |
| Report source and build guide | [BUILD_ENGLISH.md](../../paper/REL301m/BUILD_ENGLISH.md) | Edit, compile and reconstruct the PDF |
| Report entry point | [main.tex](../../paper/REL301m/main.tex) | Active LaTeX document |
| English demo instructions | [README_EN.md](../../demo/interactive/README_EN.md) | Installation boundaries, controls and interpretation |
| Research status | [PROJECT_STATUS.md](../research/PROJECT_STATUS.md) | Evidence-bounded scientific state |
| Team explanation and glossary | [TEAM_GUIDE_EN.md](presentation/TEAM_GUIDE_EN.md) | English explanation of the project and results |

Generated report and package files remain under ignored `outputs/`; pretrained
weights are not part of a source-only clone. The current local demo package is
`outputs/REL301m_English_Demo_20261112/`. The prepared desktop delivery is
`REL301m_Final_Defense/English_Submission_20261112/`.

## Demonstration

On the prepared Windows laptop, run
[START_COURSE_DEMO.bat](../../START_COURSE_DEMO.bat) from the repository root,
then open the localhost address printed by the terminal. The default port is
8765; the launcher chooses another available port when needed.

From a complete English package with Python 3.11 dependencies installed:

```bash
python launch.py --port 8765
```

Do not open the HTML file directly: policy inference and physics require the
Python server. The two panels use the same checkpoint and initial seed.
Sliders change network inputs, not weights. Live preference changes retain
history, so reset before making a matched-initial-state comparison.

## Report contents

The report covers the research question, prior work, implemented PCQN/PPO
methods, experimental protocols, negative results, bounded PPO confirmations,
limitations, software architecture, actual demo screenshots and reproduction
instructions. The figures are derived from versioned evidence or captured from
real inference; they do not depict fabricated outcomes.

Minecart confirmation used three fresh training seeds. Lunar confirmation used
two fresh seeds, separate from the specialist pilot shown in the demo.
Adaptive-allocation superiority, arbitrary-preference competence and dynamics
robustness remain unestablished. The original final-test gate is still locked.

## Supporting and historical material

[Presentation resources](presentation/README.md) provide English project
explanations and point to retained team drafts. They do not certify a new slide
export. [Milestones](milestones/) contain earlier progress reports and scope
decisions; dated instructions may refer to older models or runtime paths.

Use the current delivery guide and root README for hand-in instructions.
Retained Vietnamese originals are identified in the
[language coverage note](../ENGLISH_DOCUMENTATION.md).

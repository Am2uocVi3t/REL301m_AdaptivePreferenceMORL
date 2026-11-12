# Runtime, reproduction and demo boundaries

## Supported research runtime

The project targets Python 3.11 (`.python-version`, `pyproject.toml`). Use the
direct pins in `requirements.txt` inside a dedicated Linux/WSL environment.
Record the full resolved environment with each research run: direct pins alone
do not lock transitive dependencies, system libraries or GPU wheels.
There is no separate application build step. The demo serves static
HTML/CSS/JavaScript alongside its Python inference API.

On 12 November 2026 this checkout was inspected in WSL Ubuntu-24.04 at
`/home/heiisme/projects/Research/REL301m_AdaptivePreferenceMORL`.
Only Python 3.12 was found in the inspected Linux system/baseline environments;
no project Python 3.11 environment was present. A fresh full Linux installation
was not validated in this preparation. Do not substitute Reseto environments
or infer compatibility from their Torch versions.

The existing standalone Windows demo interpreter is
`C:/REL301m_Demo/.venv/Scripts/python.exe` (3.11.18). It provides inference
dependencies, not the full research stack. This is an explicit portable-runtime
verification path, separate from the intended WSL research environment.
Historical Windows setup is in [WINDOWS_RECOVERY.md](WINDOWS_RECOVERY.md);
paths referring to an earlier checkout must be rechecked before use.

## Commands and limits

Run the standard-library research harness from the repository root:

```bash
python scripts/research_harness.py doctor
python scripts/research_harness.py status
python scripts/research_harness.py roadmap list
```

These inspections do not launch experiments. They can use the available Python
3.12 for registry inspection; training/demo remain Python 3.11 targets.
The [root README](../README.md) provides installation, checks and a PCQN smoke
command. A smoke generates engineering artifacts, not course evidence.

| Task | Entry point | Boundary |
|---|---|---|
| PCQN training | `scripts/train.py` | Separate engineering output from registered experiments |
| Checkpoint evaluation | `scripts/evaluate.py` | Validation only; final-test remains blocked |
| Minecart PPO | `scripts/run_minecart_onpolicy.py` | Frozen plan, source binding, explicit execution acknowledgement |
| Lunar PPO | `scripts/run_lunar_onpolicy.py` | Separate frozen Lunar plan and qualification |
| Original paired matrix | `scripts/execute_course_matrix.py` | Failed qualification blocks continuation |
| Research state | `scripts/research_harness.py` | No automatic scientific gate changes |

Read each CLI's `--help` and corresponding plan under `configs/` before use.
Completed studies must not be restarted to fill missing local checkpoints.
Keep training, updates, curriculum, development and final-evaluation budgets
distinct. Preserve negative results and immutable evidence.

## Fresh clone versus pretrained demo

Git contains source, tests, direct dependency pins, protocols, versioned JSON
evidence, documentation and manuscript sources. Trained weights, environments,
runtime caches and delivery ZIPs are ignored. Some recorded SHA-256 paths refer
to artifacts absent from a fresh clone; source/provenance audits may need the
original artifact store even when raw episode records are versioned.

The Windows root launcher now prefers `outputs/REL301m_English_Demo_20261112/`.
It uses `REL301M_PYTHON` when set, otherwise the checkout's Windows virtual
environment or the existing `C:/REL301m_Demo/.venv/Scripts/python.exe` fallback.
It checks that the interpreter exists; a fresh clone still needs a compatible
runtime and pretrained artifacts. Alternatively, explicitly select a Python
3.11 interpreter and run the package's `launch.py` from its directory.

The current English package contains the same two PPO actors as the preserved
reference-review package. Minecart
uses lowest confirmation seed `20264311`, not best score. Lunar uses specialist
pilot `20265311`; prospective confirmation seeds are reported separately.
Sliders change network inputs, not weights. Older templates/packages have
different policies and caveats; do not mix configs and checkpoints.

No public checkpoint/download release was verified during this preparation.
Providing one requires selecting and publishing a bounded, audited artifact;
large weights should not enter Git to make the tree look complete.

## Confirmed hand-in and remaining work

- English PDF and editable LaTeX source are confirmed and prepared. See
  [the delivery guide](course/ENGLISH_DELIVERY_20261112.md).
- The English inference demo is prepared locally. A public pretrained download
  and clean full dependency installation remain unverified.
- No video is required; the apparent request was a dictation error.
- Additional slides, new training and final-test execution are outside this edition.

Existing presentation sources are retained. The English report was compiled
and visually checked; its editable archive was extracted and rebuilt. No slide
export, video, research training or final-test execution was performed.

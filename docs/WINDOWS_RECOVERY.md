# Windows recovery runtime — 1 November 2026

Run commands from the repository root in PowerShell. Python is isolated at
`.venv/Scripts/python.exe` (3.11.18); it does not replace system Python.
First dot-source `scripts/use_d_runtime.ps1` in each new PowerShell session so
temporary files, caches, downloads and managed runtimes stay on D:.
Downloads, Python installation, native archives and cache live on D: under
`artifacts/runtime/`. This is a **PCQN recovery runtime**, not a complete
MORL-baselines environment: `pycddlib==2.1.6` is still absent. GPI-LS remains
unqualified on this machine. Paid/Unix ARIS supervision is not supported here.

All installed direct project dependencies retain the versions in
`requirements.txt`. Box2D 2.3.8 uses the Python 3.11 Windows binary from
conda-forge, avoiding an unavailable MSVC build. Its source URL/SHA256 are in
`artifacts/runtime/box2d-native-source.json`. The package was SHA256-verified
before extracting only regular files under `Lib/site-packages/` into the venv.
Resolved installation input is `artifacts/runtime/windows-core-requirements.txt`;
it excludes pycddlib and the source Box2D build. Original requirements are unchanged.
The declarative spec is `configs/runtime/windows_recovery_python311.json`.

The RTX 3050 is detected by the driver, but the installed Torch wheel is CPU-only.
The commands below intentionally use CPU. Do not infer CUDA qualification from
the GPU's presence. Limit BLAS/OpenMP to four threads for bounded witnesses.

## Seeded kernel witness

Run this invocation verbatim from the repository root:

```powershell
.venv/Scripts/python.exe -c "import torch; from src.models.q_network import VectorQNetwork; torch.set_num_threads(4); torch.manual_seed(991); net=VectorQNetwork(8,4,4); out=net(torch.randn(2,8),torch.full((2,4),0.25)); out.square().mean().backward(); assert out.shape==(3,2,4,4); assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in net.parameters()); print('KERNEL_WITNESS shape=(3,2,4,4) grad_finite=True device=cpu')"
```

This verifies actual forward/backward execution, not learning or convergence.

## Tests and historical validation re-audit

```powershell
$env:OMP_NUM_THREADS='4'
$env:MKL_NUM_THREADS='4'
$env:SDL_VIDEODRIVER='dummy'
$env:SDL_AUDIODRIVER='dummy'
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe scripts/reaudit_recovered_validation.py
```

Unix ARIS modules skip on Windows, and the historical-checkpoint integration
test skips when its original ignored files are absent. The embedded-tensor
re-audit independently recomputes metrics for 300 historical validation records;
it neither loads missing checkpoints nor runs environments or final test.
It reports missing checkpoint files explicitly and does not unlock scientific gates.

Ruff, Bandit and compileall use the standard commands from AGENTS. MyPy defaults
to the Linux deployment target because ARIS uses fork/flock; additionally check
the portable training/evaluator path with:

```powershell
.venv/Scripts/python.exe -m mypy --platform win32 src/utils/resources.py scripts/train.py scripts/evaluate.py
```

## Completed engineering runs

`artifacts/recovery-smoke-20261101/` contains two separate 200-interaction adaptive
PCQN witnesses, with 43 optimizer updates each, safe final checkpoints and fresh
validation JSON. LunarLander uses the committed smoke protocol; Minecart uses
`artifacts/runtime/smoke_minecart_v0.json`, an explicitly non-reporting small pool.
These weights are **engineering smoke artifacts**, not recovered trained policies
or empirical support for the method. Keep them separate from the course results.

`scripts/evaluate.py` now defaults to validation, verifies checkpoint protocol/hash
and environment, and preserves the checkpoint's evaluation-RNG choice. Final test
is deliberately disabled until a separately qualified study supplies a final-test
workflow. Existing matrix-v1 and F1 decisions are unchanged.

## Git continuation

The completed course delivery is `outputs/REL301m_Course_Recovery_20261101.zip`.
Use `START_COURSE_DEMO.bat` at the repository root for the current laptop.
The ZIP includes a D-only installer, verified exact-version native Box2D wheel,
two new fixed-budget 100,000-step Uniform-PCQN replacement models, a six-page
report and two-page guide. These models are for presentation only, not historical
weights or a new allocation comparison. The extracted ZIP installed 19 compatible
demo dependencies and ran both environments independently on Windows. Real Edge
checks covered matching resets, pause/step, live weights, native render, PDF links
and a 390-pixel viewport. The full research-baseline environment still lacks cdd.

The prior zero-context numeric review returned WARN for the pre-revision paper;
the final semantic re-review failed because the reviewer usage limit was reached.
See `paper/course-recovery/PAPER_CLAIM_AUDIT.json`. Neither status is a final PASS.

The current branch descends from all 26 pushed research commits after main.
Do not recreate those changes by copying files into main. If a later laptop
commit is recovered, first preserve it on a recovery branch, compare its changes,
then merge or cherry-pick the required commits onto this continuation branch.
Nothing has been pushed or merged into main during this recovery session.

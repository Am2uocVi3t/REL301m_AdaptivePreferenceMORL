# Interactive frozen-model demo

User approved on 2026-10-17: real local website, not video. Same already-trained
checkpoint on both sides; left uses a fixed default preference, right uses simplex
sliders. Reset with the same seed for matched starts. Explicit optional live-mode
changes affect only subsequent right-side decisions; history caveat stays visible.

## Fixed implementation scope

- LunarLander: existing adaptive-PCQN seed20262001 checkpoint500000.
- Minecart: existing PER Uniform-PCQN v2 seed20264011 checkpoint1000000.
- Baseline is a preference reference, not a separately trained algorithm.
- Default weights are the existing validation preference nearest the simplex centre.
- Inference only, ensemble-mean greedy action, immutable network, nominal engine.
- Live state/action/reward telemetry, pause, reset, single step, speed, fullscreen.
- Cosmetic canvas sprites from real engine coordinates, original render toggle.
- Read-only checkpoint weights packaged without optimizer/replay/training machinery.
- Local-only backend with bounded payloads, exact asset allowlist and idempotent
  tick IDs. No arbitrary model paths, test split, upload, training or provider API.
- ZIP contains backend, website, frozen inference weights, fixed configuration,
  start/install instructions, pinned runtime requirements and two PDF documents.

## Verification targets

Prove same-weight/same-seed traces match; changed preference reaches real network;
live switching keeps state/counters; pause makes no steps; repeated tick IDs do
not duplicate inference; reset invalidates stale commands; invalid weights fail;
hashes and model parameters unchanged; terminal freeze; styled rendering is
read-only; native engine and HTTP integration work for both environments.

No new research claim, new training, final-test use, checkpoint lock, paid review,
scheduler, commit/push or submission. User interactions are presentation-only,
not additions to frozen qualification evidence. Manual laptop playback/UI checks
must be explicit if browser access is unavailable.

## Completed verification

- Real frozen models equal original source tensors, parameters remain unchanged.
- Matched default/seed first eight steps agree for both environments; live switch
  reaches next inference without resetting state. Full terminal traces retain
  raw and discounted-scaled return provenance. Minecart remains zero ore.
- 195 Python tests, full Ruff/MyPy/Bandit/compileall/whitespace gate; 80 fake-DOM
  frontend assertions; no Node build/dependency required for user runtime.
- Extracted ZIP launches with Python 3.11 in a temporary folder without repo
  import paths; real HTTP reset/inference for both environments passes.
- LunarLander browser single-step, pending/live sliders, matched reset, pause,
  styled/native rendering and error logs were inspected. Screenshot retained.
- Browser control then became disabled in Work settings. Minecart UI, fullscreen,
  mobile layout and final guard refinements remain unverified in browser; no
  alternate browser automation was used. Fresh install/other OS remain untested.
- Delivery: `outputs/REL301m_Interactive_Demo.zip`, `README_VI.md` and two PDFs.
  Qualification: `research/qualification/interactive_model_demo_v1.json`.
  No research claim, paid ledger, protocol or phase changed.

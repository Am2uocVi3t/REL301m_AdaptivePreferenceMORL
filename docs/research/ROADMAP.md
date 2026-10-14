# Evidence-Gated Research Roadmap

The machine-readable source is `research/roadmap.json`; this document explains how to use it. Phase completion is an evidence claim. The harness requires exactly one active phase, verifies phase/blocker references, and rejects a completed phase without existing evidence paths.

## Phase sequence

| Phase | Purpose | Gate to advance |
|---|---|---|
| 0 — Foundation and scientific repair | Make the intended study executable and distinguish code validation from empirical evidence. | Architecture, protocol, harness, and invariant tests are versioned. |
| 1 — Claim and antecedent mapping | Map each claim to primary-source antecedents and bound novelty. | Essential sources are read or explicitly blocked; each claim has a falsifier and verdict. |
| 2 — Pilot calibration and protocol freeze | Choose analysis-sensitive quantities using pilot evidence only. | Normalization, hypervolume reference points, budgets, seeds, checkpoints, and analysis are frozen without final-test feedback. |
| 3 — Mechanism diagnostics | Establish that signals are measurable, baselines execute, and shifts alter intended dynamics. | Predictive diagnostics, baseline/runtime, and behavioral shift tests pass or limitations are predeclared. |
| 4 — Paired-seed course experiment matrix | Run paired controls and signal/target ablations. | The frozen matrix completes with raw vector returns, provenance, uncertainty, and negative results retained. |
| 5 — Course paper | Produce an evidence-bounded manuscript and reproducible package. | Every claim links to executed evidence and reproduction instructions are tested. |
| 6 — Workshop and journal extension | Add external validity and mechanism evidence, not only more runs. | Broader domains/seeds and predictive or causal signal tests support an audited contribution. |
| 7 — Submission and artifact freeze | Submit and preserve the exact artifact. | Venue, licensing, privacy, provenance, and reproducibility requirements pass. |

## Current gate

Phase 1 is active. The roadmap contract, literature registry, and antecedent map are complete. CAPQL remains `screened` because the legal full text could not be retrieved from OpenReview or an alternative authorized source. Phase 2 is therefore a no-go until that essential gap is resolved or explicitly excluded after review.

A separate P0 execution blocker was found during verification: the pinned NumPy version requires Python 3.12+, conflicting with the declared Python 3.11 runtime. It must be repaired and fully verified before pilot execution.

## Operating rules

- Inspect the live state with `python scripts/research_harness.py roadmap list` and `status`.
- Change phase/deliverable status only when the registered evidence exists.
- Keep future phase evidence empty until it is generated; planned work is not evidence.
- Preserve separate gates for pilot calibration, training/update budgets, final evaluation, and publication claims.
- Update both the JSON roadmap and this explanation when phase logic changes.

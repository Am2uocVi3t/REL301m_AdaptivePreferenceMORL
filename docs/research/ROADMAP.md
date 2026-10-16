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

Phases 0–3 are complete and Phase 4 is active. Calibration v1 failed closed on sparse Minecart returns and exposed an unmatched uniform-sampling bug, which was repaired. Source-aware calibration v2 then froze both course protocols from non-test evidence. The course matrix subsequently froze 150 planned jobs across two environments, five paired seeds, 13 PCQN arms, and two gated comparators, along with checkpoint and estimation-first analysis rules. Its manifest explicitly forbids execution.

Envelope and GPI-LS behavior passed bounded Python 3.11 training smokes on both course environments. All three enabled LunarLander dynamics shifts changed controlled transition/reward traces over three seeds; Minecart retains no enabled non-nominal shift. These artifacts qualified plumbing and allowed Phase 4 to begin. The 30-job primary PCQN block completed with zero executor failures and verified final-checkpoint hashes.

The subsequent source audit passed for all 30 jobs and 300 saved checkpoints. Deterministic nominal-validation re-evaluation preserved raw and discounted return tensors and reproduced the logged hypervolume and expected utility at every checkpoint. The aggregation then failed closed: both Minecart ore objectives were constant zero across all validation episodes, saved checkpoints, arms, and seeds. LunarLander was non-degenerate, but the primary lock is atomic across the audited block, so zero checkpoints were locked. The user chose to retain Minecart rather than exclude it.

The completed non-test diagnosis shows that all 15 selected Minecart training archives contain positive ore while all 14,400 greedy validation episodes return zero ore; 92.42% reach the time limit, and representative ensemble/head probes never choose `Mine`. This supports a shared sparse delayed-credit backbone failure rather than a reward-path failure or treatment effect. Remediation v1 then completed three fresh, validation-only Uniform-PCQN seeds and independently audited all 30 checkpoints. Its all-seeds gate failed: two selected checkpoints had zero ore, while the third passed with 28/160 positive episodes per ore objective.

A predeclared behavior probe subsequently traced seven v1 checkpoints over 1,120 validation episodes. Successful mining and delivery appeared at transient positive checkpoints and disappeared at later checkpoints within the same seed. This selected rare-transition retention rather than additional interactions or a bundled intervention. Remediation v2 is predeclared as a single-factor proportional prioritized-replay qualification with fresh seeds and unchanged v1 budgets, checkpoint selection, and pass rule. Before execution, a dated amendment corrected the loss wording from squared TD to the unchanged v1 masked Huber loss, preventing an unintended second factor. Its exact replay/loss contract and fail-closed runner/auditor passed the complete Python 3.11 quality gate plus a 20-interaction, 17-update non-evidence smoke under seed 9192. The three qualification seeds remain unexecuted and require review/authorization. A post-validation executor gate permanently blocks all matrix-v1 jobs. Final test remains locked and no comparative empirical claim exists.

## Operating rules

- Inspect the live state with `python scripts/research_harness.py roadmap list` and `status`.
- Change phase/deliverable status only when the registered evidence exists.
- Keep future phase evidence empty until it is generated; planned work is not evidence.
- Preserve separate gates for pilot calibration, training/update budgets, final evaluation, and publication claims.
- Update both the JSON roadmap and this explanation when phase logic changes.

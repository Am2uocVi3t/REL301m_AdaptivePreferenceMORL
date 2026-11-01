# Backbone and objective investigation — 1 November 2026

This review motivates a new finite development study. It does not reopen the
completed primary matrix, PER-v2 or failed F1 replay studies, and does not access
the final test. All managed computation and primary-source downloads stay on D:.

## Why the default parameters are not a task guarantee

The demo default is the validation preference nearest the uniform simplex
point (`scripts/package_course_recovery.py`), not a successful-episode selection.
It is a convenience for presenting trade-offs. Preference coordinates multiply
statically scaled rewards; equal coordinates do not impose equal physical
importance or require a landing/ore delivery. The weights affect the policy,
but conditioning sensitivity alone does not demonstrate useful task learning.
The existing 80-case behavioral audit must remain visible alongside the demo.

The new positive control uses ten paired development seeds, two frozen-model
preferences and Gymnasium's unmodified handwritten Lunar heuristic. The latter
is a diagnostic, not a learned MORL baseline or a substitute for the demo model.
Complete native reward/action/state traces are retained on D:; the versioned
summary is `research/evidence/lunar_objective_diagnosis_v1.json`.

| Controller | Native +100 / 10 | Native +100 and pad x / 10 | Mean steps |
|---|---:|---:|---:|
| Frozen model, default weights | 0 | 0 | 1000.0 |
| Frozen model, landing-heavy weights | 4 | 2 | 683.2 |
| Gymnasium handwritten heuristic | 8 | 7 | 216.9 |

Using the unchanged gamma=.99 and protocol scales, the heuristic beats the
default model in default-weight utility in 9/10 pairs (mean .2340 vs .0574).
At landing-heavy weights it beats the corresponding model in 9/10 pairs
(mean .0585 vs -.1961). These are ten environment seeds for one frozen model,
not ten independent training replicates. A learner/optimization problem remains
even under the existing utility; objective mismatch alone cannot explain it.
Pad-x is a stricter spatial diagnostic: the native environment's +100 condition
does not itself test the pad interval. Gamma rescoring of these same finite
traces is exploratory analysis, not training with a different discount factor.

## Primary-source comparison

The retrieval/extraction pass read the full primary papers and relevant source
files below. Legal PDFs and extracted text are under the ignored D-drive
directory `artifacts/research-review-primary-sources/`; PDFs are not committed.
Existing literature records are historical; this focused review does not
silently label newly screened material as a completed full-text reading.

| Primary source | Relevant evidence | Consequence for this project |
|---|---|---|
| [Abels et al., ICML 2019](https://proceedings.mlr.press/v97/abels19a.html), main Fig.3 and supplement Table 1 | Minecart to 1M decision steps, ten replicates; gamma .98, frame skip 4, SGD/momentum; conditioned network and trajectory-preserving replay | Our masked-head Adam PCQN is an adaptation. 100k is an exploration schedule horizon in this source, not its complete Minecart training budget. |
| [Yang et al., NeurIPS 2019](https://arxiv.org/abs/1908.08342), experiments; pinned MORL-Baselines v1.3.0 example | The paper does not report Minecart; the library provides a 100k Minecart example | The recent 100k/gamma .99/scaled-reward Envelope screen is a library-based feasibility adaptation, not paper reproduction or algorithm refutation. |
| [Reymond et al., AAMAS 2022](https://arxiv.org/abs/2204.05036), §4 and author implementation | PCN uses return/horizon conditioning and supervised trajectory replay; deterministic Minecart author setup uses 10M interactions and gamma 1 | PCN and PCQN are distinct. This is not a cheap stochastic-Minecart drop-in. Gamma 1 requires careful finite-horizon/bootstrap semantics. |
| [Terekhov and Gulcehre, 2024](https://arxiv.org/html/2407.16807v1), §6 and Appendices B/D | Stochastic Minecart uses 4M interactions, five seeds, gamma .99; entropy/normalization/architecture matter; substantial GPU cost | A useful later architecture baseline, but different dependencies, training/evaluation policies and checkpoint choices preclude copying its numerical ranking into our report. |

The multi-step motivation follows [Hessel et al., Rainbow](https://arxiv.org/html/1710.02298),
Introduction and multi-step section: faster propagation trades bias and variance.
Rainbow uses n=3 and Atari; it does **not** validate n=20 on Minecart. Twenty is
our explicitly unvalidated long-credit hypothesis. No claim that this is a
paper-proven default is permitted.

## Reproducibility correction

The recent Envelope runner passed its seed argument into upstream MOAgent,
which seeds a local Generator but does not seed Torch initialization, global
NumPy replay sampling or SciPy ore draws. A zero-update witness found different
initial-network hashes when only the seed argument was supplied; explicitly
seeding global Torch and NumPy produced identical hashes on repetition.
The three historical screens remain genuine numerical records with valid
source/model/metric audits, but are only partially seeded feasibility runs.
They must not be presented as fully reproducible paired training replicates.
Do not rerun or overwrite them to erase this limitation. The older PCQN runner
already seeds Torch and NumPy; this specific defect does not automatically
apply to that historical cohort.

## New experiment and bounded interpretation

The immutable-before-main-run plan is
`configs/experiments/credit_assignment_v1.json`: two arms (n=1 vs n=20), three
paired training seeds, both environments, 500k training interactions per job.
It changes credit-assignment span only. Uniform allocation, network, gamma,
reward scales, replay distribution, optimizer and update budgets are matched.
There are exactly 12 planned jobs / 6M training interactions; checkpoint
validation and task diagnostics have separate counters. All global RNGs are
seeded before environment/network construction. A repeated complete short
CUDA learning trace is required before main execution.

Returns stop at episode boundaries. True terminations stop bootstrap;
time-limit truncations bootstrap from the actual last pre-reset observation.
Budget-tail transitions are flushed without inventing an episode completion.
Off-policy n-step targets have uncorrected behavior-policy bias; this screen
cannot attribute any gain solely to faster propagation as opposed to that bias.

Final-checkpoint task gates are specified before training: every training seed
must reach 8/10 +100-and-pad Lunar cases at landing-heavy preference, or 5/10
ore-delivery Minecart cases at the declared ore-seeking preference. Intermediate
100k/250k checks describe learning; they cannot select a best checkpoint.
Report individual paired seed effects and failure cases, not significance from
three pairs. A pass qualifies this development backbone only; original adaptive
allocation questions and original final-test gates remain separate.

If both arms fail, the next justified decision is a separately designed
exploration/architecture study, not more seeds until a favorable result appears.
If the task gate passes, allocation comparisons still need their own matched
uniform/random/adaptive experiment. Neither outcome by itself completes the
original research questions.

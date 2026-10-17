# Experiment Audit Report — Minecart F1

Date: 2026-10-18, Asia/Ho_Chi_Minh. Auditor: fresh GPT-6-Astra ultra agent. Reviewer family: `openai`; review independence: `same-family`; acceptance status: `provisional`.

## Overall verdict: WARN

Integrity status: `warn`. The completed F1 artifacts support the recorded negative qualification result. I found no fabricated ground truth, self-normalized performance score, missing claimed F1 result, altered training source, or incorrect retention computation in the inspected evidence. Warnings concern ambiguous return-field naming, incomplete planned behavior measurements, and the scope/accounting limits below. A failed learner qualification is not an integrity failure.

All three A1R1 seeds have zero delivered ore in every saved nominal-validation checkpoint: 30 checkpoints and 4,800 evaluation episodes. Their frozen retention status is `never_expressed`. A0R0 has 79 positive episodes per ore objective across its 4,800 repeated checkpoint evaluations. This is a bounded negative replay-sufficiency result in simulation; it does not establish universal replay failure, an individual component effect, or a delayed-credit mechanism.

## Audit execution and evidence boundary

I read the implementation, frozen amendment/protocol, checkpoints, manifests, TensorBoard logs, trajectory metadata, replay histograms, resource records, all 60 referenced validation JSON files, qualification/source-audit records, and reporting documents directly. I used Python 3.11 for read-only artifact arithmetic and safe checkpoint loading. I did not train, execute an environment rollout, call an evaluator that steps an environment, access the final test, or call a paid provider. Report/JSON trace files were written only after the coordinator explicitly requested durable audit outputs.

Read-only checks independently regenerated `audit_f1_sources` and `build_f1_decision` in memory. Both outputs exactly equaled their saved JSON documents. I verified 159 distinct path/SHA-256 bindings reachable from the source audit and qualification, all 60 validation tensors and derived metrics, all 66 saved checkpoint provenance records, final-versus-step-1M model equality, trajectory eligibility/projection calculations, and resource byte/counter records. The 12 inspected training/evaluation source and frozen-config files matched execution commit `0660ecc865f3a3823f248f1f1955d70c2faf5936` byte for byte. The implementation qualification source bindings passed too. Largest observed hypervolume/expected-utility discrepancy against training logs was `4.291293542735275e-09`.

This is an internal-consistency and source-binding audit of retained artifacts, not independent physical observation or a fresh rerun. Cryptographic bindings do not independently prove that every historical action occurred. The semantic verdict remains same-family provisional.

## A. Ground-truth and return provenance — PASS

Evaluation returns come from `env.step(action)`, not the network's predicted values. The rollout accumulates actual simulated reward vectors, undiscounted and with gamma 0.99 (`src/evaluation/rollout.py:55`, `src/evaluation/rollout.py:62`, `src/evaluation/rollout.py:64`). The network chooses a greedy action from mean ensemble Q values (`src/models/q_network.py:75`, `src/models/q_network.py:88`); those predictions are not used as scored returns. Environment construction goes through MO-Gymnasium (`src/envs/wrapper.py:46`).

The installed MO-Gymnasium 1.3.2 Minecart implementation emits ore reward on return to base when cargo is sold (`/home/hei/.cache/rel301m-conda311/lib/python3.11/site-packages/mo_gymnasium/envs/minecart/minecart.py:478`, `:484`). This supports the phrase “no delivered ore”; absent ore reward alone does not establish that mining or cargo acquisition never occurred.

The fixed reward scale and hypervolume reference point predate F1 and are bound to environment-reference calibration, not F1 model output extrema (`configs/protocols/course_minecart_v0.json:7`, `:10`; `research/calibration/course_calibration_v2_freeze.json:31`). I checked the calibration proposal, environment-front artifact and installed Minecart config hashes. The environment reference geometry is calibration input, not an oracle target against which a model is credited with agreement (`research/calibration/minecart_v0_gamma099_reference_front.json:4`, `:21`).

## B. Score normalization and return units — WARN

No prediction-dependent normalization is used for F1 reported performance. The wrapper multiplies rewards by fixed positive protocol constants (`src/envs/wrapper.py:23`, `:30`), expected utility is a scalarized mean (`src/evaluation/metrics.py:76`), and hypervolume uses the frozen reference (`src/evaluation/metrics.py:24`). HPR softplus normalization produces a replay preference, not a reported performance score (`src/core/replay_buffer.py:203`).

The important naming caveat is that validation `raw_episode_returns` are **undiscounted protocol-scaled returns**, not native environment-unit returns. The evaluator builds a scaled environment and persists the rollout's accumulated values without inverse scaling (`src/evaluation/course_validation.py:343`, `:375`, `:437`). Both validation tensor fields therefore share scaled units. In contrast, training trajectory metadata explicitly divides its undiscounted accumulation by the scale before saving `raw_return` (`scripts/train.py:513`); its `discounted_return` remains scaled (`scripts/train.py:499`, `:505`; `src/core/replay_buffer.py:198`).

Native-unit validation totals can be derived by dividing by the recorded fixed scale, with normal float32 accumulation limits; they are not separately retained native reward traces. This does not change the zero/positive ore classification because scaling is positive. The updated results/narrative now state this distinction (`refine-logs/EXPERIMENT_RESULTS.md:49`; `NARRATIVE_REPORT.md:37`). Keep the warning attached to the artifact schema so downstream readers do not mix magnitudes.

## C. Results, hashes, budgets, manipulation and retention — PASS

Exactly six jobs completed with one recorded attempt each, paired seeds 20264021–20264023, A0R0 and A1R1, and ten checkpoints per job. Execution/config/checkpoint identities and budgets are checked by the source auditor (`src/evaluation/remediation.py:400`, `:429`, `:438`, `:463`, `:538`). The plan fixes these cells, seeds and budgets (`configs/remediations/minecart_pcqn_replay_f1.json:54`, `:108`, `:129`). All referenced files existed and hashes matched. The generic historical `kind`/`arm` labels are disambiguated by the exact F1 study/job/cell identifiers; they do not signify a different experiment.

| Category | Verified F1 expenditure |
|---|---:|
| Training interactions | 6,000,000 |
| Gradient updates | 5,970,006 |
| Sampled batch positions | 382,080,384 |
| Curriculum-evaluation steps during training | 11,476,292 |
| Validation steps during training | 8,654,847 |
| Subsequent nominal-validation re-audit steps | 8,654,847 |

Training counters are separate in saved checkpoints (`scripts/train.py:584`, `:621`). The source audit retains them, and qualification `evaluation_summary` counts only the subsequent audit (`src/evaluation/replay_feasibility.py:329`, `:356`; `research/qualification/minecart_pcqn_replay_f1.json:1270`). Each run has 995,001 updates and 63,680,064 batch positions. Evaluation schedules/case counts are matched, but realized episode lengths and environment-step expenditures differ between cells; this is not equal total wall-clock or total environment-step compute. The six job resource records sum to 18,563.533439159393 wall seconds, excluding subsequent audit and earlier research costs.

The planning Markdown's 9,600,000-step nominal-validation cap describes one ten-checkpoint evaluation sweep (`refine-logs/EXPERIMENT_PLAN.md:56`). It must not be read as the total of training-time validation plus re-audit: those two ledgers sum to 17,309,694 steps. The executable workflow explicitly includes both passes (`scripts/train.py:568`; `scripts/run_minecart_replay_f1.py:134`). Updated reports now expose the separate expenditures; do not retroactively rewrite the frozen plan or describe 6M as all computation.

Manipulation counters agree with code and retained trajectory summaries. A0R0 uses all-uniform draws and zero relabels. A1R1 uses 31,840,032 successful-stratum positions and the same number of uniform positions per seed, with zero fallback. Its first eligible episodes finish at steps 108, 169 and 88, before learning starts at 5,000, explaining zero fallback. Eligibility, fixed-pool nearest projection and every retained projected label were independently recomputed (`src/core/replay_buffer.py:166`, `:192`, `:203`, `:275`; `src/evaluation/replay_feasibility.py:227`, `:240`, `:427`).

| A1R1 seed | Eligible completed training trajectories | Relabel attempts | Changed preferences |
|---|---:|---:|---:|
| 20264021 | 1,176 | 47,905,037 | 46,313,803 |
| 20264022 | 1,134 | 46,778,025 | 45,294,470 |
| 20264023 | 1,073 | 48,095,879 | 45,826,066 |

These values are retained at `research/evidence/minecart_pcqn_replay_f1_source_audit.json:409`, `:863`, `:1315`. Exposure is real within the records, but is not evidence of useful learning. Although 7–8 labels occur, 84.3–87.9% of effective relabel positions map to pool index 4, so distinct-label counts alone should not be called broad preference coverage. This is a descriptive projection property, not a proven cause of failure.

Retention uses positive and distinct-positive discounted ore values, first pass by 800k, and that checkpoint plus the next two; all A1R1 seeds must pass (`src/evaluation/replay_feasibility.py:376`, `:408`; frozen rule `configs/remediations/minecart_pcqn_replay_f1.json:136`). It does not select the best hypervolume checkpoint. Recomputing every checkpoint decision and the all-seeds decision reproduced the saved failure exactly. The three `never_expressed` decisions are at `research/qualification/minecart_pcqn_replay_f1.json:828`, `:1039`, `:1250`; every continuation/unlock flag remains false at `:1269` and `:1301`.

## D. Metric execution and measurement completeness — WARN

The F1 runner calls candidate evaluation and the decision builder (`scripts/run_minecart_replay_f1.py:142`). The candidate evaluator calls the rollout, hypervolume, expected utility, frontier size, sparsity and controllability, and serializes their outputs (`src/evaluation/course_validation.py:361`, `:381`, `:439`). All these fields exist in the 60 files and were independently recomputed from stored returns. Positive/distinct ore counts and retention functions are also called, not merely defined (`src/evaluation/replay_feasibility.py:330`, `:341`). `normalize_returns` is an unused utility; IGD/regret are used by the separate generic evaluator but are not F1 evidence (`src/evaluation/metrics.py:62`; `scripts/evaluate.py:151`).

However, planned B1 `Mine`, cargo, delivery-path and action-margin diagnostics (`refine-logs/EXPERIMENT_PLAN.md:60`) are not retained by this evaluator. It saves returns and episode lengths, not action traces, cargo trajectories, action margins or termination/truncation flags (`src/evaluation/rollout.py:61`, `:71`; `src/evaluation/course_validation.py:436`). Delivered-ore positivity is available through rewards; the intervening behavior is not.

I verified 3,936 A0R0 and 4,705 A1R1 episodes have length 1,000. These are **episode-limit-length cases**, not independently certified timeouts: an episode can terminate at the limit, and flags were not saved. Updated results and narrative explicitly acknowledge both limitations (`refine-logs/EXPERIMENT_RESULTS.md:40`, `:69`; `NARRATIVE_REPORT.md:66`). Missing behavior diagnostics limit localization, not the core zero-delivered-ore/retention conclusion. Do not backfill this gap with invented traces or an unauthorized rollout.

## E. Scope and overclaims — WARN

Actual scope is one nominal simulated Minecart environment, one frozen PCQN configuration, two cells, three paired training seeds, ten checkpoints per run, and 32 fixed validation preferences with five episodes each (`configs/remediations/minecart_pcqn_replay_f1.json:29`, `:54`, `:129`). The 9,600 episodes repeat validation cases across checkpoints; they are not 9,600 independent training replicates. The training seed is the relevant replicate for method-level inference.

Current narrative and results restrict conclusions appropriately and make no unsupported significance claim (`NARRATIVE_REPORT.md:28`, `:34`, `:60`; `refine-logs/EXPERIMENT_RESULTS.md:24`). Registered allocation/robustness claims remain implemented or hypotheses rather than promoted empirical claims (`research/claims.json:7`, `:23`, `:39`, `:55`, `:71`, `:87`). The positive bounded-sufficiency claim is unsupported by F1; its empirical gate failed. The two-cell screen cannot separate sampling from relabeling effects; F2 was not run. No final-test preference-generalization or shifted-environment claim follows.

The remaining scope warning is incomplete execution of the wider planned behavior-measurement list, plus residual planning-document status debt: `refine-logs/EXPERIMENT_PLAN.md:105` still says `READY_TO_DISPATCH` and `:106` says `WAITING_F1`. The original tracker and narrative were stale prelaunch snapshots, not fabricated successful results. During this audit the coordinator synchronized tracker/status/narrative from completed artifacts; I inspected the updates directly. The current tracker correctly distinguishes complete execution, failed qualification and ineligible F2 (`refine-logs/EXPERIMENT_TRACKER.md:11`, `:26`). Historical prelaunch wording explicitly superseded in project status should not be treated as live authority.

## F. Evaluation type — PASS: simulation_only

F1 is simulated-environment policy evaluation using actual Minecart reward signals; it is not real-world ground-truth testing, human evaluation, or model-generated-reference scoring (`src/envs/wrapper.py:46`; `src/evaluation/rollout.py:62`). Checkpoint validation is nominal and validation-only, with split, seed, preferences and protocol verified (`src/evaluation/course_validation.py:142`, `:161`). The audit files confirm that scope, for example `artifacts/minecart-pcqn-replay-f1/validation-evidence/A1R1/seed20264021/checkpoint_step1000000.json:1119`. Deterministic synthetic implementation tests are separate engineering evidence, not the F1 empirical result.

## Action items and claim impact

1. Preserve the failed F1 decision and all locked continuation flags. Do not add seeds, extend budgets, tune for a win, run F2 or access final test from this audit.
2. Keep explicit return-unit language and all four interaction ledgers in any downstream report. Preserve the frozen evidence rather than renaming or rewriting historical tensors.
3. Retain the documented absence of Mine/cargo/action-margin and termination flags. Use “1,000-step episodes,” not certified timeout counts. No additional rollout is needed to report the bounded negative outcome.
4. Synchronize or visibly mark the experiment plan's milestone table as historical; preserve its predeclared design/budget wording and explain the separate re-audit ledger in current results.
5. Persist this response, structured verdict, exact input hashes and full same-family trace. Do not convert mechanical checks or this provisional review into cross-family scientific acceptance or new execution authority.

Supported with qualifiers: six completed matched-training-budget runs; verified replay exposure; zero delivered ore across all evaluated A1R1 checkpoints; failure of the frozen F1 retention screen in this configuration. Unsupported: successful bounded sufficiency, universal replay failure, reliable A0R0 superiority, individual component causality, delayed-credit mechanism proof, adaptive-allocation benefit, unseen-preference/environment generalization, and course-comparison completion. The updated report's descriptive A0R0 counts are supported without treating them as inferential confirmation.

The structured verdict contains the immutable primary evidence/source hashes and the latest reporting snapshots inspected. Earlier report snapshots changed only through coordinator synchronization during this review. No scientific outcome was changed by those edits.

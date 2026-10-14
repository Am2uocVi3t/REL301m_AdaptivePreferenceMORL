# Cross-Chat Research Handoff

Copy the complete prompt below into a new chat.

```text
You are continuing the REL301m Adaptive Preference MORL research project.

Before acting:
1. Read `AGENTS.md`, `.agents/memory/MEMORY.md`, and `docs/research/PROJECT_STATUS.md`.
2. Run `python scripts/research_harness.py doctor` and `python scripts/research_harness.py status`.
3. Run `git status --short --branch`; do not overwrite unrelated changes.
4. Read the relevant protocol/config/code directly before making scientific claims.

Snapshot generated: 2026-10-14T20:11:36+00:00
Expected working branch at generation: feature/ai-research-harness
Expected commit at generation: b513d31
Working tree dirty at generation: yes
Current phase: phase-1 — Claim and antecedent mapping (active)
Publication state: no multi-seed empirical claim established

Roadmap:
- phase-0 [complete]: Foundation and scientific repair
- phase-1 [active]: Claim and antecedent mapping
- phase-2 [not_started]: Pilot calibration and protocol freeze
- phase-3 [not_started]: Mechanism diagnostics
- phase-4 [not_started]: Paired-seed course experiment matrix
- phase-5 [not_started]: Course paper
- phase-6 [not_started]: Workshop and journal extension
- phase-7 [not_started]: Submission and artifact freeze

Research question:
Under matched interaction, update, evaluation, and tuning budgets, which signal—conditioning gap, masked-ensemble disagreement, local coverage and recency, or observed learning progress—best predicts and improves future performance in weak preference regions?

Source precedence:
1. Executed tests and versioned raw-result artifacts.
2. Code and protocol/config files.
3. Machine-readable registries under `research/`, `docs/research/PROJECT_STATUS.md`, and `docs/ARCHITECTURE.md`.
4. Editable proposal v2.
5. Other Markdown documents.
6. Original submitted proposal PDF (historical only).

Active claims:
- conditioning-gap-allocation [implemented]: Empirical conditioning gap identifies weak preference regions
- disagreement-allocation [implemented]: Masked-ensemble disagreement identifies useful allocation regions
- coverage-recency-allocation [implemented]: Local coverage and recency improve preference allocation
- learning-progress-allocation [hypothesis]: Observed learning progress is a better allocation target than difficulty or uncertainty
- combined-allocation [hypothesis]: Combining gap, disagreement, coverage/recency, and progress improves sample efficiency
- environment-shift-robustness [hypothesis]: Adaptive preference allocation affects robustness under dynamics shift

Literature queue:
- abels2019dynamic-weights [read; full_text; access=open_full_text]: Dynamic Weights in Multi-Objective Deep Reinforcement Learning
- yang2019envelope [read; full_text; access=open_full_text]: A Generalized Algorithm for Multi-Objective Reinforcement Learning and Policy Adaptation
- xu2020pgmorl [read; full_text; access=open_full_text]: Prediction-Guided Multi-Objective Reinforcement Learning for Continuous Robot Control
- reymond2022pcn [read; full_text; access=open_full_text]: Pareto Conditioned Networks
- lu2023capql [screened; abstract_only; access=blocked]: Multi-Objective Reinforcement Learning: Convexity, Stationarity and Pareto Optimality
- basaklar2023pdmorl [read; full_text; access=open_full_text]: PD-MORL: Preference-Driven Multi-Objective Reinforcement Learning Algorithm
- alegre2023gpi-prioritization [read; full_text; access=open_full_text]: Sample-Efficient Multi-Objective Learning via Generalized Policy Improvement Prioritization
- zhang2020value-disagreement [read; full_text; access=open_full_text]: Automatic Curriculum Learning through Value Disagreement
- portelas2020alp-gmm [read; full_text; access=open_full_text]: Teacher Algorithms for Curriculum Learning of Deep RL in Continuously Parameterized Environments
- jiang2021plr [read; full_text; access=open_full_text]: Prioritized Level Replay
- colas2019curious [read; full_text; access=open_full_text]: CURIOUS: Intrinsically Motivated Modular Multi-Goal Reinforcement Learning
- teoh2025morl-generalization [read; full_text; access=open_full_text]: On Generalization Across Environments In Multi-Objective Reinforcement Learning
- shianifar2026hpr [read; full_text; access=open_full_text]: Hindsight Preference Replay Improves Preference-Conditioned Multi-Objective Reinforcement Learning
- liu2025cmorl [read; full_text; access=open_full_text]: Efficient Discovery of Pareto Front for Multi-Objective Reinforcement Learning
- yang2025pcrl [read; full_text; access=open_full_text]: Preference Controllable Reinforcement Learning with Advanced Multi-Objective Optimization

Full-text requests for the user:
- lu2023capql: Multi-Objective Reinforcement Learning: Convexity, Stationarity and Pareto Optimality — https://openreview.net/forum?id=TjEzIsyEsQ6 — OpenReview abstract/index checked 2026-10-15. Direct PDF, attachment, and API endpoints returned an access challenge/HTTP 403; no legal alternative copy was found. Request uploaded PDF or authorized link.

Active experiments:
- pilot-protocol-freeze [planned]: Pilot-only reward-scale and hypervolume-reference calibration
- course-paired-matrix [blocked]: Paired-seed controls and allocation-signal ablations

Open blockers:
- Repair the pinned dependency set for Python 3.11; numpy==2.5.4 requires Python 3.12 or newer, so requirements.txt cannot install on the declared target runtime.
- Obtain a legal full-text copy of CAPQL; OpenReview PDF endpoints are blocked by an access challenge and no alternative authorized copy was found.
- Freeze reward scaling and dominated hypervolume reference points from pilot-only evidence.
- Validate GPI-LS under Python 3.11 with native cddlib headers.
- Behaviorally validate that every enabled dynamics shift changes the intended transitions.
- Run paired controls, signal ablations, and compatible close baselines after freezing the protocol.

Latest closed-session summary:
Formalized an evidence-gated Phase 0-7 roadmap and integrated it into the standard-library research harness, status, handoff, schemas, tests, workflow, and memory. Registered 15 primary/authoritative antecedents: 14 full-text readings and one CAPQL abstract-only access blocker. Added claim-level closest antecedents, bounded novelty verdicts, differentiating experiments, and falsifiers. The full suite passed 39 tests on the available CPU host environment, and 18 harness tests passed on Python 3.11.17. No large experiment or final-test evaluation ran, and no empirical performance claim was made.

Next actions:
1. Obtain an uploaded or authorized CAPQL full text and complete its mechanism note.
2. Review and approve the Phase 1 antecedent and novelty judgments, then close the phase or explicitly exclude CAPQL.
3. Repair Python 3.11 dependency pins and rerun the full quality gate before pilot calibration.

Non-negotiable scientific guardrails:
- Do not label a claim `experimentally_supported` without a versioned raw-result artifact.
- Do not use final-test data for tuning, normalization, reference points, or checkpoint selection.
- Separate preference generalization from environment/dynamics generalization.
- Match interaction, update, diagnostic-evaluation, final-evaluation, and tuning budgets.
- Literature: use primary sources; log queries; register metadata/BibTeX; complete notes; never commit PDFs.
- Search legal full-text alternatives autonomously. If access still fails, keep the paper `screened`, record
  `full_text_required`, state what was tried, and ask the user for an uploaded PDF or authorized link.
- Never make a strong novelty or mechanism claim from metadata or an abstract alone.
- End substantial sessions with `python scripts/research_harness.py session close ... --write-handoff`.

User request for this new session:
[PASTE THE NEW REQUEST HERE]
```

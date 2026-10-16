# Cross-Chat Research Handoff

Copy the complete prompt below into a new chat.

```text
You are continuing the REL301m Adaptive Preference MORL research project.

Before acting:
1. Read `AGENTS.md`, `.agents/memory/MEMORY.md`, and `docs/research/PROJECT_STATUS.md`.
2. Run `python scripts/research_harness.py doctor` and `python scripts/research_harness.py status`.
3. Run `git status --short --branch`; do not overwrite unrelated changes.
4. Read the relevant protocol/config/code directly before making scientific claims.

Snapshot generated: 2026-10-16T13:36:48+00:00
Expected working branch at generation: feature/pilot-calibration-protocol
Expected commit at generation: b29c915
Working tree dirty at generation: yes
Current phase: phase-4 — Paired-seed course experiment matrix (active)
Publication state: no multi-seed empirical claim established

Roadmap:
- phase-0 [complete]: Foundation and scientific repair
- phase-1 [complete]: Claim and antecedent mapping
- phase-2 [complete]: Pilot calibration and protocol freeze
- phase-3 [complete]: Mechanism diagnostics
- phase-4 [active]: Paired-seed course experiment matrix
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
- lu2023capql [read; full_text; access=user_supplied]: Multi-Objective Reinforcement Learning: Convexity, Stationarity and Pareto Optimality
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
- chen2026morl-fb [read; full_text; access=author_manuscript]: A Reward-Free Viewpoint on Multi-Objective Reinforcement Learning
- ambadkar2026d3po [read; full_text; access=open_full_text]: Preference Conditioned Multi-Objective Reinforcement Learning: Decomposed, Diversity-Driven Policy Optimization
- delasheras2026controllability [read; full_text; access=open_full_text]: Controllability in Preference-Conditioned Multi-Objective Reinforcement Learning
- hu2026predictable-preferences [read; full_text; access=open_full_text]: Near-Minimax Multi-Objective RL under Predictable Adversarial Preferences and Preference-Free Exploration in Linear MDPs
- hu2026pbmorl [read; full_text; access=open_full_text]: Human-in-the-Loop Policy Optimization for Preference-Based Multi-Objective Reinforcement Learning
- hu2026reactive-preferences [read; full_text; access=open_full_text]: Time-Consistent Robust Multi-Objective Reinforcement Learning via a Bellman–Isaacs Weight-Adversary Recursion
- zhao2026mpft [read; full_text; access=open_full_text]: Population-Free Pareto Tracking for Sample-Efficient Multi-Policy MORL

Full-text requests for the user:
- None currently registered.

Active experiments:
- course-paired-matrix [blocked]: Paired-seed controls and allocation-signal ablations
- minecart-pcqn-remediation [failed]: Minecart sparse-credit PCQN backbone qualification

Open blockers:
- Minecart remediation v1 completed and failed its predeclared all-seeds qualification gate: two selected checkpoints had 0/160 positive episodes for both ore objectives, while one seed passed with 28/160. Sparse ore behavior appeared only transiently at a few non-selected checkpoints. Matrix v1 is permanently blocked; another run requires a separately predeclared remediation v2, and checkpoint locking, any revised matrix, and final test remain prohibited.

Latest closed-session summary:
Completed and independently audited Minecart remediation v1: exactly three predeclared 1M-interaction Uniform-PCQN runs, 30 checkpoints, and 4,800 nominal-validation episodes. The all-seeds gate failed because seeds 20264001 and 20264002 had zero positive ore episodes at their selected checkpoints, while seed 20264003 passed with 28/160 per ore objective. Sparse ore delivery was transient across checkpoints; no final-test or shifted data was accessed, no allocation claim was promoted, and matrix v1 remains permanently blocked.

Next actions:
1. Localize transient ore acquisition and retention using validation-only v1 evidence.
2. Predeclare a separately versioned remediation v2 before any algorithmic implementation or run.
3. Keep matrix v1, checkpoint locking, remaining course jobs, and final test blocked.

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

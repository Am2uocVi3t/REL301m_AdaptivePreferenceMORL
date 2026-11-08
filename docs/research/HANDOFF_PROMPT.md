# Cross-Chat Research Handoff

Copy the complete prompt below into a new chat.

```text
You are continuing the REL301m Adaptive Preference MORL research project.

Before acting:
1. Read `AGENTS.md`, `.agents/memory/MEMORY.md`, and `docs/research/PROJECT_STATUS.md`.
2. Run `python scripts/research_harness.py doctor` and `python scripts/research_harness.py status`.
3. Run `git status --short --branch`; do not overwrite unrelated changes.
4. Read the relevant protocol/config/code directly before making scientific claims.

Snapshot generated: 2026-11-08T07:39:55+00:00
Expected working branch at generation: cleanup/repo-restructure-rel301m
Expected commit at generation: 074adc2
Working tree dirty at generation: yes
Current phase: phase-4 — Paired-seed course experiment matrix (active)
Publication state: bounded three-seed Minecart task confirmation; adaptive-allocation claims unestablished

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
- terekhov2024architectures [read; full_text; access=open_full_text]: In Search for Architectures and Loss Functions in Multi-Objective Reinforcement Learning
- osband2016bootstrapped-dqn [read; full_text; access=open_full_text]: Deep Exploration via Bootstrapped DQN
- schulman2017ppo [screened; full_text; access=open_full_text]: Proximal Policy Optimization Algorithms
- schulman2015gae [screened; full_text; access=open_full_text]: High-Dimensional Continuous Control Using Generalized Advantage Estimation
- vanhasselt2016popart [screened; full_text; access=open_full_text]: Learning values across many orders of magnitude
- agarwal2021evaluation [screened; full_text; access=open_full_text]: Deep Reinforcement Learning at the Edge of the Statistical Precipice

Full-text requests for the user:
- schulman2017ppo: Proximal Policy Optimization Algorithms — https://arxiv.org/abs/1707.06347 — Relevant full-text sections consulted; status remains screened. Whole-paper reading not completed or claimed. Full text is legally accessible; no upload required.
- schulman2015gae: High-Dimensional Continuous Control Using Generalized Advantage Estimation — https://arxiv.org/abs/1506.02438 — Relevant full-text sections consulted; status remains screened. Whole-paper reading not completed or claimed. Full text is legally accessible; no upload required.
- vanhasselt2016popart: Learning values across many orders of magnitude — https://arxiv.org/abs/1602.07714v2 — Relevant full-text sections consulted; status remains screened. Whole-paper reading not completed or claimed. Full text is legally accessible; no upload required.
- agarwal2021evaluation: Deep Reinforcement Learning at the Edge of the Statistical Precipice — https://arxiv.org/abs/2108.13264 — Relevant full-text sections consulted; status remains screened. Whole-paper reading not completed or claimed. Full text is legally accessible; no upload required.

Active experiments:
- course-paired-matrix [blocked]: Paired-seed controls and allocation-signal ablations
- minecart-pcqn-remediation [failed]: Minecart sparse-credit PCQN backbone qualification
- minecart-pcqn-remediation-v2 [failed]: Minecart prioritized-replay PCQN backbone qualification
- minecart-pcqn-replay-f1 [failed]: Minecart successful-episode replay paired F1 feasibility screen
- credit-assignment-v1 [blocked]: Finite paired n-step backbone qualification
- onpolicy-backbone-pilot-v1 [planned]: Proposed source-mapped on-policy specialist and conditioned feasibility pilot

Open blockers:
- F1 completed all six paired jobs and passed source audit, but all three A1R1 seeds never expressed positive ore at any of 30 checkpoints; frozen retention qualification failed. Preserve the negative result and stop F1 training. F2, matrix v1, checkpoint locking and final test remain locked. No extra seeds, budget or tuning to seek a win. Independent semantic evidence reviews and non-manuscript analysis continue; course/conference manuscript and PDF are held by user.

Latest closed-session summary:
Reviewed research positioning and references:7 author-list errors corrected from primary sources; old24 reading records retained/not recertified;4 foundations screened targeted-only,28 library/21 cited. Report19p clarifies contribution, antecedents and unimplemented alternatives. New corrected ZIP verified40cases+81JS+Edge+launcher8768;233pass4skip. Executor-only provisional; no training/protocol/result changes.

Next actions:
1. Use corrected19-page reference-review package and bibliography; prepare final slides/current-demo recording and confirm lecturer scope. Original allocation comparison remains unestablished. No automatic training or independent-semantic acceptance claim; four foundations still need complete-paper review before marking read.

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

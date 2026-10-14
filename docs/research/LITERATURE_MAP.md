# Literature and Antecedent Map

Search date: **2026-10-15**. Scope: primary or authoritative sources for preference-conditioned MORL, adaptive weight/task allocation, curriculum signals, and environment generalization. All 15 registered papers were checked in full text; CAPQL was completed from a user-supplied ICLR 2023 PDF.

## Antecedent matrix

| Work | Venue/status | Mechanism | Adaptive allocation | Archive/gap | Uncertainty | Coverage/recency | Learning progress | Unseen preferences | Environment shift | Related claim IDs | Full-text evidence |
|---|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---|---|
| [Abels et al. (2019)](https://proceedings.mlr.press/v97/abels19a.html) | ICML 2019 | weight-conditioned Q-network + diverse replay | No | No | No | Diversity only | No | Yes | No | `combined-allocation` | PMLR full text |
| [Yang et al. (2019)](https://arxiv.org/abs/1908.08342) | NeurIPS 2019 | envelope-conditioned value network | No | Envelope | No | No | No | Yes | No | `combined-allocation` | Author full text |
| [Xu et al. (2020), PGMORL](https://proceedings.mlr.press/v119/xu20h.html) | ICML 2020 | predictor selects policy-weight tasks | Yes | Pareto improvement | No | Pareto set | Predicted | Partial | No | `conditioning-gap-allocation`, `learning-progress-allocation`, `combined-allocation` | PMLR full text |
| [Reymond et al. (2022), PCN](https://arxiv.org/abs/2204.05036) | AAMAS 2022 | return-conditioned policy trained from non-dominated archive | Target selection | Archive | No | Frontier targets | No | Yes | No | `combined-allocation` | Author full text |
| [Lu et al. (2023), CAPQL](https://openreview.net/forum?id=TjEzIsyEsQ6) | ICLR 2023 | conditioned SAC with entropy/concave reward augmentation | No; fixed `Dφ` | No | No | No | No | Conditioned; no held-out split | No | `combined-allocation` | User-supplied proceedings PDF |
| [Basaklar et al. (2023), PD-MORL](https://openreview.net/forum?id=zS9sRyaPFlJ) | ICLR 2023 | universal policy + preference prediction/alignment | Partial | Pareto alignment | No | No | No | Yes | No | `combined-allocation` | OpenReview full text |
| [Alegre et al. (2023), GPI-LS](https://www.ifaamas.org/Proceedings/aamas2023/pdfs/p2003.pdf) | AAMAS 2023 | GPI lower bound prioritizes weights and Dyna experience | Yes | GPI improvement gap | No | Indirect | Expected improvement | Yes | No | `conditioning-gap-allocation`, `learning-progress-allocation`, `combined-allocation` | Proceedings full text |
| [Zhang et al. (2020), VDS](https://papers.nips.cc/paper/2020/hash/566f0ea4f6c2e947f36795c8f58ba901-Abstract.html) | NeurIPS 2020 | independent value ensemble selects goals | Yes | No | Ensemble disagreement | Frontier effect | No | Not applicable | No | `disagreement-allocation`, `combined-allocation` | Proceedings full text |
| [Portelas et al. (2020), ALP-GMM](https://proceedings.mlr.press/v100/portelas20a.html) | CoRL 2019 / PMLR 2020 | GMM teacher over continuous task parameters | Yes | No | No | Task-space regions | Absolute progress | Not applicable | Task variation, not MORL shift | `learning-progress-allocation`, `combined-allocation` | PMLR full text |
| [Jiang et al. (2021), PLR](https://proceedings.mlr.press/v139/jiang21b.html) | ICML 2021 | value-loss priority mixed with staleness | Yes | No | No | Staleness | Proxy potential | Not applicable | Procedural levels | `coverage-recency-allocation`, `learning-progress-allocation`, `combined-allocation` | PMLR full text |
| [Colas et al. (2019), CURIOUS](https://proceedings.mlr.press/v97/colas19a.html) | ICML 2019 | goal-module teacher + hindsight replay | Yes | No | No | Module sampling | Absolute competence progress | Not applicable | No | `learning-progress-allocation`, `combined-allocation` | PMLR full text |
| [Teoh et al. (2025), MORL-Generalization](https://openreview.net/forum?id=tuEP424UQ5) | ICLR 2025 | benchmark separates preferences from contexts/environments | No | No | No | No | No | Separately evaluated | Yes | `environment-shift-robustness` | OpenReview full text |
| [Shianifar et al. (2026), HPR](https://arxiv.org/abs/2601.11604) | arXiv preprint; authors state AICS 2025 acceptance | hindsight preference relabeling in replay | Replay only | Achieved return | No | No | No | Yes | No | `combined-allocation` | Author full text |
| [Liu et al. (2025), C-MORL](https://proceedings.iclr.cc/paper_files/paper/2025/hash/adb77ecc8ba1c2d3135c86a46b8f2496-Abstract-Conference.html) | ICLR 2025 | crowding-guided constrained Pareto extension | Yes | Pareto archive | No | Crowding distance | No | Across frontier | No | `coverage-recency-allocation`, `conditioning-gap-allocation`, `combined-allocation` | Proceedings full text |
| [Yang et al. (2025), PCRL/PreCo](https://proceedings.mlr.press/v267/yang25ax.html) | ICML 2025 | controllable meta-policy + multi-objective gradient method | Optimization, not curriculum | No | No | No | No | Yes | No | `combined-allocation` | PMLR full text |

“Unseen preferences” records the paper's intended capability, not independent replication. “Environment shift” distinguishes contexts/dynamics from unseen preference weights.

## Per-claim verdicts

### `conditioning-gap-allocation`

- Closest antecedent: GPI-LS; PGMORL and C-MORL are adjacent.
- Known: additional learning is already directed using GPI bounds, predicted Pareto improvement, or sparse-front coverage.
- Difference: the repository uses an archive-relative scalarization gap from one conditioned policy.
- Verdict: **incremental** (medium confidence), not a new allocation problem.
- Differentiating experiment: measure score-at-time-*t* correlation with held-out improvement at *t+k*, then compare causal allocation against GPI-LS, uniform, and compute-matched random controls.
- Falsifier: equivalent prior scheduling or no predictive/causal value beyond the closest controls.
- Highest defensible wording: “The repository implements an empirical conditioning-gap allocation signal; predictive value is unvalidated.”

### `disagreement-allocation`

- Closest antecedent: Value Disagreement Sampling.
- Known: ensemble value dispersion already drives curricula as an epistemic-uncertainty proxy.
- Difference: preference candidates and shared masked heads replace goals and independent networks.
- Verdict: **incremental** (medium confidence); “calibrated epistemic uncertainty” is not established.
- Differentiating experiment: calibration, score-to-future-improvement, independent-ensemble sensitivity, and matched-random allocation.
- Falsifier: prior equivalent preference allocator, failed calibration, or no downstream benefit.
- Highest defensible wording: “Masked head disagreement is implemented as a candidate allocation signal, not established epistemic uncertainty.”

### `coverage-recency-allocation`

- Closest antecedent: PLR for staleness; C-MORL for sparse Pareto coverage.
- Known: recency and crowding/coverage are established curriculum and Pareto-search signals.
- Difference: both are combined locally over a preference simplex for one conditioned policy.
- Verdict: **incremental** (medium confidence).
- Differentiating experiment: coverage-only, recency-only, full, uniform, and matched-random ablations over pool size/front geometry.
- Falsifier: an equivalent sampler or no component benefit under matched budgets.
- Highest defensible wording: “The sampler includes local coverage and recency signals whose empirical benefit remains unknown.”

### `learning-progress-allocation`

- Closest antecedent: ALP-GMM; CURIOUS and GPI-LS are adjacent.
- Known: absolute learning progress is a mature curriculum heuristic.
- Difference: lagged preference-region progress is compared directly against difficulty/gap, disagreement, coverage/recency, and controls.
- Verdict: **incremental** (medium confidence).
- Differentiating experiment: preregister lagged predictive tests and a progress-only causal allocation arm.
- Falsifier: an equivalent controlled MORL study or no prediction/improvement beyond controls.
- Highest defensible wording: “We test whether observed learning progress is more predictive than difficulty or disagreement.”

### `combined-allocation`

- Closest antecedent: GPI-LS, with PGMORL, PLR, and ALP-GMM supplying components.
- Known: the signal families and adaptive task allocation are familiar; CAPQL conditions continuous-control policies on weights sampled from a fixed distribution.
- Difference: a common implementation permits a factorial, matched-budget comparison of outcome-dependent allocation signals within preference-conditioned MORL.
- Verdict: **novelty unresolved** (high confidence that broad novelty is indefensible).
- Differentiating experiment: all single-signal, selected pairwise, full, uniform, random, and compatible close-baseline arms with paired seeds.
- Falsifier: prior equivalent factorial evidence or no benefit/insight beyond controls.
- Highest defensible wording: “The study evaluates a combined allocation rule assembled from familiar signals; no novelty or superiority is claimed yet.”

### `environment-shift-robustness`

- Closest antecedent: MORL-Generalization.
- Known: environment/context generalization is already formalized separately from preference objectives.
- Difference: the repository isolates whether the allocation rule changes robustness of locked checkpoints under declared dynamics shifts.
- Verdict: **incremental** (medium confidence).
- Differentiating experiment: nominal versus predeclared OOD shifts after all tuning and checkpoint selection are locked on non-test data.
- Falsifier: equivalent prior matched-budget evidence or no paired robustness effect.
- Highest defensible wording: “Environment-shift robustness is a separate evaluation question from unseen-preference generalization.”

## Synthesis

The defensible contribution is not “the first adaptive preference-conditioned MORL method.” The most supportable study is a controlled test of which familiar allocation signal predicts and produces subsequent improvement in weak preference regions, under explicit compute budgets and with preference versus environment generalization kept separate. Even that contribution remains a hypothesis until Phase 4 evidence exists.

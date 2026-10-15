# Literature Search Log

Append one section per search session. Search primary or authoritative sources, record the exact date and query, and distinguish peer-reviewed versions from preprints.

## Entry template

### YYYY-MM-DD — topic

- Research question or claim IDs:
- Sources searched:
- Exact queries:
- Inclusion criteria:
- Exclusion criteria:
- Citation chaining performed:
- Papers registered:
- Negative search result and limitations:

### 2026-10-15 — adaptive preference allocation and adjacent curricula

- Research question or claim IDs: all six registered claims, emphasizing gap, disagreement, coverage/recency, progress, and environment shift.
- Sources searched: PMLR, NeurIPS proceedings, ICLR proceedings, OpenReview, IFAAMAS/AAMAS proceedings, arXiv, and citation/reference trails in included papers.
- Exact queries: `multi-objective reinforcement learning adaptive preference sampling`; `MORL adaptive weight vector selection Pareto archive`; `preference-conditioned MORL curriculum learning`; `MORL hypervolume-guided preference selection`; `MORL uncertainty-guided preference sampling`; `single-policy MORL weight allocation`; `environment generalization dynamics shift MORL`; `hindsight preference replay MORL`; `automatic curriculum value disagreement reinforcement learning`; `prioritized level replay coverage staleness curriculum`; plus exact-title and author searches for every candidate.
- Inclusion criteria: primary or authoritative source; mechanism directly covers preference-conditioned MORL, weight/task prioritization, a registered signal family, or environment generalization; enough evidence to map mechanism and falsifiable difference.
- Exclusion criteria: surveys as evidence for mechanism, unverified derivative summaries, unrelated multi-task curricula, pure scalarization comparisons without conditioning/allocation relevance, and duplicate preprint/proceedings records.
- Citation chaining performed: backward/forward conceptual chaining from GPI-LS and PGMORL to conditioned MORL; from disagreement/progress/recency mechanisms to VDS, ALP-GMM, CURIOUS, and PLR; recent-source search added MORL-Generalization, HPR, C-MORL, and PCRL.
- Papers registered: 15 total; 14 full-text `read`, CAPQL `screened` with `abstract_only` evidence and `full_text_required: true`.
- Negative search result and limitations: no primary source found that exactly combines the four registered signals in a factorial preference-conditioned MORL study. This is not proof of absence. CAPQL's full text could not be retrieved legally because OpenReview download/API endpoints returned an access challenge/HTTP 403 and no authorized alternative copy was located.

### 2026-10-15 — CAPQL user-supplied full-text follow-up

- Research question or claim IDs: `combined-allocation`; possible equivalence to adaptive preference scheduling.
- Source checked: user-supplied ICLR 2023 proceedings PDF corresponding to the registered OpenReview record.
- Provenance: local Git-ignored copy `research/literature/pdfs/lu2023capql.pdf`; SHA-256 `5412e729244b633a573585bc4a03fe529fef60288e344dc899ddc44d9b8f09c3`.
- Finding: CAPQL samples preferences from a fixed distribution `Dφ` and trains conditioned SAC-style Q/policy networks with entropy-based concave reward augmentation. It does not adapt preference allocation using gap, uncertainty, coverage/recency, or learning progress.
- Registry outcome: evidence raised from `abstract_only` to `full_text`, access recorded as `user_supplied`, and paper status raised from `screened` to `read`.

### 2026-10-15 — focused 2026 venue and preprint refresh

- Research question or claim IDs: `coverage-recency-allocation`, `combined-allocation`, and evaluation boundaries relevant to preference controllability and preference shifts.
- Sources searched: official ICLR/OpenReview records, ICML 2026 PMLR volume 306, arXiv 2026 records, and reference trails in the included papers.
- Exact queries: `site:openreview.net/forum?id= "multi-objective reinforcement learning" "ICLR 2026"`; `site:proceedings.mlr.press/v306 "Multi-Objective Reinforcement Learning"`; `site:arxiv.org/abs/26 "preference-conditioned" "multi-objective reinforcement learning"`; plus exact-title searches for every included candidate.
- Date window: records dated 2026 and available by 2026-10-15. Peer-reviewed venue records and preprints were kept distinct.
- Inclusion criteria: a primary full text that conditions on, selects, schedules, elicits, adversarially varies, or evaluates objective preferences in MORL; or a Pareto-search method that explicitly reallocates training toward weak/sparse regions.
- Exclusion criteria: application-only use of vector rewards; max-min, constrained, risk-sensitive, or lexicographic MORL without preference allocation/conditioning relevance; LLM preference optimization; duplicate venue/preprint records; and title/abstract matches that did not affect a registered claim or evaluation boundary.
- Included and read in full: Chen et al. (MORL-FB, ICLR 2026); Ambadkar et al. (D³PO, arXiv preprint); de las Heras Molins et al. (controllability, arXiv preprint); Hu and Yu (predictable preferences/PFE, ICML 2026); Hu, Luo, and Li (PBMORL, ICML 2026); Hu and Yu (reactive-preference robustness, ICML 2026); Zhao et al. (MPFT, ICML 2026).
- Key novelty update: PBMORL explicitly converts learned human utility and uncertainty into an adaptive distribution over scalarized optimization tasks. MPFT explicitly allocates additional policy training to sparse Pareto regions. Broad novelty for adaptive or coverage-driven preference allocation is therefore indefensible; the repository's narrower distinction remains its four autonomous outcome-derived signals, single-conditioned-policy setting, and matched factorial comparison.
- Evaluation update: the controllability preprint shows that front metrics need not measure preference compliance; the predictable-preference paper proposes convex-hull hypervolume under episode-start randomization; the reactive-preference paper concerns adversarial weight shifts rather than environment/dynamics shifts. These are protocol considerations, not empirical support for this repository.
- Screened out by scope after primary abstract/proceedings review: *Constrained Multi-Objective Reinforcement Learning with Max-Min Criterion* (fixed fairness/constraints); *Knothe-Rosenblatt Quantile Regression for Risk-sensitive MORL* (risk distributions); *Learning from Comparison: Constrained Projection Policy Optimization for Pareto-Front Improvement* (constrained optimizer rather than preference scheduler); *PROMO* and *ScenePilot* (application-focused); *Multi-Objective Preference Optimization* (LLM alignment rather than MOMDP preference allocation).
- Retrieval limitation: automated OpenReview PDF access for MORL-FB returned HTTP 403; the author-posted arXiv full text was used. No paywall or access control was bypassed. All temporary PDFs/text remained outside Git.
- Negative result and limitation: no 2026 source in this bounded sweep was found that compares the exact gap, masked-value disagreement, local coverage/recency, and lagged-progress signals in one preference-conditioned policy under matched rollout/update/evaluation budgets. This bounded venue/query sweep is not proof of global absence and should be refreshed before a publication submission.

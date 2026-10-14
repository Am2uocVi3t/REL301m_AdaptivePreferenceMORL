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

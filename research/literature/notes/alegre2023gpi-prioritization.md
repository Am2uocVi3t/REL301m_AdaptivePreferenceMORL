---
paper_id: alegre2023gpi-prioritization
evidence_level: full_text
---

# Sample-Efficient Multi-Objective Learning via Generalized Policy Improvement Prioritization

Primary source: https://www.ifaamas.org/Proceedings/aamas2023/pdfs/p2003.pdf

## Access report

Official AAMAS full text checked on 2026-10-15.

## Relevance and mechanism

GPI-LS is the closest direct antecedent for adaptive preference priority. It derives a GPI lower bound, selects weights where more learning is most useful, and can prioritize Dyna experience.

## Evidence and relationship to claims

Experiments evaluate sample efficiency and coverage. This is the closest antecedent for `conditioning-gap-allocation` and `combined-allocation`, and informs `learning-progress-allocation`. The project's possible difference is its single-model empirical signals and controlled comparison.

## Limitations and falsifiers

GPI assumptions and dependencies affect compatibility. If GPI-LS matches or dominates the proposed rules under matched budgets, claims must be narrowed or rejected.

Evidence pointer: prioritization derivation and experiments.

## Full-text reread for policy diagnosis — 2026-11-02

Re-read all ten pages of the official proceedings PDF. Local ignored copy:
`artifacts/research-review-primary-sources/alegre2023-gpi-prioritization.pdf`,
SHA256 `843f7974641eefc3016d227fd43b9a2f035a23c6d6a9ccfd0a2b7d800667b727`.
Section 2.2 Eq. 4 (p. 2005) gives GPI relative to source policies; it does not
guarantee optimality or remove approximate-value error requirements. Section 4
Eq. 11 (p. 2008) uses conditional Q: source preference inside the critic,
requested target preference outside in scalarization. Eq. 12 and Algorithm 2
line 22 describe vector TD and current/resampled support weights. A finite
bank inference heuristic alone is neither GPI-LS training nor GPI-PD/Dyna.
Our head-mean approximation has no certified error bound; do not transfer the
theoretical guarantee to the proposed heuristic or attribute our scalar Huber
auxiliary loss to this paper.

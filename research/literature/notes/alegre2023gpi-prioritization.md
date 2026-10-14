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

---
paper_id: reymond2022pcn
evidence_level: full_text
---

# Pareto Conditioned Networks

Primary source: https://arxiv.org/abs/2204.05036

## Access report

Author-posted AAMAS 2022 full text checked on 2026-10-15.

## Relevance and mechanism

PCN trains one supervised policy conditioned on desired return and remaining horizon. A non-dominated trajectory archive supplies attainable frontier targets.

## Evidence and relationship to claims

Discrete-action experiments evaluate Pareto coverage. Archive-conditioned target generation is known and constrains `combined-allocation`, but the paper does not conduct the four-signal allocation study.

## Limitations and falsifiers

Return conditioning is not value-based PCQN. A target-selection equivalence to the proposed sampler would narrow the claimed difference.

Evidence pointer: Sections 3–4.

# Round 1 Review

**Reviewer:** fresh Codex `gpt-6-astra`, `xhigh`  
**Review independence:** same-family  
**Acceptance status:** provisional  
**Verdict:** REVISE  
**Weighted score:** 6.65 / 10

## Scores

| Dimension | Score |
|---|---:|
| Problem Fidelity | 9 |
| Method Specificity | 6 |
| Contribution Quality | 6 |
| Frontier Leverage | 7 |
| Feasibility | 7 |
| Validation Focus | 6 |
| Venue Readiness | 5 |

## Blocking findings

1. The initial reference-point/suffix-return mapping was not justified and could
   vary the effective preference within one trajectory.
2. The buffer capacity equals the complete interaction budget, so buffer
   eviction is not the supported explanation. Sampling single transitions does
   not directly change delayed credit.
3. Sampling, fallback, truncation, and factorial semantics were incomplete.
4. Outcome-conditioned replay is an intentional reweighting heuristic, not a
   proven unbiased Bellman estimator.
5. The design can test bounded sufficiency, not identify retention versus
   delayed credit causally.
6. Seeds, total staged budget, checkpoint decision, and compact logging needed
   to be frozen.

## Required resolution

- Reframe as successful-experience exposure plus episode-level preference
  relabeling under the unchanged one-step learner.
- Use one episode-level HPR-style mapping and project it deterministically to the
  frozen preference pool.
- Define all four factorial cells and the exact joint sampler contract.
- State off-policy assumptions and outcome-selection limitations.
- Predeclare acquisition-limited, expression, and retention outcomes.
- Isolate random streams and log aggregate counters rather than every sampled
  vector.

Full raw trace: `.aris/traces/research-refine/2026-10-17_run01/001-round-1-review.response.md`.


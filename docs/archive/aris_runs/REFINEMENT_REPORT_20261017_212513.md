# Refinement Report

**Problem:** Minecart exploratory acquisition without stable greedy expression  
**Date:** 2026-10-17  
**Rounds:** 3 / 5  
**Final score:** 9.10 / 10  
**Final verdict:** READY for amendment planning only  
**Assurance:** same-family provisional

## Outputs

- `refine-logs/FINAL_PROPOSAL.md`
- `refine-logs/REVIEW_SUMMARY.md`
- `refine-logs/EXPERIMENT_PLAN.md`
- `refine-logs/EXPERIMENT_TRACKER.md`
- `.aris/traces/research-refine/2026-10-17_run01/`

## Score Evolution

| Round | Fidelity | Specificity | Contribution | Frontier | Feasibility | Validation | Venue | Overall | Verdict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | 9 | 6 | 6 | 7 | 7 | 6 | 5 | 6.65 | REVISE |
| 2 | 10 | 9 | 8 | 8 | 9 | 9 | 8 | 8.70 | REVISE |
| 3 | 10 | 9 | 9 | 9 | 9 | 9 | 8 | 9.10 | READY |

## Method Evolution Highlights

1. Replaced a reference-point/suffix-return map with one episode-level HPR
   equation and an explicit finite-pool projection.
2. Replaced vague trajectory replay with an executable 2x2 transition-sampling
   and relabel contract.
3. Replaced causal language with a bounded sufficiency claim and deterministic
   negative/inconclusive outcomes.

## Remaining Weaknesses

No implementation or experiment supports the proposed mechanism. F2 would be
conditional on F1 success, resource estimates remain an amendment prerequisite,
and same-family review is provisional. Cross-family acceptance, supervisor
authority, implementation audit, and training authorization are all absent.

## Next Gate

Supervisor chooses either:

1. authorize preparation of a versioned implementation/protocol amendment for
   the six-run F1 feasibility block; or
2. preserve the Minecart result as a blocked negative result and stop.


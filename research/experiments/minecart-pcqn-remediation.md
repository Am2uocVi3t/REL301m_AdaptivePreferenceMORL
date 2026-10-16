---
experiment_id: minecart-pcqn-remediation
plan: configs/remediations/minecart_pcqn_backbone_v1.json
status: failed
claim_ids: []
---

# Minecart PCQN backbone remediation v1

## Falsifiable question

Can a fixed, common PCQN training bundle learn both sparse Minecart ore objectives on the immutable validation protocol before allocation-signal comparisons resume?

This is a post-failure backbone qualification, not a course comparison and not evidence for any allocation claim.

## Diagnosis boundary

The diagnosis uses only training archives, the failed pilot, the 300-checkpoint nominal-validation audit, and validation-only policy probes. No test preference or shifted environment was accessed. The versioned diagnosis is `research/evidence/minecart_validation_diagnosis_v1.json`.

Facts supporting the failure mode:

- all 15 Minecart selected checkpoints contain positive ore outcomes in their training archives;
- all 14,400 primary validation episodes have zero return in both ore objectives, and 92.42% reach the 1,000-step limit;
- three representative selected checkpoints, evaluated as an ensemble and as each individual head, chose the `Mine` action zero times in 345,417 action decisions and never collected ore;
- Minecart emits ore only after departure, stopping at a mine, mining, and returning to base, while fuel cost is immediate and dense.

The evidence therefore localizes the failure to greedy policy learning under sparse delayed credit. It does not identify one causal hyperparameter and does not support a treatment comparison.

## Frozen remediation bundle

The environment, reward scale, `gamma=0.99`, network, optimizer, fixed training pool, and validation preferences remain unchanged. Uniform-PCQN receives:

- 1,000,000 training interactions;
- one gradient update opportunity per interaction after 5,000 learning-start steps;
- a 1,000,000-transition replay buffer;
- epsilon decay from 1.0 to 0.05 over 500,000 steps.

These changes extend exploration, retain early ore trajectories, and increase Bellman propagation opportunities without reward shaping, demonstrations, prioritized replay, n-step targets, or final-test feedback.

The exact non-executing command template and output root are stored in the JSON plan. The three seeds are substituted one at a time; all other arguments are fixed, including 100,000-step checkpoint/evaluation cadence and five validation episodes per preference. The expected update count is 995,001 per run.

`scripts/run_minecart_remediation.py` renders that template and previews by default. Execution fails closed unless it runs under Python 3.11 from a clean committed tree with the exact plan ID, explicit seed selectors, and a positive seed cap. Job status is written atomically and completed checkpoints are hash-verified before reuse. The audit independently verifies run manifests, Git provenance, budgets, periodic checkpoints, and TensorBoard validation curves before storing raw discounted and undiscounted validation returns for the fixed decision rule.

## Qualification and decision rule

Run only Uniform-PCQN on fresh seeds `20264001`–`20264003`. Evaluate ten predeclared checkpoints on the 32 immutable validation preferences with five episodes each. Select by the already-frozen hypervolume, expected-utility, earlier-step rule.

Every seed must have, at its selected checkpoint:

- at least 8/160 positive-return episodes for each ore objective;
- at least two distinct positive return values for each ore objective;
- finite, provenance-valid return tensors and exact budget counters;
- no final-test or shifted-environment access.

The 5% floor is fixed before execution to reject an isolated lucky delivery. These three runs become the disclosed Minecart remediation/tuning budget and are excluded from course contrasts.

## Fail-closed continuation

If any seed fails, Phase 4 remains blocked. Any n-step, prioritized-replay, demonstration, reward-shaping, or further hyperparameter proposal requires a new versioned remediation; it cannot be tried opportunistically.

If all seeds pass, create a new course study ID and manifest. Do not mutate matrix v1. Rerun all 65 Minecart PCQN jobs with the qualified common backbone; never combine the 15 failed v1 Minecart jobs with the revised study. Minecart comparator budget/update fairness needs a separate qualification. Unchanged LunarLander artifacts may be referenced only by exact hash, and final testing remains atomic and locked until the revised matrix completes.

## Observed outcome

The three predeclared runs completed and the independent source audit accepted all 30 checkpoints. The qualification evaluated 4,800 nominal-validation episodes (3,966,246 environment steps) with no test or shifted-environment access.

The all-seeds gate failed:

- seed `20264001`: selected step 800,000, 0/160 positive episodes for each ore objective;
- seed `20264002`: selected step 600,000, 0/160 for each ore objective;
- seed `20264003`: selected step 600,000, 28/160 for each ore objective, with 28 distinct positive values.

Checkpoint-wide evidence shows instability rather than uniform impossibility. Seed `20264002` produced 3/160 positive episodes at step 200,000 and 2/160 at step 800,000. Seed `20264003` produced 4/160 at step 500,000, 28/160 at step 600,000, 2/160 at step 900,000, and zero at later or intervening checkpoints. Seed `20264001` remained at zero throughout. Therefore increasing the interaction budget alone is not justified: rare ore-delivery behavior can emerge but is not consistently learned or retained.

The authoritative decision is `research/qualification/minecart_pcqn_backbone_v1.json`. Matrix v1 and final test remain locked. Any intervention aimed at rare-transition retention or delayed credit propagation must be specified in a separately versioned remediation v2 before implementation or execution.

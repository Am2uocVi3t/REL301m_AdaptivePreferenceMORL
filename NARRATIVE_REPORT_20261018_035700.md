# Narrative Report: Completed Minecart F1 Replay Screen

Date: 2026-10-18 (Asia/Ho_Chi_Minh).
Status: F1 training and nominal-validation audit complete; frozen retention
decision failed. Independent semantic reviews are in progress. Manuscript/PDF
writing remains held by the user.

## Problem and bounded question

The common PCQN backbone previously failed the primary Minecart qualification,
and one-step TD-error PER did not restore greedy ore expression. The separately
authorized F1 screen tests whether successful-episode stratification combined
with episode-level achieved-return preference relabeling is sufficient under the
frozen learner and budget. It does not test the course allocation-signal claims.

## Method and execution

F1 compares A0R0 (uniform/original preference) with A1R1 (successful-episode
stratification plus projected HPR-style episode relabeling) using three paired
training seeds. All six jobs completed on source commit
`0660ecc865f3a3823f248f1f1955d70c2faf5936`, with 1M training interactions and
995,001 updates each. Rewards, network, optimizer, exploration and the validation
protocol were fixed by the versioned amendment. Source audit passed 60 checkpoints.
F2 sampling-only/relabel-only cells were conditional and were not run.

## Executed results

Every A1R1 checkpoint has zero positive ore episodes for both ore objectives:
0/4,800 cases across its 30 checkpoint evaluations. All three seeds are
`never_expressed`; the frozen first-pass-plus-retention qualification is
`failed`. A0R0 has 79 positive cases per ore objective across 4,800 checkpoint
evaluations, with isolated or late expression, not a reliable overall solution.

The re-audit comprises 9,600 episodes / 8,654,847 environment steps. Cases repeat
fixed preferences and episode seeds across checkpoints; training seed, not
episode, is the experimental unit. The counts are descriptive, not a significance
test or causal decomposition. Evaluation "raw" tensors are undiscounted
protocol-scaled returns; native training trajectory returns are distinct.

## Complete accounting and evidence

Training interactions: 6,000,000; gradient updates: 5,970,006.
Curriculum-evaluation steps during training: 11,476,292.
Training-time validation steps: 8,654,847.
Independent validation re-audit steps: another 8,654,847.
Do not report 6M interactions as the entire computational cost.

- `refine-logs/EXPERIMENT_RESULTS.md`: per-seed counts, budget ledger,
  manipulation exposure and return-unit caveats.
- `research/evidence/minecart_pcqn_replay_f1_source_audit.json`: source,
  checkpoint, budget and manipulation bindings.
- `research/qualification/minecart_pcqn_replay_f1.json`: retention decisions,
  60 referenced validation artifacts and locked continuation flags.
- `artifacts/minecart-pcqn-replay-f1/validation-evidence/`: raw/discounted tensors.
- Proposal-review score 9.10 was readiness for amendment planning only, not
  empirical success, scientific acceptance or paper readiness.

## Claim boundary and limitations

The recorded F1 sufficiency gate failed in this Minecart/PCQN configuration.
No universal impossibility claim, replay-component causal attribution, delayed-
credit mechanism proof, adaptive-allocation benefit, preference-generalization
result or environment-shift claim follows. Same-family semantic review remains
provisional; deterministic source verification is not cross-family acceptance.

## Tables, figures and writing handoff

The result report contains per-seed outcome and budget/manipulation tables.
The decision artifact provides checkpoint-wise counts for any later figure.
No new manuscript figure or PDF was produced while the user hold is active.
Venue is not selected. Conference fit research is advisory, not submission.

## Next action and stop policy

Complete the integrity and result-to-claim records, bounded internal review and
evidence/report synchronization. Preserve the negative result. No additional
training, seed, tuning or budget is added to seek a positive result. F2, matrix
v1, checkpoint lock and final test remain locked. Course/conference TeX and PDF
updates wait for the user to lift the hold.

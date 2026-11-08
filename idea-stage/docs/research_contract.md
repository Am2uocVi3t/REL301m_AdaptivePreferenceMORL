# Research Contract: Minecart successful-episode replay F1

## Selected idea

Test the bounded successful-episode-stratified, HPR-style preference replay
proposal in `refine-logs/FINAL_PROPOSAL.md`. Existing exploration acquired ore,
but v1/v2 evidence did not establish stable greedy expression across seeds.
The user authorized this distinct F1 amendment on 17 October 2026.

## Prospective claim

The intervention is sufficient under the declared budget only if every A1R1
seed first passes the two-ore expression rule by 800k and passes the next two
100k checkpoints, with all source/manipulation audits passing. This is a
prospective criterion; no F1 empirical result exists at launch.

## Method and experiment

Completed episodes with positive delivered ore receive one projected
`softplus(G)` label from scaled discounted returns. A1R1 draws 32 positions
uniformly over eligible trajectories and then their transitions, plus 32
uniform replay positions, with replacement. Eligible positions use the same
effective preference in prediction and Double-DQN bootstrap. A0R0 uses 64
uniform positions and the original behavior preference.

F1 compares the two cells on seeds 20264021–20264023: six runs of 1M training
interactions, 995,001 updates, batch 64. Ten nominal-validation checkpoints use
32 preferences × 5 episodes each. Training, curriculum evaluation, training
validation and independent re-evaluation have separate counters. The existing
frozen protocol supplies geometry, reward scaling and reference points.

## Current results and limits

Engineering qualification and same-family code review passed; sanity runs are
excluded from research results. A1R1 sufficiency, superiority over A0R0 and any
causal mechanism remain unestablished. F2 is conditional and exploratory;
matrix v1, checkpoint locks and final test retain their separate gates.

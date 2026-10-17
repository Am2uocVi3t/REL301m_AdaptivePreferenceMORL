# F1 successful-episode replay results

Verified 2026-10-18 (Asia/Ho_Chi_Minh). This is a bounded, nominal-validation
replay-sufficiency screen, not the course allocation comparison.

## Execution and deterministic decision

Six jobs completed once on clean source commit
`0660ecc865f3a3823f248f1f1955d70c2faf5936`, with three paired training seeds
20264021–20264023 and cells A0R0 and A1R1. Each used 1,000,000 training
interactions and 995,001 gradient updates. Source audit passed six jobs and
60 checkpoints. The frozen qualification decision is **failed**: all three
A1R1 retention states are `never_expressed`.

| Cell | Training seed | Positive ore-0 episodes over 10 checkpoints | Positive ore-1 episodes over 10 checkpoints | Final checkpoint positives per ore objective |
|---|---:|---:|---:|---:|
| A0R0 | 20264021 | 60 / 1600 | 60 / 1600 | 19 / 160 |
| A0R0 | 20264022 | 19 / 1600 | 19 / 1600 | 17 / 160 |
| A0R0 | 20264023 | 0 / 1600 | 0 / 1600 | 0 / 160 |
| A1R1 | 20264021 | 0 / 1600 | 0 / 1600 | 0 / 160 |
| A1R1 | 20264022 | 0 / 1600 | 0 / 1600 | 0 / 160 |
| A1R1 | 20264023 | 0 / 1600 | 0 / 1600 | 0 / 160 |

Each checkpoint evaluates the same 32 validation preferences × 5 episode seeds.
Counts across checkpoints repeat fixed cases; 9,600 evaluations are not 9,600
independent training replicates. Experimental unit is the training seed.
No significance test or causal attribution is asserted.

## Budget ledger

| Category | Steps or updates |
|---|---:|
| Training interactions | 6,000,000 |
| Gradient updates | 5,970,006 |
| Curriculum-evaluation environment steps during training | 11,476,292 |
| Validation environment steps during training | 8,654,847 |
| Independent nominal-validation re-audit environment steps | 8,654,847 |

The independent re-audit has 60 checkpoints × 160 cases = 9,600 episodes.
A0R0 accounts for 4,800 episodes / 3,948,162 steps / 3,936 length-1,000 cases;
A1R1 accounts for 4,800 episodes / 4,706,685 steps / 4,705 length-1,000 cases.
Saved tensors do not retain termination/truncation flags, so these length counts
cannot independently certify timeouts.
The six training job resource records sum to 18,563.53 wall seconds; that is
training-job wall time, not audit or whole-project tuning cost.

## Return semantics and manipulation records

The evaluation field `raw_episode_returns` means **undiscounted protocol-scaled
vector returns**, not native environment units; `discounted_episode_returns`
uses the same scaled rewards and the frozen discount. Trajectory metadata
`raw_return` is a separate native-unit training record. Positive ore/zero ore
is invariant to the frozen positive scaling; do not mix magnitudes between
these sources or call scaled values native raw returns.

A1R1 manipulation counters are available, including eligible completed
trajectories, successful-stratum samples, attempted/actually changed preference
labels, projections and label histograms. They distinguish treatment exposure
from greedy validation performance; nonzero exposure is not sufficiency.

| A1R1 seed | Eligible training trajectories | Successful-stratum sampled positions | Relabel attempts | Actually changed positions |
|---|---:|---:|---:|---:|
| 20264021 | 1176 | 31840032 | 47905037 | 46313803 |
| 20264022 | 1134 | 31840032 | 46778025 | 45294470 |
| 20264023 | 1073 | 31840032 | 48095879 | 45826066 |

## Evidence and limits

The planned Mine/cargo/action-margin diagnostics are not emitted in the saved
evaluation artifacts. This prevents localizing absent ore delivery to absent
mining, cargo acquisition or return-to-base behavior. No such causal/localization
claim is made, and no extra rollout is performed to fill this gap.

- Frozen plan: `configs/remediations/minecart_pcqn_replay_f1.json`.
- Execution: `artifacts/minecart-pcqn-replay-f1/execution_status.json`.
- Source/manipulation audit: `research/evidence/minecart_pcqn_replay_f1_source_audit.json`.
- Decision and all 60 evidence references: `research/qualification/minecart_pcqn_replay_f1.json`.
- Return tensors: `artifacts/minecart-pcqn-replay-f1/validation-evidence/`.
- Coordinator verified all 60 validation hashes and the bound source-audit hash.
- `EXPERIMENT_AUDIT.json`: WARN, same-family provisional; core failed F1 verified,
  with return-unit, measurement-completeness and scope qualifiers.
- `CLAIMS_FROM_RESULTS.json`: claim_supported=no, same-family provisional,
  attached integrity_status=warn. No cross-family acceptance is granted.

This screen does not establish universal replay failure, a delayed-credit cause,
an individual sampling/relabel effect, adaptive-allocation benefit, preference
generalization, dynamics-shift robustness, or publication readiness.
F2, checkpoint lock, matrix v1 and final test remain locked. Preserve the
negative result; do not extend seeds/budget or tune/restart to seek a win.

Manuscript/TeX/PDF updates remain held by the user. Evidence reports and review
records may be completed; venue selection and submission remain separate.

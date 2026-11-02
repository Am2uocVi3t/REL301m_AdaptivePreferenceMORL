# Minecart PPO specialist S — completed pilot

The frozen4M-interaction job completed normally. Both final-only specialist
gates pass at the trained preference `[.45,.45,.1]`. This is one training seed,
not a multi-seed or arbitrary-preference result. Lunar was not trained here.

Evidence: `research/evidence/minecart_onpolicy_specialist_v1.json` contains all
928 development episode records, milestone summaries, source/artifact hashes
and executor audit outcome. Source at launch: clean `30a9baa`.
No independent semantic-review PASS is claimed.

## Final checkpoint, selected prospectively

| Preference | Mode | Ore deliveries | Mean frozen utility | Mean episode steps |
|---|---|---:|---:|---:|
| Trained `[.45,.45,.1]` | sampled |10/10| .468334 |17.1|
| Trained `[.45,.45,.1]` | argmax |10/10| .475012 |16.1|
| Secondary `[.8,.1,.1]` | sampled |9/10| .050331 |161.8|
| Secondary `[.8,.1,.1]` | argmax |10/10| .488817 |16.0|

Idle reference utility at both task profiles is approximately-.164942.
Both modes exceed it at the trained profile and meet>=8/10 deliveries.
Secondary-profile outcomes are descriptive, not the S selection gate.
Sampled secondary performance is not perfect: retain the one failure and long
episode rather than describing every final case as successful.

## Learning trajectory at trained profile

| Training interactions | Sampled deliveries /10 | Argmax deliveries /10 |
|---:|---:|---:|
|500k|7|0|
|1M|10|10|
|2M|10|10|
|4M final|10|10|

Each checkpoint also includes32 frozen validation preferences x3 episode seeds
x2 modes. Final ore-positive counts are96/96 sampled and83/96 argmax, but this
model was trained at only one preference. Ore occurrence does not establish
useful trade-off control or optimal utility at those other preferences.
The specialist is not a qualified replacement for a conditional policy.

## Executed accounting and audit

- Training4,000,000 interactions;7,815 rounds;250,080 actor /500,160 critic updates.
- Development928 episodes /148,181 steps; final-test0.
- Engineering qualification12,928 training interactions was separate.
- Source/config/protocol qualified hashes match the clean launch manifest.
- Final checkpoint checksum matches completion and the retained resume pointer;
  saved optimizer/counters and completed + partial episode lengths match4M.
- All4 evaluation-file hashes match saved checkpoint receipts. All928 return
  vectors/utility values and case counts checked; all160 task NPZ hashes,
  per-step raw/discounted rewards, lengths and action counts rechecked.
- Worker has exited; native monitor reports complete, GPU idle at inspection.

The audit reproduces the runner's float32 fixed scale representation when
reconstructing scaled return/utility, rather than substituting float64 constants.
No reward scale, checkpoint choice, threshold, seed or budget changed.

## Interpretation and next gate

Task competence at the trained preference is now supported for this bounded
pilot, unlike the completed P2 final policies. This is not matched-budget
evidence of PPO superiority: architecture/loss/exploration and training budget
all differ from P2. The data do not isolate a unique causal component.

The S pass permits preparing C, not automatically dispatching it. Next freeze
a separate conditional32-preference pilot, implement episode-fixed uniform
sampling, preserve exact resume/native-monitor coverage and qualify it before
launch. Do not warm-start C from this specialist, extend S, replace seeds,
unlock the original final test or claim adaptive allocation benefit. Lunar
remains a separate unresolved feasibility task. Phase4 remains active.

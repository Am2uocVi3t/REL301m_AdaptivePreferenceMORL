# Lunar confirmation v1 — prospective two-seed replication

Authorized by the user's 3 November request to carry out the proposed next
steps. This is repository-native execution, not ARIS paid/scheduled dispatch.
The existing Windows CUDA runtime is reused without installation or changes;
see configs/runtime/cuda_training_python311.json and its recorded witnesses.

## Claim and units

Question: does the frozen landing-heavy PPO+GAE specialist reproduce its
nominal task competence in two fresh training seeds? The pilot seed20265311
was already observed, so it is exploratory and excluded from prospective
confirmation statistics. Report n=2 prospective runs and n=1 pilot separately;
a three-run descriptive appendix may show all three with their roles labelled.
No superiority, adaptive-allocation benefit, arbitrary-weight competence or
dynamics-generalization claim is tested. Failed seeds remain in the report.

Candidate is identical to the completed pilot: ActorCritic8/4/4 width256,
vector GAE .95, frozen gamma .99 and utility scales,8 streams x128 fragments,
four epochs/eight minibatches/two critic steps, preference [.7,.1,.1,.1],
same optimizer, PopArt and entropy settings. The versioned new runner copies
the historical pilot loop to preserve its source hash and adds explicit seed
binding, run isolation and initial-parameter hashes. No pilot files are edited.

## Frozen design

Executable: configs/experiments/lunar_onpolicy_confirmation_v1.json.
New development protocol: configs/protocols/lunar_confirmation_development_v1.json.
It retains utility/reference/dynamics and training-pool metadata from its parent,
changes only development weight seed to20266421 (32 draws), and is never used
to access the original test split. Cases are development, not a hidden test.

Fresh training seeds20266311/20266312;4M each,8M total. Checkpoints500k/1M/2M/4M
are descriptive; final4M is the only gate checkpoint. Per run3909 rounds,
125088 actor/250176 critic updates; cohort250176 actor/500352 critic updates.
Task cases20266431–20266440; secondary uniform [.25]*4 is diagnostic only.
Validation cases20266451–20266453,32 new weights. Both sampled and argmax.
Per checkpoint232 evaluation episodes;928/run,1856/cohort, <=1,856,000 steps.
Preserve raw, discounted, scaled returns, actions/end flags and task traces.
No final test, curriculum evaluation, checkpoint selection or automatic extension.

Gate: EACH new training seed must have >=8/10 native +100 terminations with
lander x inside the native helipad, at the TRAINED profile in BOTH modes at4M.
Uniform landing/utility and32-weight EU remain separate diagnostics, not gates.
Summarize per seed first, then mean/sample SD over the two prospective seeds;
n=2 cannot support a precise population estimate or a significance claim.
Do not treat evaluation episodes or preferences as independent trained models.

## Qualification and execution

Before full launch, run two concurrent CUDA reference jobs of2112 interactions
and two corresponding interrupted/resumed jobs, killing only the two created
engineering process trees at durable1024. Final64 partial batch is included.
Compare every learner/optimizer/RNG/environment state, histories and trace hash
exactly across all8 streams for both seeds. Initial hashes must differ by seed.
Engineering expense8448 training interactions; reconstruction and development
steps reported separately, combined training ceiling20000; no task claim.

Run the full repository quality gate, commit a clean source tree, then launch
scripts/start_lunar_confirmation.ps1. Two workers share the existing4GiB GPU
only after the concurrent qualification succeeds. Completed run guards,
source/runtime/seed bindings and explicit inspected resume are mandatory.
No retries, new seeds, tuning or budget increases are scheduled. Source drift,
NaN, unknown process state, exhausted disk or failed qualification stop launch.
Native terminal follows LG ahead of completed pilot/Minecart; reads append-only
logs and immutable receipts, never rotating state JSON during writes.

## Parallel presentation diagnosis and reporting

The portable, frozen two-PPO demo is diagnosed with each default, uniform and
each simplex corner, five environment seeds20266511–20266515. Exactly55
argmax episodes (30 Lunar,25 Minecart), <=55k steps. No pass expectation at
corners; preserve failure and negative utility. These are presentation diagnostics
and cannot change the already-fixed candidate or confirmation design. No final
test access. Prepare a talk outline/script now; update outcome slides/report
only after completion/source audit. Lecturer rubric/deadline needs the user to
confirm with the lecturer; no message is sent on the user's behalf.

## Literature rationale

Agarwal et al., Deep Reinforcement Learning at the Edge of the Statistical
Precipice (2021), https://arxiv.org/html/2108.13264v3, introduction and evaluation
recommendations consulted3 November. Small numbers of independent training
runs leave substantial uncertainty; report seed-level data and avoid pooling
episodes into an inflated sample size. This is a targeted full-text consultation,
not a claim of a new completed whole-paper reading. No novelty is claimed for
PPO or the statistical practice. Finite local confirmation is prioritized over
an underpowered new algorithm-comparison sweep.

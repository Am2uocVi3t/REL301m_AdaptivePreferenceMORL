# Lunar PPO specialist L v1

Prospective scope (3 November 2026): one fresh seed20265311, fixed landing-heavy
preference[.7,.1,.1,.1],4M interactions. Preserve all Minecart code/results.
Same frozen Lunar gamma.99, reward scales and reference. Native environment:
8 observations,4 discrete actions,4 vector rewards (outcome/shaping/main/side).
Never interpret the native+100 outcome alone as landing inside the pad.

Decisions before code:
- Separate actor/critic multibody width256; PPO clip.2, Adam3e-4/eps1e-5,
  four epochs/eight minibatches, two critic steps per actor, clipgrad.5.
- Vector GAE(lambda.95),8 streams x128 steps =1024/batch. True termination
  suppresses bootstrap; time limit bootstraps the pre-reset state then stops
  recursion. Actor scalarization preserves frozen utility; PopArt critic only.
  This is a new candidate, not transfer of Minecart's results or paper optimum.
- Signed MDMM entropy target log4 to.2 over4M; rate3e-5,damping.01,initial.01.
  Four actions require log4, not Minecart's hard-coded log6.
- Milestones500k/1M/2M/4M, final only;3909 rounds,125088 actor/250176 critic
  updates. Partial batches split equally across8 minibatches, no dropped steps.
- New task seeds20265321..330; trained profile and uniform diagnostic profile,
  sampled/argmax separate. Existing32 validation weights x3 seeds20265341..343.
  Four checkpoints:928 dev episodes,<=928k steps; zero original final test.
- Final specialist gate>=8/10 native+100 AND lander x inside pad for each mode
  at trained preference. Record original scalar reward, angle/velocity/contact
  and native vectors. No standard-Gym200-score solved claim for vector utility.
- Box2D objects must not be pickled as exact state. Snapshot each stream's
  deterministic episode seed and action history, reconstruct by replay under
  identical source/binary, assert exact observation, then restore training RNG.
  Count reconstruction steps separately from logical training; qualify real
  process-kill/resume before main launch. Resume never selects a checkpoint.
- Engineering ceiling20k logical training interactions, reconstruction/evaluation
  costs separate. One seed only; no automatic conditional or confirmation run.
- Demo checkpoint rule: lowest confirmation seed20264311 at final4M, argmax,
  chosen by identifier, never by best observed score. Demo observations/actions
  must reproduce direct inference and keep raw reward traces. Lunar demo stays
  explicitly unqualified until its own new task evidence exists.

Primary sources: Farama MO-Lunar-Lander documentation and pinned installed
environment source; PPO (Schulman et al.,2017), GAE (Schulman et al.,2015/2016)
and prior MOPPO mapping. GAE is used as a bias/variance estimator; numerical
settings and bounded task gate are prospective project choices, not evidence
that Lunar will succeed.

https://mo-gymnasium.farama.org/environments/mo-lunar-lander/
https://gymnasium.farama.org/environments/box2d/lunar_lander/
https://arxiv.org/abs/1707.06347
https://arxiv.org/html/1506.02438v6 (targeted formula section; no new full-reading claim)

## Executed qualification

CUDA continuous2112 versus1024 + actual process kill + resume1088 matched model,
optimizers, all8 ongoing Box2D episodes, global RNG, training trace and losses.
The resumed process replayed239 physical reconstruction steps, counted separately
from4224 engineering training interactions and364 evaluation steps. Final64-sample
partial batch included. GAE boundaries, log4 entropy, frozen update budget,
Box2D future-state reconstruction and native Lunar-monitor priority are tested.
Full quality gate231 passed/4 existing skips. Qualification is technical,
executor-only, and does not establish a learned landing result.

Receipt: `research/qualification/lunar_onpolicy_specialist_v1.json`.
Clean-source launch: `powershell -File scripts/start_lunar_onpolicy.ps1`.
No automatic retry or conditional continuation; inspect interruption before
explicit `-Resume`. Output root: `artifacts/lunar-onpolicy-specialist-v1`.

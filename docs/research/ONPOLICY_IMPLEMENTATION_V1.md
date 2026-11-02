# Minecart on-policy implementation v1

Base: `0c05fe2`. User authorized implementation on 2 November 2026.
This is a new Minecart feasibility study, not a repair of historical results.
P2, Lunar, original checkpoint/final-test locks remain unchanged.

## Decisions frozen before implementation

| Decision | Choice and reason |
|---|---|
| Scope | Implement and qualify F0, then S only. C/G are not executable in this version. |
| Utility | Preserve the frozen scaled-vector utility `w.T @ return`. PopArt normalizes critic targets only. Scalar actor advantages use `w.T @ (TD1 - V)` then one batch-wide standard deviation. Unlike paper Eq18, do not divide each objective's advantage by a different sigma: that changes the relative utility weights. |
| Architecture | Separate actor/critic. Three objective-specific Linear(7,256)+ReLU bodies, preference-weighted sum, Linear(256,256)+ReLU, categorical6 / vector3 head. No observation/reward retuning. |
| PPO | Collection log-probs and vector values frozen for four epochs. TD(1) targets and PopArt statistics updated once per collected batch, not recomputed per epoch. Clip .2, Adam eps1e-5, LR3e-4 both, actor gradient clip .5, critic clip .5. Two critic optimizer steps per actor minibatch, as separate-trunk paper appendix. No KL early stop, LR schedule, advantage-objective renormalization or replay. |
| Entropy | Signed MDMM multiplier, Eq21: coefficient lambda+.01*(target-H); lambda +=3e-5*(target-H). Linear target log6 to .4 over exactly4M interactions. No positive clamp (equality constraint). |
| Return boundary | True terminal: no bootstrap. Time limit: bootstrap final pre-reset observation at old preference, then stop recursion. Fragment: bootstrap last next value. Never recurse across reset or changed preference. |
| Collection | Eight synchronous streams,64 steps each. Preferences fixed for an episode. S uses [.45,.45,.1] for all streams; conditional sampling is deferred. No gamma^episode-time actor weighting (standard PPO sampled-state surrogate, not exact paper reproduction). |
| Budget | Split fragments at milestones500k/1M/2M/4M; all divisible by8. 7,815 rounds,32 actor and64 critic updates each:250,080 actor /500,160 critic updates. Every epoch shuffles all samples and splits into8 equal minibatches; smallest batch64. |
| Evaluation | Every milestone: two modes (sampled/argmax), two task profiles x10 seeds20264121..130, plus32 existing validation preferences x3 seeds20264141..143. 232 episodes/checkpoint,928 total, <=928k steps. Task gate final only, trained profile, >=8/10 deliveries AND mean utility above idle; modes separate. Sampled uses a per-case seed derived from env seed, profile index and stream label. Evaluation preserves all training RNG. No test split. |
| Resume | Snapshot after optimizer round, every<=8192 interactions and at milestones; retain2 generations. Store cart/end, wrapper clocks, each stream observation/episode accumulators, global NumPy/Python/Torch/CUDA RNG, optimizer/PopArt/MDMM state and histories. Fixed geometry/distribution signatures checked on restore; never pickle/reconstruct an EzPickle environment as a substitute for dynamic state. |
| Failure | Single OS worker lease; never overwrite, resume completed, retry jobs, or launch conditional stages automatically. Bounded Windows sharing-error retry only for atomic publication. Restore exact saved step; discarded tail documented separately if a real interruption occurs. |
| Provenance | Bind executable plan, source, protocol, environment source/config, dependencies and device in checkpoints. Evaluation keeps raw/discounted/scaled vectors and task action traces. Engineering outputs explicitly separate from main pilot. All storage D:. |

## Source mapping

Primary paper: https://arxiv.org/html/2407.16807v1 (Eq10,19,21, Appendix Algorithm2).
Author configs pinned at c568cb6d689d7eaa50a2dec38197de8847f18adc are mapped in
`research/evidence/onpolicy_primary_source_map_20261102.json`.
Width/clip/entropy/PopArt are paper motivated; LR, batch standardization,
target refresh frequency and objective-preserving scalarization are explicit
project choices, not tuned optima or an exact reproduction. S success alone
cannot establish preference generalization, adaptive benefit or superiority.

## Acceptance ladder

1. Numerical tests: clipped loss sign/ratios, TD1 boundary examples, PopArt
   preservation, MDMM sign and utility-preserving scalarization.
2. Real Minecart smoke, finite CUDA parameter updates and exact8-stream resume,
   including process kill, mining stochasticity and evaluation RNG isolation.
3. Native terminal detects new study using append-only logs, never rotating
   training JSON; show sampled/argmax task results separately.
4. Full repository gate; source-bound qualification; clean committed launch.

Training/task success is an empirical outcome, not an implementation acceptance
claim. F0 qualification is limited to50k interactions, counted separately.

## Executed engineering evidence

`research/qualification/minecart_onpolicy_v1.json` records the source-bound CUDA
qualification: continuous6208 interactions versus4096 + actual process-tree kill
+ resume2112, exact on all8 stream states, model/optimizers/RNG, losses and training
returns. Includes the final64-sample partial batch. Combined training engineering
cost12,416 plus the earlier512-step spine =12,928, below50k. Development evaluation
in that qualification used2,098 steps, separate from training. No final-test access.
Reference stdout measured approximately481–560 interactions/s before final eval;
this short measurement includes startup effects and is not a long-run ETA promise.
Separate real Minecart tests exercise stochastic mining and time-limit restoration;
a Windows held-reader test exercises the bounded atomic JSON retry against a real
file handle. Native collector/render tests cover new-study detection and separate
sampled/argmax results without rotating JSON reads. Semantic review remains
executor-only; this evidence does not establish task competence.

Supported launch after clean source commit and F0 receipt:
`powershell -File scripts/start_minecart_onpolicy.ps1`.
Inspect interruption evidence before explicit `-Resume`; no automatic retries.
The finite S job runs independently of the monitor and stops at4M. C/G remain
unimplemented and disabled. Evaluation artifacts and both final mode gates are
under `artifacts/minecart-onpolicy-specialist-v1/runs/minecart-v0_S_seed20264111`.

# Executable Architecture and Scientific Contracts

This document describes the implemented v2 algorithm. Planned publication extensions are kept in the revised proposal and are not part of this runtime contract.

## Data flow

```text
fixed protocol + sampler distribution
              |
              v
 behavior preference --> rollout with one sampled ensemble head
              |                    |
              |                    +--> completed raw episode return --> Pareto archive
              v
 replay(s, a, r, s', terminated, truncated, w_behavior, bootstrap_mask)
              |
              v
 update preference selected by allocation_target
              |
              v
 per-head Double-DQN target + masked Huber loss
              |
              v
 curriculum checkpoint on a separate evaluation environment
       | gap | disagreement | local coverage/recency | learning progress
              |
              v
 softmax distribution mixed with a uniform floor
```

Training interactions, gradient updates, curriculum-evaluation steps, and validation steps are counted separately.

## Tensor contracts

- State: `[B, state_dim]`, `float32`.
- Preference: `[B, reward_dim]`, finite, non-negative, row sum one.
- Vector reward: `[B, reward_dim]`, maximization convention.
- Network output: `[K, B, action_dim, reward_dim]`.
- Bootstrap masks: `[B, K]`, at least one active head per transition.
- `terminated` disables Bellman continuation. `truncated` ends rollout collection but does not by itself disable continuation.
- Archive, conditioning gap, and primary evaluation metrics use discounted episodic returns with the protocol's fixed `gamma`; raw episodic returns are also retained for auditability.

## Action and target semantics

For head `k`, preference `w`, and next state `s'`:

```text
a*_k = argmax_a w^T Q_online,k(s', a, w)
y_k  = r + gamma * (1 - terminated) * Q_target,k(s', a*_k, w)
```

Each head chooses its own action. The per-transition bootstrap mask controls which head losses are included. Heads share a feature trunk, so documentation calls this a masked multi-head ensemble rather than a fully independent bootstrap ensemble.

## Allocation modes

| Mode | Rollout preference | Update preference |
|---|---|---|
| `rollout_only` | adaptive | stored behavior preference |
| `update_only` | uniform | adaptive |
| `rollout_and_update` | adaptive | adaptive |

For `uniform-pcqn`, both columns use uniform episode preferences and stored behavior preferences respectively. `random-curriculum-pcqn` performs the same curriculum evaluations as Adaptive-PCQN but updates its distribution from random scores.

## Curriculum signals

Candidate pool size is exact and contains simplex corners, the center, available edge midpoints, then seeded Dirichlet samples. Its seed and size come from the protocol, so paired training seeds share the same candidate set while retaining independent sampling trajectories.

- `gap(w)` uses the current policy's measured vector return; omitting that return is an error.
- `uncertainty(w)` is the variance across masked heads' scalarized greedy values over replay states.
- `coverage_recency(w)` combines inverse Gaussian-kernel visit density and normalized time since sampling.
- `progress(w)` is the absolute change in measured scalarized return between curriculum checkpoints.

Every signal is min-max normalized. Constant signals contribute zero. The final distribution is a temperature softmax mixed with the configured uniform floor.

## Evaluation contract

Protocol JSON files define the environment, reward dimension, reward scale, preference generation seeds, and a frozen reference point. Validation preferences are reused at every checkpoint. Test preferences are reserved for final evaluation.

Hypervolume is exact and deterministic: native 2-D computation or `pymoo` for three or more objectives. If `pymoo` is unavailable, high-dimensional HV fails explicitly instead of silently switching to stochastic Monte Carlo. If the reference point remains `null`, evaluation reports utility/front metrics and records HV as unavailable.

The evaluator writes raw per-episode vector returns, lengths, mean returns, Pareto front, metrics, protocol hash, checkpoint hash, dependency versions, Git state, and resolved arguments.

## Dynamics shifts

Constructor-level environment parameters are preferred because changing a Python attribute after Box2D initialization may not alter physics. LunarLander shifts are passed at environment construction. Attribute overrides are strict: a missing attribute raises an error. Minecart non-nominal shifts are disabled until a constructor-level intervention is identified and behaviorally verified.

## Public interfaces

- `VectorReplayBuffer.add(..., terminated, truncated, behavior_preference, bootstrap_mask=None)`
- `compute_double_dqn_targets(...)`
- `masked_bootstrap_loss(...)`
- `compute_conditioning_gap(preference, archive, current_policy_return)`
- `AdaptivePreferenceSampler.sample()` and `.sample_batch(batch_size)`
- `AdaptivePreferenceSampler.update_distribution(gap, uncertainty, progress, random_scores=None)`
- `load_protocol(path, split)`
- `evaluate_preferences(env, network, preferences, episodes_per_preference, device, seed)`
- `compute_hypervolume`, `compute_expected_utility`, `compute_scalarized_regret`, `compute_igd`, `compute_sparsity`
- `paired_permutation_test`, `bootstrap_ci`, `holm_adjust`

## Validation boundaries

Passing unit tests proves local invariants, not convergence, robustness, calibration, baseline fairness, or publication readiness. Those claims require versioned multi-seed artifacts under the protocol in the revised proposal.

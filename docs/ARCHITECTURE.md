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

For `uniform-pcqn`, rollout preferences are sampled uniformly from the same protocol-seeded finite candidate pool used by adaptive methods, and updates use stored behavior preferences. `update_only` also keeps rollout sampling uniform over that fixed pool even after its adaptive update distribution changes. `random-curriculum-pcqn` performs the same curriculum evaluations as Adaptive-PCQN but updates its distribution from random scores.

## Curriculum signals

Candidate pool size is exact and contains simplex corners, the center, available edge midpoints, then seeded Dirichlet samples. Its seed and size come from the protocol, so paired training seeds share the same candidate set while retaining independent sampling trajectories.

- `gap(w)` uses the current policy's measured vector return; omitting that return is an error.
- `uncertainty(w)` is the variance across masked heads' scalarized greedy values over replay states.
- `coverage_recency(w)` combines inverse Gaussian-kernel visit density and normalized time since sampling.
- `progress(w)` is the absolute change in measured scalarized return between curriculum checkpoints.
- `geometry(w)` is a static inverse kernel-density score over the fixed candidate pool. It is used only by the predeclared geometry-only antecedent control and contains no visit or learner-outcome signal.

Every signal is min-max normalized. Constant signals contribute zero. The final distribution is a temperature softmax mixed with the configured uniform floor.

## Evaluation contract

Protocol JSON files define the environment, reward dimension, reward scale, preference generation seeds, and a frozen reference point. Validation preferences are reused at every checkpoint. Test preferences are reserved for final evaluation.

Hypervolume is exact and deterministic: native 2-D computation or `pymoo` for three or more objectives. If `pymoo` is unavailable, high-dimensional HV fails explicitly instead of silently switching to stochastic Monte Carlo. If the reference point remains `null`, evaluation reports utility/front metrics and records HV as unavailable.

The evaluator writes raw per-episode vector returns, lengths, mean returns, Pareto front, metrics, per-objective Spearman controllability, protocol hash, checkpoint hash, dependency versions, Git state, and resolved arguments.

## Frozen course matrix

`configs/experiments/course_paired_matrix_v1.json` is the authoritative course-study contract. `scripts/build_course_matrix.py` validates it and renders a non-executing manifest; it has no execution flag. The frozen study uses five common seeds, fixed training/diagnostic/validation/final budgets, 13 PCQN arms, and two qualification-gated MORL comparator slots. Checkpoints are selected on validation data only, and the final-test split remains one-time post-lock evaluation.

`scripts/execute_course_matrix.py` is the separate Phase 4 execution boundary. It fails closed unless the rendered manifest exactly matches the current frozen study and protocol hashes and all versioned qualification hashes resolve. Course execution requires an exact study-ID acknowledgement, explicit selectors, and an explicit job limit. Status updates are atomic and bind completed jobs to final-artifact SHA-256 values. Resume is job-level only; the training process itself has no checkpoint-resume contract. Its isolated 20-step smoke mode rewrites the output directory and records `course_evidence: false`, so it cannot complete or support a course result.

Five paired seeds imply coarse exact-test resolution. Analysis is therefore estimation-first and cannot use a non-significant result as evidence of equivalence or absence of effect.

`scripts/audit_course_validation.py` is the validation-only checkpoint-lock boundary. It binds atomic execution status, run manifests, TensorBoard curves, periodic checkpoint hashes and counters, and frozen protocol hashes before re-evaluating any checkpoint. Per-checkpoint evidence is written atomically and reused only after full validation. The compact versioned aggregate retains fixed preference identifiers, raw and discounted episode-return tensors, episode lengths, budget counters, metrics, hashes, and missingness/degeneracy diagnostics. Selection applies maximum validation hypervolume, then expected utility, then earlier step for exact ties. A missing, non-finite, incompatible, shifted, test-split, hash-mismatched, or degenerate run blocks the atomic lock; partial environment locking does not unlock final testing.

After a failed primary validation gate, `scripts/execute_course_matrix.py` also requires a study-specific post-validation execution gate for every non-smoke launch. Matrix v1's gate is permanently blocked after the Minecart diagnosis; it cannot resume or be edited in place. A passed gate must bind a `passed: true` qualification artifact by path and SHA-256. The predeclared Minecart remediation is a separate validation-only Uniform-PCQN backbone qualification, and any successful continuation must use a new study ID and manifest.

`scripts/run_minecart_remediation.py` is the separate remediation execution and audit boundary. It renders only the three plan seeds, previews by default, requires Python 3.11 plus a clean committed worktree for execution, and records atomic job status bound to the plan hash and execution commit. Its auditor verifies run manifests, periodic checkpoints, budget counters, protocol hashes, and validation curves before independently reproducing raw validation returns. The resulting qualification artifact can authorize design of a new study after an all-seed pass, but it cannot unlock matrix v1 or final-test access.

## Pilot calibration contract

Calibration v1 is retained as a failed, informative attempt: its learner-derived Minecart returns were degenerate. ADR-003 and `configs/pilots/calibration_v2.json` define the accepted source-aware rule. Environments with an audited deterministic reference-front capability use a versioned geometry artifact; environments without one use independent Uniform-PCQN validation pilots sampled from the shared fixed protocol pool. `scripts/run_pilot_calibration.py` renders only the validation-pilot jobs, while `scripts/extract_reference_front.py` reproduces the declared geometry source. Final-test artifacts are rejected.

`scripts/calibrate_protocol.py` verifies plan, protocol, seed, split, shift, reference-front provenance, and artifact hashes before proposing values. Per-objective scales use the inverse 95th-percentile absolute return. The scaled coordinatewise minimum minus a fixed robust margin yields a reference point strictly dominated by every point from the environment's declared source. The output is a review proposal and cannot mutate protocol JSON. The accepted proposal, source front, and freeze record are versioned under `research/calibration/`; raw pilot checkpoints and evaluation tensors remain ignored. Post-freeze diagnostics cannot revise these values.

## Dynamics shifts

Constructor-level environment parameters are preferred because changing a Python attribute after Box2D initialization may not alter physics. LunarLander shifts are passed at environment construction. Attribute overrides are strict: a missing attribute raises an error. Minecart non-nominal shifts are disabled until a constructor-level intervention is identified and behaviorally verified.

The three enabled LunarLander shifts passed controlled nominal-versus-shift action-trace checks over three seeds. That qualification shows that transition behavior changes; it is not evidence of robustness or robustness improvement.

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
- `propose_calibration(returns, rule)`, `validate_calibration_artifact(...)`, and `validate_reference_front_artifact(...)`
- `build_pilot_jobs(plan, output_dir, python_executable, device, smoke)`
- `paired_permutation_test`, `bootstrap_ci`, `holm_adjust`

## Validation boundaries

Passing unit tests proves local invariants, not convergence, robustness, calibration, baseline fairness, or publication readiness. Those claims require versioned multi-seed artifacts under the protocol in the revised proposal.

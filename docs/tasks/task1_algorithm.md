# Task 1: Conditioned Q-learning and preference allocation

**Status:** implemented and unit-tested at invariant level; empirical validation pending.

## Implemented

- `VectorQNetwork.forward` returns `[K, B, actions, objectives]`.
- `VectorQNetwork.predict_action` performs linear scalarization for one head or the ensemble mean.
- Replay stores behavior preferences, true termination, time-limit truncation, and Bernoulli bootstrap masks.
- Every head selects its own Double-DQN next action.
- Masked Huber loss trains heads on different replay subsets.
- Conditioning gap requires an empirical current-policy return.
- Curriculum includes local coverage, explicit recency, observed learning progress, temperature, and a uniform floor.
- `rollout_only`, `update_only`, and `rollout_and_update` are executable ablations.

## Still to validate empirically

- Ensemble calibration and whether disagreement predicts error.
- Correlation between each score and future HV or tail-regret improvement.
- Stability across seeds, objective scales, candidate-pool sizes, and front geometry.
- Convergence is not established by the unit tests.

## Verification

```bash
python -m pytest tests/test_algorithm.py -q
```

Required publication evidence is defined in the revised proposal, not inferred from a passing shape test.

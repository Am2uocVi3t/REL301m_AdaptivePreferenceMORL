import numpy as np
import pytest
import torch

from src.evaluation.metrics import (
    compute_expected_utility,
    compute_hypervolume,
    compute_igd,
    compute_per_objective_controllability,
    compute_scalarized_regret,
    pareto_prune,
)
from src.evaluation.protocol import generate_preferences, load_protocol, resolve_training_pool_size
from src.evaluation.rollout import evaluate_preferences
from src.evaluation.stats import holm_adjust, paired_permutation_test
from src.models.q_network import VectorQNetwork


def test_pareto_prune_removes_dominated_points_and_duplicates():
    points = np.array([[1, 3], [2, 2], [3, 1], [1, 1], [2, 2]], dtype=np.float32)
    frontier = pareto_prune(points)
    assert {tuple(point) for point in frontier} == {(1.0, 3.0), (2.0, 2.0), (3.0, 1.0)}


def test_known_two_dimensional_hypervolume():
    points = np.array([[1, 3], [2, 2], [3, 1]], dtype=np.float32)
    assert compute_hypervolume(points, np.array([0, 0], dtype=np.float32)) == pytest.approx(6.0)


def test_utility_regret_and_igd_known_values():
    preferences = np.array([[1, 0], [0, 1]], dtype=np.float32)
    returns = np.array([[2, 0], [0, 2]], dtype=np.float32)
    reference = np.array([[3, 0], [0, 3]], dtype=np.float32)

    assert compute_expected_utility(returns, preferences) == pytest.approx(2.0)
    assert compute_scalarized_regret(returns, reference, preferences)["mean_regret"] == pytest.approx(1.0)
    assert compute_igd(returns, reference) == pytest.approx(1.0)


def test_per_objective_controllability_uses_tie_aware_rank_correlation():
    preferences = np.array([[1.0, 0.0], [0.5, 0.5], [0.0, 1.0]], dtype=np.float32)
    returns = np.array([[3.0, 0.0], [2.0, 2.0], [1.0, 4.0]], dtype=np.float32)

    result = compute_per_objective_controllability(returns, preferences)

    assert result["per_objective_spearman"] == pytest.approx([1.0, 1.0])
    assert result["mean_spearman"] == pytest.approx(1.0)


def test_five_pair_exact_test_cannot_cross_point_zero_five():
    result = paired_permutation_test(np.ones(5), np.zeros(5))
    assert result["mode"] == "exact"
    assert result["p_value"] == pytest.approx(0.0625)


def test_holm_adjustment_is_monotone_in_sorted_order():
    adjusted = holm_adjust(np.array([0.01, 0.04, 0.03]))
    assert np.allclose(adjusted, np.array([0.03, 0.06, 0.06]))


def test_protocol_preferences_are_fixed_and_on_simplex():
    first = generate_preferences(4, 10, 123)
    second = generate_preferences(4, 10, 123)
    protocol, loaded = load_protocol("configs/protocols/course_mo_lunar_lander_v3.json", "validation")

    assert np.array_equal(first, second)
    assert loaded.shape == (32, 4)
    assert np.allclose(loaded.sum(axis=1), 1.0)
    reference_point = np.asarray(protocol["reference_point"], dtype=np.float32)
    assert reference_point.shape == (4,)
    assert np.all(np.isfinite(reference_point))
    assert protocol["reference_point_status"] == "frozen_from_source_aware_calibration_v2"
    assert protocol["calibration_evidence"]["source_type"] == "validation_pilot"


def test_training_pool_size_defaults_to_protocol_and_rejects_mismatch():
    protocol = {"training_preference_pool": {"count": 5}}

    assert resolve_training_pool_size(protocol) == 5
    assert resolve_training_pool_size(protocol, 5) == 5
    with pytest.raises(ValueError, match="must match protocol"):
        resolve_training_pool_size(protocol, 32)


class TwoStepVectorRewardEnv:
    def reset(self, seed=None):
        self.step_index = 0
        return np.zeros(1, dtype=np.float32), {}

    def step(self, action):
        rewards = (np.array([1.0, 0.0]), np.array([2.0, 4.0]))
        reward = rewards[self.step_index]
        self.step_index += 1
        return np.zeros(1, dtype=np.float32), reward, self.step_index == 2, False, {}


def test_rollout_retains_raw_returns_and_uses_protocol_discount():
    network = VectorQNetwork(1, 1, 2, hidden_dims=(), num_heads=2)
    for parameter in network.parameters():
        torch.nn.init.zeros_(parameter)
    result = evaluate_preferences(
        TwoStepVectorRewardEnv(),
        network,
        np.array([[0.5, 0.5]], dtype=np.float32),
        episodes_per_preference=1,
        device="cpu",
        seed=5,
        discount_factor=0.5,
    )
    assert np.allclose(result["mean_returns"], [[2.0, 2.0]])
    assert np.allclose(result["raw_mean_returns"], [[3.0, 4.0]])

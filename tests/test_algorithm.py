from argparse import Namespace

import numpy as np
import pytest
import torch

from scripts.train import choose_rollout_preference
from src.core.pareto_archive import ParetoArchive
from src.core.replay_buffer import VectorReplayBuffer
from src.curriculum.gap import compute_conditioning_gap
from src.curriculum.sampler import AdaptivePreferenceSampler
from src.curriculum.uncertainty import compute_bootstrap_uncertainty
from src.models.q_network import VectorQNetwork
from src.models.update import compute_double_dqn_targets, masked_bootstrap_loss


def test_vector_q_network_forward_and_action_shapes():
    network = VectorQNetwork(8, 4, 4, num_heads=3)
    states = torch.randn(16, 8)
    preferences = torch.full((16, 4), 0.25)

    output = network(states, preferences)
    action, values = network.predict_action(states[0], preferences[0], head_idx=None)

    assert output.shape == (3, 16, 4, 4)
    assert 0 <= action < 4
    assert values.shape == (4,)


def test_replay_preserves_preference_terminal_semantics_and_bootstrap_mask():
    replay = VectorReplayBuffer(10, 2, 2, 3, num_heads=3, seed=7)
    preference = np.array([0.2, 0.3, 0.5], dtype=np.float32)
    replay.add(
        np.array([1.0, 2.0]),
        1,
        np.array([3.0, 4.0, 5.0]),
        np.array([2.0, 3.0]),
        terminated=False,
        truncated=True,
        behavior_preference=preference,
        bootstrap_mask=np.array([1.0, 0.0, 1.0]),
    )

    batch = replay.sample(1)

    assert torch.allclose(batch.behavior_preferences[0], torch.tensor(preference))
    assert batch.terminated.item() == 0.0
    assert batch.truncated.item() == 1.0
    assert torch.equal(batch.bootstrap_masks[0], torch.tensor([1.0, 0.0, 1.0]))


def test_replay_rejects_non_simplex_preference():
    replay = VectorReplayBuffer(10, 2, 2, 2)
    with pytest.raises(ValueError, match="simplex"):
        replay.add(np.zeros(2), 0, np.ones(2), np.ones(2), False, False, np.array([0.2, 0.2]))


class FixedNetwork(VectorQNetwork):
    def __init__(self, values: torch.Tensor):
        super().__init__(
            1,
            values.shape[2],
            values.shape[3],
            hidden_dims=(),
            num_heads=values.shape[0],
        )
        self.values = values

    def forward(self, state: torch.Tensor, preference: torch.Tensor) -> torch.Tensor:
        return self.values.to(state.device).expand(-1, len(state), -1, -1)


def test_double_dqn_selects_a_separate_action_for_each_head():
    online_values = torch.tensor(
        [
            [[[5.0, 0.0], [0.0, 4.0]]],
            [[[0.0, 3.0], [4.0, 0.0]]],
        ]
    )
    target_values = torch.tensor(
        [
            [[[10.0, 1.0], [2.0, 20.0]]],
            [[[30.0, 3.0], [4.0, 40.0]]],
        ]
    )
    preferences = torch.tensor([[0.75, 0.25]])
    targets = compute_double_dqn_targets(
        FixedNetwork(online_values),
        FixedNetwork(target_values),
        torch.zeros((1, 1)),
        preferences,
        torch.tensor([[1.0, 2.0]]),
        torch.tensor([0.0]),
        gamma=0.5,
    )

    assert torch.allclose(targets[0, 0], torch.tensor([6.0, 2.5]))
    assert torch.allclose(targets[1, 0], torch.tensor([3.0, 22.0]))


def test_terminated_stops_bootstrap_but_truncation_is_not_used_as_terminal():
    values = torch.ones((2, 1, 2, 2)) * 10.0
    targets = compute_double_dqn_targets(
        FixedNetwork(values),
        FixedNetwork(values),
        torch.zeros((1, 1)),
        torch.tensor([[0.5, 0.5]]),
        torch.tensor([[1.0, 2.0]]),
        torch.tensor([1.0]),
        gamma=0.9,
    )
    assert torch.allclose(targets, torch.tensor([[[1.0, 2.0]], [[1.0, 2.0]]]))


def test_masked_bootstrap_loss_excludes_unselected_heads():
    predicted = torch.tensor([[[1.0]], [[100.0]]])
    target = torch.zeros_like(predicted)
    mask = torch.tensor([[1.0, 0.0]])
    assert masked_bootstrap_loss(predicted, target, mask).item() == pytest.approx(0.5)


def test_conditioning_gap_requires_empirical_current_return():
    archive = ParetoArchive(2)
    archive.add(np.array([10.0, 5.0]))
    archive.add(np.array([2.0, 20.0]))
    gap = compute_conditioning_gap(
        np.array([0.5, 0.5]),
        archive,
        np.array([5.0, 5.0]),
    )
    assert gap == pytest.approx(6.0)


def test_conditioning_gap_is_zero_until_archive_has_evidence():
    archive = ParetoArchive(2)
    gap = compute_conditioning_gap(
        np.array([0.5, 0.5]),
        archive,
        np.array([-10.0, -10.0]),
    )
    assert gap == 0.0


def test_sampler_has_exact_size_simplex_floor_and_history_signals():
    sampler = AdaptivePreferenceSampler(4, pool_size=11, uniform_floor=0.2, seed=2)
    for _ in range(5):
        sampler.sample_index()
    zeros = np.zeros(11, dtype=np.float32)
    sampler.update_distribution(zeros, zeros, zeros)

    assert sampler.pool.shape == (11, 4)
    assert np.allclose(sampler.pool.sum(axis=1), 1.0)
    assert np.all(sampler.pool >= 0.0)
    assert np.isclose(sampler.probabilities.sum(), 1.0)
    assert np.all(sampler.probabilities >= 0.2 / 11 - 1e-7)
    assert np.ptp(sampler.coverage_scores) > 0.0


def test_sampler_pool_is_fixed_across_training_seeds():
    first = AdaptivePreferenceSampler(4, pool_size=20, seed=1, pool_seed=99)
    second = AdaptivePreferenceSampler(4, pool_size=20, seed=2, pool_seed=99)
    assert np.array_equal(first.pool, second.pool)


def test_geometry_only_scores_are_static_and_change_sampling_distribution():
    sampler = AdaptivePreferenceSampler(
        3,
        pool_size=12,
        gap_weight=0.0,
        uncertainty_weight=0.0,
        coverage_weight=0.0,
        progress_weight=0.0,
        geometry_weight=1.0,
        uniform_floor=0.0,
        seed=3,
    )
    initial_geometry = sampler.geometry_scores.copy()
    zeros = np.zeros(sampler.pool_size, dtype=np.float32)

    for _ in range(20):
        sampler.sample_uniform_index()
    sampler.update_distribution(zeros, zeros, zeros)

    assert np.array_equal(sampler.geometry_scores, initial_geometry)
    assert np.ptp(sampler.geometry_scores) > 0.0
    assert np.ptp(sampler.probabilities) > 0.0


def test_uniform_rollouts_sample_only_from_fixed_candidate_pool():
    sampler = AdaptivePreferenceSampler(3, pool_size=7, seed=11, pool_seed=99)
    args = Namespace(algo="uniform-pcqn", allocation_target="rollout_and_update")

    sampled = np.asarray([choose_rollout_preference(args, sampler) for _ in range(200)])

    assert all(any(np.array_equal(value, candidate) for candidate in sampler.pool) for value in sampled)
    assert all(any(np.array_equal(value, anchor) for value in sampled) for anchor in np.eye(3, dtype=np.float32))


def test_update_only_rollouts_remain_uniform_when_adaptive_distribution_changes():
    sampler = AdaptivePreferenceSampler(2, pool_size=5, seed=7, pool_seed=99)
    sampler.probabilities[:] = 0.0
    sampler.probabilities[0] = 1.0
    args = Namespace(algo="adaptive-pcqn", allocation_target="update_only")

    sampled = np.asarray([choose_rollout_preference(args, sampler) for _ in range(100)])

    assert len(np.unique(sampled, axis=0)) > 1


def test_uncertainty_restores_training_mode():
    network = VectorQNetwork(3, 2, 2, num_heads=3)
    network.train()
    uncertainty = compute_bootstrap_uncertainty(
        network,
        torch.randn(5, 3),
        np.array([0.5, 0.5], dtype=np.float32),
    )
    assert uncertainty >= 0.0
    assert network.training

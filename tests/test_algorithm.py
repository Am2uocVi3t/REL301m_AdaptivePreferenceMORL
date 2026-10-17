from argparse import Namespace

import numpy as np
import pytest
import torch

from scripts.train import choose_rollout_preference, linear_priority_beta
from src.core.pareto_archive import ParetoArchive
from src.core.replay_buffer import VectorReplayBuffer
from src.curriculum.gap import compute_conditioning_gap
from src.curriculum.sampler import AdaptivePreferenceSampler
from src.curriculum.uncertainty import compute_bootstrap_uncertainty
from src.models.q_network import VectorQNetwork
from src.models.update import (
    compute_double_dqn_targets,
    masked_bootstrap_loss,
    masked_mean_absolute_td_error,
    weighted_masked_huber_loss,
)


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


def test_prioritized_replay_rejects_nonfinite_priority_parameters():
    with pytest.raises(ValueError, match="priority_alpha must be finite"):
        VectorReplayBuffer(10, 2, 2, 2, priority_alpha=np.nan)
    with pytest.raises(ValueError, match="priority_epsilon must be finite"):
        VectorReplayBuffer(10, 2, 2, 2, priority_epsilon=np.inf)


def test_prioritized_replay_uses_exact_proportional_probabilities_and_weights():
    replay = VectorReplayBuffer(
        3,
        1,
        2,
        2,
        sampling="prioritized",
        priority_alpha=1.0,
        priority_epsilon=0.5,
        seed=5,
    )
    for value in range(3):
        replay.add(
            np.array([value], dtype=np.float32),
            0,
            np.zeros(2, dtype=np.float32),
            np.array([value + 1], dtype=np.float32),
            False,
            False,
            np.array([0.5, 0.5], dtype=np.float32),
            bootstrap_mask=np.ones(3, dtype=np.float32),
        )
    replay.update_priorities(np.array([0, 1, 2]), np.array([0.5, 1.5, 3.5]))

    assert np.allclose(replay.sampling_probabilities(), np.array([1.0, 2.0, 4.0]) / 7.0)

    batch = replay.sample(8, beta=0.5)
    probabilities = replay.sampling_probabilities()[batch.indices]
    expected = np.power(len(replay) * probabilities, -0.5)
    expected /= expected.max()

    assert torch.allclose(batch.importance_weights.cpu(), torch.tensor(expected, dtype=torch.float32))


def test_prioritized_replay_new_transition_uses_current_maximum_priority():
    replay = VectorReplayBuffer(3, 1, 2, 2, sampling="prioritized", priority_epsilon=0.1)
    preference = np.array([0.5, 0.5], dtype=np.float32)
    mask = np.ones(3, dtype=np.float32)
    replay.add(np.zeros(1), 0, np.zeros(2), np.ones(1), False, False, preference, mask)
    replay.update_priorities(np.array([0]), np.array([4.9]))
    replay.add(np.ones(1), 1, np.ones(2), np.zeros(1), False, False, preference, mask)

    assert replay.priorities[:2].tolist() == pytest.approx([5.0, 5.0])


def test_uniform_replay_keeps_unit_importance_weights():
    replay = VectorReplayBuffer(2, 1, 2, 2, seed=3)
    preference = np.array([0.5, 0.5], dtype=np.float32)
    for _ in range(2):
        replay.add(
            np.zeros(1),
            0,
            np.zeros(2),
            np.ones(1),
            False,
            False,
            preference,
            bootstrap_mask=np.ones(3, dtype=np.float32),
        )

    batch = replay.sample(5, beta=0.9)

    assert np.array_equal(batch.indices, np.random.default_rng(3).integers(0, 2, size=5))
    assert torch.equal(batch.importance_weights, torch.ones(5))
    assert np.array_equal(replay.sampling_probabilities(), np.array([0.5, 0.5]))


def _add_trajectory(replay: VectorReplayBuffer, trajectory_id: int, preference: np.ndarray, count: int = 2):
    return [
        replay.add(
            np.array([float(index)]),
            index % 2,
            np.array([1.0, 0.0, -0.1]),
            np.array([float(index + 1)]),
            False,
            index == count - 1,
            preference,
            bootstrap_mask=np.ones(replay.num_heads, dtype=np.float32),
            trajectory_id=trajectory_id,
        )
        for index in range(count)
    ]


def test_successful_trajectory_projection_stratification_and_relabeling():
    replay = VectorReplayBuffer(20, 1, 2, 3, seed=5)
    behavior = np.array([1 / 3, 1 / 3, 1 / 3], dtype=np.float32)
    handles = _add_trajectory(replay, 7, behavior)
    episode_return = np.array([2.0, 1.0, -1.0], dtype=np.float32)
    continuous = np.logaddexp(0.0, episode_return)
    continuous /= continuous.sum()
    pool = np.stack((continuous, np.array([0.0, 0.0, 1.0])))

    result = replay.complete_trajectory(handles, 7, episode_return, pool)
    batch = replay.sample(64, successful_fraction=0.5, relabel_success=True)

    assert result["eligible"] is True
    assert result["projected_pool_index"] == 0
    assert torch.count_nonzero(batch.sample_origins).item() == 32
    expected = torch.tensor(continuous, dtype=torch.float32).repeat(64, 1)
    assert torch.allclose(batch.effective_preferences, expected)
    audit = replay.replay_audit()
    assert audit["success_positions_requested"] == 32
    assert audit["success_positions_sampled"] == 32
    assert audit["fallback_positions"] == 0
    assert audit["relabel_attempt_positions"] == 64
    assert audit["relabel_changed_positions"] == 64


def test_success_stratum_falls_back_and_partial_episode_is_never_eligible():
    replay = VectorReplayBuffer(10, 1, 2, 3, seed=6)
    preference = np.array([0.5, 0.5, 0.0], dtype=np.float32)
    _add_trajectory(replay, 3, preference)

    batch = replay.sample(64, successful_fraction=0.5, relabel_success=True)

    assert torch.count_nonzero(batch.sample_origins).item() == 0
    assert torch.allclose(batch.effective_preferences, batch.behavior_preferences)
    assert replay.replay_audit()["fallback_positions"] == 32


def test_generation_guard_rejects_overwritten_trajectory_handles():
    replay = VectorReplayBuffer(1, 1, 2, 3, seed=7)
    preference = np.array([0.5, 0.5, 0.0], dtype=np.float32)
    stale = _add_trajectory(replay, 1, preference, count=1)
    _add_trajectory(replay, 2, preference, count=1)

    with pytest.raises(ValueError, match="stale or mismatched"):
        replay.complete_trajectory(stale, 1, np.array([1.0, 0.0, -1.0]), np.array([[0.5, 0.5, 0.0]]))


def test_uniform_sampling_does_not_advance_bootstrap_rng():
    preference = np.array([0.5, 0.5], dtype=np.float32)
    first = VectorReplayBuffer(10, 1, 2, 2, seed=8)
    second = VectorReplayBuffer(10, 1, 2, 2, seed=8)
    first.add(np.zeros(1), 0, np.zeros(2), np.ones(1), False, False, preference)
    second.add(np.zeros(1), 0, np.zeros(2), np.ones(1), False, False, preference)
    first.sample(4)
    first.add(np.ones(1), 1, np.zeros(2), np.zeros(1), False, False, preference)
    second.add(np.ones(1), 1, np.zeros(2), np.zeros(1), False, False, preference)

    assert np.array_equal(first.bootstrap_masks[1], second.bootstrap_masks[1])


@pytest.mark.parametrize("stratify,relabel", [(False, False), (True, False), (False, True), (True, True)])
def test_all_replay_cells_keep_rewards_masks_and_behavior_preferences(stratify, relabel):
    replay = VectorReplayBuffer(20, 1, 2, 3, seed=20)
    preference = np.array([0.0, 0.0, 1.0], dtype=np.float32)
    handles = _add_trajectory(replay, 0, preference)
    replay.complete_trajectory(handles, 0, np.array([2.0, 0.0, -1.0]), np.array([[1.0, 0.0, 0.0]]))
    batch = replay.sample(64, successful_fraction=0.5 if stratify else 0.0, relabel_success=relabel)
    assert int(batch.sample_origins.sum()) == (32 if stratify else 0)
    assert torch.equal(batch.rewards, torch.tensor([[1.0, 0.0, -0.1]]).repeat(64, 1))
    assert torch.equal(batch.behavior_preferences, torch.tensor(preference).repeat(64, 1))
    assert torch.equal(batch.bootstrap_masks, torch.ones((64, 3)))
    expected = [1.0, 0.0, 0.0] if relabel else preference.tolist()
    assert torch.allclose(batch.effective_preferences, torch.tensor(expected).repeat(64, 1))


def test_cannot_finalize_partial_episode_or_use_stale_success_after_overwrite():
    replay = VectorReplayBuffer(2, 1, 2, 3, seed=4)
    preference = np.array([0.0, 0.0, 1.0], dtype=np.float32)
    handle = replay.add(np.zeros(1), 0, np.zeros(3), np.ones(1), False, False, preference, trajectory_id=0)
    with pytest.raises(ValueError, match="completed episode"):
        replay.complete_trajectory([handle], 0, np.ones(3), np.array([[1.0, 0.0, 0.0]]))
    handles = _add_trajectory(replay, 1, preference, count=1)
    replay.complete_trajectory(handles, 1, np.ones(3), np.array([[1.0, 0.0, 0.0]]))
    _add_trajectory(replay, 2, preference, count=2)
    batch = replay.sample(64, successful_fraction=0.5, relabel_success=True)
    assert not bool(batch.sample_origins.any())
    assert torch.equal(batch.effective_preferences, batch.behavior_preferences)


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


def test_prioritized_td_priority_averages_objectives_and_active_heads():
    predicted = torch.tensor(
        [
            [[1.0, 3.0], [2.0, 8.0]],
            [[5.0, 7.0], [4.0, 10.0]],
        ]
    )
    target = torch.zeros_like(predicted)
    masks = torch.tensor([[1.0, 0.0], [1.0, 1.0]])

    priorities = masked_mean_absolute_td_error(predicted, target, masks)

    assert torch.allclose(priorities, torch.tensor([2.0, 6.0]))


def test_prioritized_loss_weights_per_transition_masked_huber():
    predicted = torch.tensor(
        [
            [[1.0, 3.0], [2.0, 4.0]],
            [[100.0, 100.0], [6.0, 8.0]],
        ]
    )
    target = torch.zeros_like(predicted)
    masks = torch.tensor([[1.0, 0.0], [1.0, 1.0]])
    weights = torch.tensor([1.0, 0.5])

    loss = weighted_masked_huber_loss(predicted, target, masks, weights)

    assert loss.item() == pytest.approx((1.5 + 0.5 * 2.5 + 0.5 * 6.5) / 3.0)


def test_prioritized_huber_loss_with_unit_weights_matches_uniform_loss():
    predicted = torch.tensor(
        [
            [[1.0, 3.0], [2.0, 4.0]],
            [[100.0, 100.0], [6.0, 8.0]],
        ]
    )
    target = torch.zeros_like(predicted)
    masks = torch.tensor([[1.0, 0.0], [1.0, 1.0]])

    uniform_loss = masked_bootstrap_loss(predicted, target, masks)
    prioritized_loss = weighted_masked_huber_loss(predicted, target, masks, torch.ones(2))

    assert prioritized_loss.item() == pytest.approx(uniform_loss.item())


def test_priority_beta_schedule_includes_both_frozen_endpoints():
    assert linear_priority_beta(0, 995_001, 0.4, 1.0) == pytest.approx(0.4)
    assert linear_priority_beta(497_500, 995_001, 0.4, 1.0) == pytest.approx(0.7)
    assert linear_priority_beta(995_000, 995_001, 0.4, 1.0) == pytest.approx(1.0)


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

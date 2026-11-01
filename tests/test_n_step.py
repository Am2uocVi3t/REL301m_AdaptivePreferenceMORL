import numpy as np
import pytest
import torch

from src.core.n_step import NStepAccumulator, Transition, n_step_targets
from src.models.q_network import VectorQNetwork
from src.models.update import compute_double_dqn_targets


def transition(i, terminated=False, truncated=False):
    return Transition(
        np.array([i]), i, np.array([i + 1.0, -1.0]), np.array([i + 1]), terminated, truncated, np.array([0.7, 0.3])
    )


@pytest.mark.parametrize("terminated,truncated", [(True, False), (False, True)])
def test_episode_tail_has_exact_rewards_and_original_end_state(terminated, truncated):
    queue = NStepAccumulator(3, 0.5)
    assert not queue.append(transition(0))
    assert not queue.append(transition(1))
    emitted = queue.append(transition(2, terminated, truncated))
    np.testing.assert_allclose(emitted[0].reward, [2.75, -1.75])
    np.testing.assert_allclose(emitted[1].reward, [3.5, -1.5])
    assert [item.steps for item in emitted] == [3, 2, 1]
    assert all(item.last.terminated == terminated and item.last.truncated == truncated for item in emitted)
    assert not queue.pending
    assert not queue.append(transition(10))


def test_budget_tail_bootstraps_and_preference_cannot_change_mid_episode():
    queue = NStepAccumulator(20, 0.99)
    queue.append(transition(0))
    wrong = transition(1)
    wrong.preference = np.array([0.1, 0.9])
    with pytest.raises(ValueError, match="Preference"):
        queue.append(wrong)
    tail = queue.flush()
    assert tail[0].steps == 1 and not tail[0].last.terminated and not tail[0].last.truncated


def test_overlapping_windows_cover_each_original_transition_once():
    queue = NStepAccumulator(3, 0.5)
    results = []
    for i in range(5):
        results.extend(queue.append(transition(i)))
    results.extend(queue.flush())
    assert [item.first.action for item in results] == list(range(5))
    assert [item.steps for item in results] == [3, 3, 3, 2, 1]
    np.testing.assert_allclose(results[2].reward, [6.25, -1.75])


def test_targets_reduce_exactly_to_one_step_and_mask_only_true_terminal():
    torch.manual_seed(17)
    online, target = [VectorQNetwork(2, 3, 2, hidden_dims=[8]) for _ in range(2)]
    states, preferences = torch.ones(3, 2), torch.tensor([[0.7, 0.3]] * 3)
    rewards, terminated = torch.ones(3, 2), torch.tensor([0.0, 0.0, 1.0])
    expected = compute_double_dqn_targets(online, target, states, preferences, rewards, terminated, 0.99)
    actual = n_step_targets(online, target, states, preferences, rewards, terminated, torch.full((3,), 0.99))
    torch.testing.assert_close(actual, expected, rtol=0, atol=0)
    torch.testing.assert_close(actual[:, 2], rewards[2].expand(3, -1))

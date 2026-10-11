import pytest
import torch
import numpy as np
from src.models.q_network import VectorQNetwork
from src.curriculum.uncertainty import compute_bootstrap_uncertainty
from src.curriculum.gap import compute_conditioning_gap
from src.curriculum.sampler import AdaptivePreferenceSampler
from src.core.pareto_archive import ParetoArchive
from src.core.replay_buffer import VectorReplayBuffer


def test_vector_q_network_forward_and_shapes():
    state_dim = 8
    action_dim = 4
    reward_dim = 4
    num_heads = 3
    batch_size = 16

    net = VectorQNetwork(state_dim, action_dim, reward_dim, num_heads=num_heads)
    s = torch.randn(batch_size, state_dim)
    w = torch.randn(batch_size, reward_dim)

    # Forward pass: shape must be [num_heads, batch_size, action_dim, reward_dim]
    out = net(s, w)
    assert out.shape == (num_heads, batch_size, action_dim, reward_dim)


def test_predict_action():
    state_dim = 8
    action_dim = 4
    reward_dim = 4
    net = VectorQNetwork(state_dim, action_dim, reward_dim, num_heads=3)

    s = torch.randn(state_dim)
    w = torch.tensor([0.25, 0.25, 0.25, 0.25])

    # Head 0 prediction
    action, q_vals = net.predict_action(s, w, head_idx=0)
    assert isinstance(action, int)
    assert 0 <= action < action_dim
    assert q_vals.shape == (action_dim,)

    # Ensemble mean prediction (head_idx=None)
    action_ens, q_vals_ens = net.predict_action(s, w, head_idx=None)
    assert isinstance(action_ens, int)
    assert 0 <= action_ens < action_dim


def test_compute_bootstrap_uncertainty():
    state_dim = 8
    action_dim = 4
    reward_dim = 4
    num_heads = 3
    net = VectorQNetwork(state_dim, action_dim, reward_dim, num_heads=num_heads)

    states_batch = torch.randn(32, state_dim)
    w = np.array([0.5, 0.2, 0.2, 0.1], dtype=np.float32)

    unc = compute_bootstrap_uncertainty(net, states_batch, w, device="cpu")
    assert isinstance(unc, float)
    assert unc >= 0.0
    assert not np.isnan(unc)


def test_compute_conditioning_gap():
    reward_dim = 4
    archive = ParetoArchive(reward_dim=reward_dim)
    w = np.array([0.5, 0.5, 0.0, 0.0], dtype=np.float32)

    # Empty archive
    gap_empty = compute_conditioning_gap(w, archive)
    assert gap_empty == 0.0

    # Add points to archive
    archive.add(np.array([10.0, 5.0, 0.0, 0.0]))
    archive.add(np.array([2.0, 20.0, 0.0, 0.0]))

    # If policy return is lower
    curr_return = np.array([5.0, 5.0, 0.0, 0.0])
    gap = compute_conditioning_gap(w, archive, curr_return)
    # max w^T v is max(0.5*10 + 0.5*5, 0.5*2 + 0.5*20) = max(7.5, 11) = 11.0
    # curr_val is 0.5*5 + 0.5*5 = 5.0
    # gap should be 11.0 - 5.0 = 6.0
    assert pytest.approx(gap, 0.01) == 6.0


def test_adaptive_preference_sampler():
    reward_dim = 3
    pool_size = 50
    sampler = AdaptivePreferenceSampler(reward_dim=reward_dim, pool_size=pool_size, eps_c=0.2)

    assert len(sampler.pool) >= pool_size
    assert np.isclose(np.sum(sampler.probabilities), 1.0)

    # Sample preference vector
    w = sampler.sample()
    assert len(w) == reward_dim
    assert np.isclose(np.sum(w), 1.0, atol=1e-5)
    assert np.all(w >= 0.0)

    # Test updating scores
    mock_gaps = np.random.uniform(0, 10, size=len(sampler.pool)).astype(np.float32)
    mock_unc = np.random.uniform(0, 5, size=len(sampler.pool)).astype(np.float32)

    sampler.update_scores(mock_gaps, mock_unc)

    assert np.isclose(np.sum(sampler.probabilities), 1.0, atol=1e-5)
    assert not np.any(np.isnan(sampler.probabilities))
    # Exploration floor: each candidate should have probability >= eps_c / |W| * 0.99
    min_prob = 0.2 / len(sampler.pool)
    assert np.all(sampler.probabilities >= min_prob - 1e-6)

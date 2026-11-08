import pytest
import torch

from scripts.run_preference_transfer import GPIMeanQ
from src.models.q_network import VectorQNetwork


def test_gpi_matches_literal_source_policy_target_utility_with_batches():
    torch.manual_seed(53)
    model = VectorQNetwork(7, 6, 3)
    bank = torch.tensor([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.45, 0.45, 0.1]])
    states = torch.randn(4, 7)
    targets = torch.softmax(torch.randn(4, 3), -1)
    adapter = GPIMeanQ(model, bank)
    composite = adapter(states, targets)
    for index in range(4):
        qs = torch.stack([model(states[index : index + 1], w[None])[:, 0] for w in bank], dim=1)
        values = torch.matmul(qs.mean(0), targets[index])
        expected = values.max(0).values
        actual = torch.matmul(composite[:, index].mean(0), targets[index])
        torch.testing.assert_close(actual, expected, atol=1e-7, rtol=1e-5)
        # Every action's vector must come from ONE common source for all objectives/heads.
        for action in range(6):
            source = values[:, action].argmax()
            torch.testing.assert_close(composite[:, index, action], qs[:, source, action])


def test_singleton_gpi_retains_source_vector_but_uses_requested_target_weight():
    torch.manual_seed(67)
    model = VectorQNetwork(2, 3, 2)
    state = torch.randn(1, 2)
    source = torch.tensor([[1.0, 0.0]])
    requested = torch.tensor([[0.0, 1.0]])
    torch.testing.assert_close(GPIMeanQ(model, source)(state, requested), model(state, source))


def test_gpi_rejects_invalid_source_bank():
    model = VectorQNetwork(2, 3, 2)
    for bank in (torch.empty(0, 2), torch.tensor([[2.0, -1.0]]), torch.tensor([[0.2, 0.2]])):
        with pytest.raises(ValueError):
            GPIMeanQ(model, bank)

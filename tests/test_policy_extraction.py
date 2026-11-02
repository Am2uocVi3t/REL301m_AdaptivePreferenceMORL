import torch

from scripts.diagnose_policy_extraction import greedy_action, scores, vote_action
from src.models.q_network import VectorQNetwork


def test_score_order_matches_production_inference_for_each_head_and_mean():
    torch.manual_seed(37)
    model = VectorQNetwork(7, 6, 3)
    state = torch.randn(7)
    preference = torch.tensor([0.45, 0.45, 0.1])
    with torch.inference_mode():
        q = model(state[None], preference[None])[:, 0]
        heads, mean = scores(q, preference)
        for head in range(3):
            action, original = model.predict_action(state, preference, head)
            torch.testing.assert_close(heads[head], original, rtol=0, atol=0)
            assert greedy_action(f"head{head}_greedy", 0, heads, mean) == action
        action, original = model.predict_action(state, preference, None)
        torch.testing.assert_close(mean, original, rtol=0, atol=0)
        assert greedy_action("mean_greedy", 0, heads, mean) == action


def test_voting_excludes_unsupported_mean_action_and_has_declared_tie_break():
    heads = torch.tensor([[10.0, 9.0, 0.0], [0.0, 9.0, 10.0], [8.0, 9.0, 10.0]])
    mean = heads.mean(0)
    assert mean.argmax().item() == 1
    assert vote_action(heads, mean) == 2
    tied = torch.eye(3)
    assert vote_action(tied, torch.tensor([0.0, 0.8, 0.2])) == 1

import torch
import torch.nn.functional as F

from scripts.preference_recovery_core import recovery_loss
from src.models.update import masked_bootstrap_loss


def test_zero_auxiliary_is_exact_original_vector_loss_and_gradient():
    torch.manual_seed(71)
    prediction = torch.randn(3, 5, 3, requires_grad=True)
    target = torch.randn_like(prediction)
    masks = torch.tensor([[1.0, 0.0, 1.0], [0.0, 1.0, 1.0], [1.0, 1.0, 0.0], [1.0, 1.0, 1.0], [0.0, 1.0, 0.0]])
    preferences = torch.softmax(torch.randn(5, 3), -1)
    old = masked_bootstrap_loss(prediction, target, masks)
    new = recovery_loss(prediction, target, masks, preferences, 0.0)
    torch.testing.assert_close(new, old, rtol=0, atol=0)
    torch.testing.assert_close(
        torch.autograd.grad(new, prediction)[0], torch.autograd.grad(old, prediction)[0], rtol=0, atol=0
    )


def test_hybrid_uses_huber_after_scalarization_and_excludes_inactive_heads():
    prediction = torch.tensor([[[2.0, -2.0]], [[3.0, 0.0]], [[900.0, 900.0]]], requires_grad=True)
    target = torch.zeros_like(prediction)
    masks = torch.tensor([[1.0, 1.0, 0.0]])
    preference = torch.tensor([[0.5, 0.5]])
    # Scalar TDs are 0 and 1.5: Huber then mean = (0+1)/2 = .5.
    # Mean vector Hubers for active heads are 1.5 and 1.25, mean 1.375.
    actual = recovery_loss(prediction, target, masks, preference, 0.5)
    torch.testing.assert_close(actual, torch.tensor(0.9375))
    gradient = torch.autograd.grad(actual, prediction)[0]
    assert torch.equal(gradient[2], torch.zeros_like(gradient[2]))
    assert torch.isfinite(gradient).all()


def test_each_relabel_weight_must_scalarize_its_own_row():
    prediction = torch.tensor([[[2.0, 9.0], [7.0, 3.0]]])
    target = torch.zeros_like(prediction)
    masks = torch.ones(2, 1)
    preferences = torch.eye(2)
    expected = F.smooth_l1_loss(torch.tensor([2.0, 3.0]), torch.zeros(2))
    torch.testing.assert_close(recovery_loss(prediction, target, masks, preferences, 1.0), expected)

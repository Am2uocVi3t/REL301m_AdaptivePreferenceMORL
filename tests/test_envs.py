import pytest

from src.envs.shift import apply_dynamics_shift


class FakeEnvironment:
    def __init__(self):
        self.unwrapped = self
        self.gravity = -10.0


def test_attribute_shift_is_applied_and_verified():
    environment = FakeEnvironment()
    apply_dynamics_shift(environment, {"gravity": -15.0})
    assert environment.gravity == -15.0


def test_unknown_shift_attribute_fails_instead_of_silently_doing_nothing():
    with pytest.raises(ValueError, match="does not expose"):
        apply_dynamics_shift(FakeEnvironment(), {"fuel_cost": 1.5})

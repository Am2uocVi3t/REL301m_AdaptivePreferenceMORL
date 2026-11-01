from __future__ import annotations

import random
from typing import Any

import numpy as np
import pytest
import torch

from scripts.run_envelope_feasibility import evaluate


class TwoStepEnv:
    def reset(self, seed: int) -> tuple[np.ndarray, dict[str, Any]]:
        self.step_count = 0
        return np.zeros(2), {}

    def step(self, action: int) -> tuple[np.ndarray, np.ndarray, bool, bool, dict[str, Any]]:
        self.step_count += 1
        return np.zeros(2), np.array([1.0, 2.0, -1.0]), False, self.step_count == 2, {}

    def close(self) -> None:
        pass


class TestAgent:
    __test__ = False

    def __init__(self) -> None:
        self.q_net = torch.nn.Linear(2, 2)
        self.np_random = np.random.default_rng(31)

    def eval(self, obs: np.ndarray, weight: np.ndarray) -> int:
        np.random.random()
        random.random()
        torch.rand(1)
        self.np_random.random()
        return 0


def test_validation_preserves_rng_and_retains_discounting_and_end_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("scripts.run_envelope_feasibility.make_mo_env", lambda *args, **kwargs: TwoStepEnv())
    agent = TestAgent()
    torch.manual_seed(41)
    np.random.seed(41)
    random.seed(41)
    expected = (torch.rand(1), np.random.random(), random.random(), np.random.default_rng(31).random())
    torch.manual_seed(41)
    np.random.seed(41)
    random.seed(41)
    protocol = {"env_id": "fake", "reward_dim": 3, "return_definition": {"gamma": 0.5}, "reference_point": [0, 0, -3]}
    result = evaluate(agent, protocol, np.array([[1.0, 0, 0]], dtype=np.float32), 2, 71)
    np.testing.assert_allclose(result["raw_episode_returns"], [[[2, 4, -2], [2, 4, -2]]])
    np.testing.assert_allclose(result["episode_returns"], [[[1.5, 3, -1.5], [1.5, 3, -1.5]]])
    assert result["evaluation_steps"] == 4
    assert not result["terminated"].any()
    assert result["truncated"].all()
    assert agent.q_net.training
    assert torch.equal(torch.rand(1), expected[0])
    assert np.random.random() == expected[1]
    assert random.random() == expected[2]
    assert agent.np_random.random() == expected[3]

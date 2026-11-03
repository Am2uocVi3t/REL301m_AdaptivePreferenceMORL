"""Reconstruct a Lunar Box2D episode from its seed and exact action history."""

from __future__ import annotations

from typing import Any

import numpy as np

from src.envs.wrapper import make_mo_env


class ReplayLunar:
    def __init__(self, training_seed: int, stream: int, nominal: dict[str, Any]):
        self.training_seed, self.stream = training_seed, stream
        self.env = make_mo_env("mo-lunar-lander-v3", dynamics_shift_config=nominal)
        self.episode = -1
        self.actions: list[int] = []
        self.episode_seed = 0
        self.observation = np.zeros(8, dtype=np.float32)

    @property
    def unwrapped(self):
        return self.env.unwrapped

    def get_wrapper_attr(self, name):
        return self.env.get_wrapper_attr(name)

    def reset(self):
        self.episode += 1
        self.episode_seed = int(
            np.random.SeedSequence([self.training_seed, self.stream, self.episode]).generate_state(1)[0]
        )
        self.actions = []
        self.observation, info = self.env.reset(seed=self.episode_seed)
        return self.observation, info

    def step(self, action):
        result = self.env.step(action)
        self.actions.append(int(action))
        self.observation = result[0]
        return result

    def state_dict(self):
        return {
            "episode": self.episode,
            "seed": self.episode_seed,
            "actions": self.actions.copy(),
            "observation": self.observation.copy(),
        }

    def restore(self, state, expected):
        self.episode = state["episode"] - 1
        self.reset()
        if self.episode_seed != state["seed"]:
            raise ValueError("Lunar reconstruction seed differs")
        for action in state["actions"]:
            self.step(action)
        np.testing.assert_array_equal(self.observation, state["observation"])
        np.testing.assert_array_equal(self.observation, expected)
        return len(state["actions"])

    def close(self):
        self.env.close()

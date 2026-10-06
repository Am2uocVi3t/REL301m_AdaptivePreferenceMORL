import os
import yaml
import pytest
import numpy as np
import gymnasium as gym

from src.envs.wrapper import make_mo_env, MORewardNormalizeWrapper
from src.envs.shift import apply_dynamics_shift, get_dynamics_shifts, MODynamicsShiftRewardWrapper
from src.baselines.morl_baselines_runner import MORLBaselineRunner


def test_make_mo_env_minecart():
    """Verify minecart-v0 initialization, dimensions, and step output."""
    env = make_mo_env("minecart-v0", seed=42)
    obs, info = env.reset(seed=42)

    assert obs.shape == (7,)
    assert env.action_space.n == 6

    action = env.action_space.sample()
    next_obs, reward, terminated, truncated, info = env.step(action)

    assert next_obs.shape == (7,)
    assert isinstance(reward, np.ndarray)
    assert reward.shape == (3,)  # [ore_1, ore_2, fuel]
    env.close()


def test_make_mo_env_lunarlander():
    """Verify mo-lunar-lander initialization, dimensions, and reward dimensions."""
    env = make_mo_env("mo-lunar-lander-v2", seed=42)
    obs, info = env.reset(seed=42)

    assert obs.shape == (8,)
    assert env.action_space.n == 4

    action = env.action_space.sample()
    next_obs, reward, terminated, truncated, info = env.step(action)

    assert next_obs.shape == (8,)
    assert isinstance(reward, np.ndarray)
    assert reward.shape == (4,)  # [landing/crash, shaping, main_fuel, side_fuel]
    env.close()


def test_reward_normalize_wrapper():
    """Verify MORewardNormalizeWrapper multiplies vector rewards by scale factors."""
    env = make_mo_env("minecart-v0", seed=42)
    scale_vector = [2.0, 0.5, 10.0]
    wrapped_env = MORewardNormalizeWrapper(env, scale_vector=scale_vector)

    raw_r = np.array([1.0, 4.0, -0.2], dtype=np.float32)
    norm_r = wrapped_env.reward(raw_r)

    expected = np.array([2.0, 2.0, -2.0], dtype=np.float32)
    np.testing.assert_allclose(norm_r, expected, atol=1e-5)
    wrapped_env.close()


def test_reward_normalize_wrapper_clipping():
    """Verify MORewardNormalizeWrapper clipping bounds."""
    env = make_mo_env("minecart-v0", seed=42)
    wrapped_env = MORewardNormalizeWrapper(
        env,
        scale_vector=[1.0, 1.0, 1.0],
        clip_range=(-1.0, 1.0)
    )

    raw_r = np.array([5.0, -10.0, 0.5], dtype=np.float32)
    clipped_r = wrapped_env.reward(raw_r)

    expected = np.array([1.0, -1.0, 0.5], dtype=np.float32)
    np.testing.assert_allclose(clipped_r, expected, atol=1e-5)
    wrapped_env.close()


def test_apply_dynamics_shift_lunarlander():
    """Verify dynamics shifts change physics parameters on Box2D lunar lander."""
    env = make_mo_env("mo-lunar-lander-v2", seed=42)

    # 1. Nominal
    apply_dynamics_shift(env, "nominal")
    unwrapped = env.unwrapped
    assert unwrapped.gravity == -10.0
    assert unwrapped.enable_wind is False

    # 2. Heavy gravity
    apply_dynamics_shift(env, "heavy_gravity")
    assert unwrapped.gravity == -15.0

    # 3. Strong wind
    apply_dynamics_shift(env, "strong_wind")
    assert unwrapped.gravity == -10.0
    assert unwrapped.enable_wind is True
    assert unwrapped.wind_power == 15.0
    assert unwrapped.turbulence_power == 0.5

    # 4. Extreme turbulence
    apply_dynamics_shift(env, "extreme_turbulence")
    assert unwrapped.gravity == -8.0
    assert unwrapped.enable_wind is True
    assert unwrapped.wind_power == 20.0
    assert unwrapped.turbulence_power == 1.5

    env.close()


def test_apply_dynamics_shift_minecart():
    """Verify dynamics shifts for minecart environment and reward wrapper."""
    env = make_mo_env("minecart-v0", seed=42)

    # High friction shift
    shift_cfg = apply_dynamics_shift(env, "high_friction")
    assert shift_cfg["fuel_cost_multiplier"] == 1.5

    # Reward wrapper scaling for minecart
    wrapper = MODynamicsShiftRewardWrapper(env, "high_friction")
    raw_reward = np.array([1.0, 2.0, -0.1], dtype=np.float32)
    shifted_reward = wrapper.reward(raw_reward)

    expected = np.array([1.0, 2.0, -0.15], dtype=np.float32)
    np.testing.assert_allclose(shifted_reward, expected, atol=1e-5)

    # Low ore yield shift
    wrapper_ore = MODynamicsShiftRewardWrapper(env, "low_ore_yield")
    shifted_ore = wrapper_ore.reward(raw_reward)
    expected_ore = np.array([0.7, 1.4, -0.1], dtype=np.float32)
    np.testing.assert_allclose(shifted_ore, expected_ore, atol=1e-5)

    env.close()


def test_env_configs_exist_and_valid():
    """Verify YAML configuration files for environments are valid and complete."""
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    lunar_cfg_path = os.path.join(root_dir, "configs", "env", "lunarlander.yaml")
    minecart_cfg_path = os.path.join(root_dir, "configs", "env", "minecart.yaml")

    assert os.path.exists(lunar_cfg_path), f"Missing {lunar_cfg_path}"
    assert os.path.exists(minecart_cfg_path), f"Missing {minecart_cfg_path}"

    with open(lunar_cfg_path, "r", encoding="utf-8") as f:
        lunar_cfg = yaml.safe_load(f)
    assert lunar_cfg["state_dim"] == 8
    assert lunar_cfg["action_dim"] == 4
    assert lunar_cfg["reward_dim"] == 4
    assert len(lunar_cfg["reward_scale"]) == 4
    assert len(lunar_cfg["ref_point"]) == 4

    with open(minecart_cfg_path, "r", encoding="utf-8") as f:
        minecart_cfg = yaml.safe_load(f)
    assert minecart_cfg["state_dim"] == 7
    assert minecart_cfg["action_dim"] == 6
    assert minecart_cfg["reward_dim"] == 3
    assert len(minecart_cfg["reward_scale"]) == 3
    assert len(minecart_cfg["ref_point"]) == 3


def test_morl_baseline_runner_interface():
    """Verify MORLBaselineRunner initialization and algorithm routing."""
    runner_env = MORLBaselineRunner(
        algo_name="envelope",
        env_id="minecart-v0",
        seed=123,
        device="cpu"
    )
    assert runner_env.algo_name == "envelope"
    assert runner_env.env_id == "minecart-v0"
    assert len(runner_env.ref_point) == 3

    runner_gpi = MORLBaselineRunner(
        algo_name="gpi-ls",
        env_id="mo-lunar-lander-v2",
        seed=123,
        device="cpu"
    )
    assert runner_gpi.algo_name == "gpi-ls"
    assert len(runner_gpi.ref_point) == 4

    runner_uniform = MORLBaselineRunner(
        algo_name="uniform-pcqn",
        env_id="minecart-v0",
        seed=123,
        device="cpu"
    )
    assert runner_uniform.algo_name == "uniform-pcqn"

    with pytest.raises(ValueError):
        MORLBaselineRunner(algo_name="non_existent_algo")


def test_morl_baseline_smoke_training():
    """Smoke test running 10 steps of Envelope and GPILS to guarantee runtime stability."""
    runner_env = MORLBaselineRunner(
        algo_name="envelope",
        env_id="minecart-v0",
        seed=42,
        device="cpu",
        extra_kwargs={"learning_starts": 5, "buffer_size": 100}
    )
    agent_env = runner_env.train(total_timesteps=10, eval_freq=100)
    assert agent_env is not None

    runner_gpi = MORLBaselineRunner(
        algo_name="gpi-ls",
        env_id="minecart-v0",
        seed=42,
        device="cpu",
        extra_kwargs={"learning_starts": 5, "buffer_size": 100}
    )
    agent_gpi = runner_gpi.train(total_timesteps=10, eval_freq=100)
    assert agent_gpi is not None

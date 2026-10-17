from __future__ import annotations

from typing import Any

import numpy as np

from src.envs.wrapper import make_mo_env


def run_envelope_baseline(
    env_id: str,
    ref_point: np.ndarray,
    seed: int = 42,
    total_timesteps: int = 500_000,
    eval_freq: int = 25_000,
    wandb_project: str | None = None,
    reward_scale: np.ndarray | None = None,
    agent_kwargs: dict[str, Any] | None = None,
) -> Any:
    """Run MORL-Baselines 1.3 Envelope under an explicit interaction budget."""
    try:
        from morl_baselines.multi_policy.envelope.envelope import Envelope
    except ImportError as error:
        raise RuntimeError("Install the pinned MORL baseline dependencies before running baselines") from error

    env = make_mo_env(env_id, seed=seed, reward_scale=reward_scale)
    eval_env = make_mo_env(env_id, seed=seed + 1_000_000, reward_scale=reward_scale)
    agent = Envelope(
        env=env,
        project_name=wandb_project or "REL301m-MORL",
        experiment_name=f"envelope_{env_id}_seed{seed}",
        log=wandb_project is not None,
        seed=seed,
        **(agent_kwargs or {}),
    )
    initial_parameters = [parameter.detach().clone() for parameter in agent.q_net.parameters()]
    agent.train(
        total_timesteps=total_timesteps,
        eval_env=eval_env,
        ref_point=np.asarray(ref_point, dtype=np.float32),
        eval_freq=eval_freq,
    )
    final_parameters = [parameter.detach() for parameter in agent.q_net.parameters()]
    agent.rel301m_run_summary = {
        "global_step": int(agent.global_step),
        "episodes": int(agent.num_episodes),
        "replay_size": len(agent.replay_buffer),
        "parameters_changed": any(
            not np.array_equal(before.cpu().numpy(), after.cpu().numpy())
            for before, after in zip(initial_parameters, final_parameters, strict=True)
        ),
    }
    env.close()
    eval_env.close()
    return agent


def run_gpi_ls_baseline(
    env_id: str,
    ref_point: np.ndarray,
    seed: int = 42,
    total_timesteps: int = 500_000,
    eval_freq: int = 25_000,
    wandb_project: str | None = None,
    reward_scale: np.ndarray | None = None,
    timesteps_per_iter: int = 10_000,
    num_eval_episodes_for_front: int = 5,
    checkpoints: bool = False,
    agent_kwargs: dict[str, Any] | None = None,
) -> Any:
    """Run MORL-Baselines 1.3 GPILS under an explicit interaction budget."""
    try:
        from morl_baselines.multi_policy.gpi_pd.gpi_pd import GPILS
    except ImportError as error:
        raise RuntimeError("Install the pinned MORL baseline dependencies before running baselines") from error

    env = make_mo_env(env_id, seed=seed, reward_scale=reward_scale)
    eval_env = make_mo_env(env_id, seed=seed + 1_000_000, reward_scale=reward_scale)
    agent = GPILS(
        env=env,
        project_name=wandb_project or "REL301m-MORL",
        experiment_name=f"gpi_ls_{env_id}_seed{seed}",
        log=wandb_project is not None,
        seed=seed,
        **(agent_kwargs or {}),
    )
    initial_parameters = [parameter.detach().clone() for network in agent.q_nets for parameter in network.parameters()]
    agent.train(
        total_timesteps=total_timesteps,
        eval_env=eval_env,
        ref_point=np.asarray(ref_point, dtype=np.float32),
        eval_freq=eval_freq,
        eval_mo_freq=eval_freq,
        weight_selection_algo="gpi-ls",
        timesteps_per_iter=timesteps_per_iter,
        num_eval_episodes_for_front=num_eval_episodes_for_front,
        checkpoints=checkpoints,
    )
    final_parameters = [parameter.detach() for network in agent.q_nets for parameter in network.parameters()]
    agent.rel301m_run_summary = {
        "global_step": int(agent.global_step),
        "episodes": int(agent.num_episodes),
        "replay_size": len(agent.replay_buffer),
        "parameters_changed": any(
            not np.array_equal(before.cpu().numpy(), after.cpu().numpy())
            for before, after in zip(initial_parameters, final_parameters, strict=True)
        ),
    }
    env.close()
    eval_env.close()
    return agent

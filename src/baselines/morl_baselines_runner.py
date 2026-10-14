from __future__ import annotations

from typing import Any

import numpy as np


def run_envelope_baseline(
    env_id: str,
    ref_point: np.ndarray,
    seed: int = 42,
    total_timesteps: int = 500_000,
    eval_freq: int = 25_000,
    wandb_project: str | None = None,
) -> Any:
    """Run MORL-Baselines 1.3 Envelope under an explicit interaction budget."""
    try:
        import mo_gymnasium as mo_gym
        from morl_baselines.multi_policy.envelope.envelope import Envelope
    except ImportError as error:
        raise RuntimeError("Install the pinned MORL baseline dependencies before running baselines") from error

    env = mo_gym.make(env_id)
    eval_env = mo_gym.make(env_id)
    agent = Envelope(
        env=env,
        project_name=wandb_project or "REL301m-MORL",
        experiment_name=f"envelope_{env_id}_seed{seed}",
        log=wandb_project is not None,
        seed=seed,
    )
    agent.train(
        total_timesteps=total_timesteps,
        eval_env=eval_env,
        ref_point=np.asarray(ref_point, dtype=np.float32),
        eval_freq=eval_freq,
    )
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
) -> Any:
    """Run MORL-Baselines 1.3 GPILS under an explicit interaction budget."""
    try:
        import mo_gymnasium as mo_gym
        from morl_baselines.multi_policy.gpi_pd.gpi_pd import GPILS
    except ImportError as error:
        raise RuntimeError("Install the pinned MORL baseline dependencies before running baselines") from error

    env = mo_gym.make(env_id)
    eval_env = mo_gym.make(env_id)
    agent = GPILS(
        env=env,
        project_name=wandb_project or "REL301m-MORL",
        experiment_name=f"gpi_ls_{env_id}_seed{seed}",
        log=wandb_project is not None,
        seed=seed,
    )
    agent.train(
        total_timesteps=total_timesteps,
        eval_env=eval_env,
        ref_point=np.asarray(ref_point, dtype=np.float32),
        eval_freq=eval_freq,
        eval_mo_freq=eval_freq,
        weight_selection_algo="gpi-ls",
    )
    env.close()
    eval_env.close()
    return agent

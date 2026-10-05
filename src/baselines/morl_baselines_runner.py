import os
from typing import Optional

def run_envelope_baseline(
    env_id: str,
    seed: int = 42,
    total_timesteps: int = 500000,
    wandb_project: Optional[str] = None
):
    """
    Runs Envelope Q-Learning from morl-baselines with comparable interaction budget.
    """
    try:
        from morl_baselines.single_policy.ser.envelope import Envelope
        import mo_gymnasium as mo_gym
    except ImportError:
        raise ImportError("morl-baselines and mo-gymnasium are required to run the Envelope baseline.")

    env = mo_gym.make(env_id)
    eval_env = mo_gym.make(env_id)

    agent = Envelope(
        env=env,
        log=bool(wandb_project),
        project_name=wandb_project or "REL301m-MORL",
        seed=seed,
    )

    agent.train(
        total_timesteps=total_timesteps,
        eval_env=eval_env,
        ref_point=None,
    )
    return agent

def run_gpi_ls_baseline(
    env_id: str,
    seed: int = 42,
    total_timesteps: int = 500000,
    wandb_project: Optional[str] = None
):
    """
    Runs GPI-LS (Generalized Policy Improvement with Linear Support) baseline.
    """
    try:
        from morl_baselines.multi_policy.gpi_pd.gpi_agent_ls import GPIAgentLS
        import mo_gymnasium as mo_gym
    except ImportError:
        raise ImportError("morl-baselines and mo-gymnasium are required to run the GPI-LS baseline.")

    env = mo_gym.make(env_id)
    eval_env = mo_gym.make(env_id)

    agent = GPIAgentLS(
        env=env,
        log=bool(wandb_project),
        project_name=wandb_project or "REL301m-MORL",
        seed=seed,
    )

    agent.train(
        total_timesteps=total_timesteps,
        eval_env=eval_env,
        ref_point=None,
    )
    return agent

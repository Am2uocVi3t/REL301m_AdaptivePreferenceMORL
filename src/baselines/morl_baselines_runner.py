import os
import sys
import numpy as np
from typing import Optional, Dict, Any, List, Union

try:
    from morl_baselines.multi_policy.envelope.envelope import Envelope
except ImportError:
    try:
        from morl_baselines.single_policy.ser.envelope import Envelope
    except ImportError:
        Envelope = None

try:
    from morl_baselines.multi_policy.gpi_pd.gpi_pd import GPILS as GPIAgentLS
except ImportError:
    try:
        from morl_baselines.multi_policy.gpi_pd.gpi_agent_ls import GPIAgentLS
    except ImportError:
        GPIAgentLS = None

from src.envs.wrapper import make_mo_env


class MORLBaselineRunner:
    """
    Standardized runner for Multi-Objective Reinforcement Learning baselines.
    Supports Envelope Q-Learning, GPI-LS, and Uniform-PCQN with a unified training interface.
    """
    def __init__(
        self,
        algo_name: str,
        env_id: str = "mo-lunar-lander-v2",
        seed: int = 42,
        device: str = "cpu",
        wandb_project: Optional[str] = None,
        extra_kwargs: Optional[Dict[str, Any]] = None
    ):
        self.algo_name = algo_name.lower().replace("_", "-")
        supported_algos = ["envelope", "gpi-ls", "gpils", "uniform-pcqn"]
        if self.algo_name not in supported_algos:
            raise ValueError(
                f"Unknown baseline algorithm '{self.algo_name}'. Choose from: 'envelope', 'gpi-ls', 'uniform-pcqn'."
            )
        self.env_id = env_id
        self.seed = seed
        self.device = device
        self.wandb_project = wandb_project
        self.extra_kwargs = extra_kwargs or {}

        # Default conservative reference points for Hypervolume calculation
        if "lunar" in self.env_id.lower():
            self.ref_point = np.array([-100.0, -100.0, -100.0, -100.0], dtype=np.float32)
        else:
            self.ref_point = np.array([-10.0, -10.0, -100.0], dtype=np.float32)

        self.agent = None

    def train(
        self,
        total_timesteps: int = 500000,
        eval_freq: int = 25000,
        eval_episodes: int = 5,
        ref_point: Optional[Union[List[float], np.ndarray]] = None
    ):
        """
        Executes baseline training for the requested number of interaction steps.
        """
        if ref_point is not None:
            self.ref_point = np.asarray(ref_point, dtype=np.float32)

        env = make_mo_env(self.env_id, seed=self.seed)
        eval_env = make_mo_env(self.env_id, seed=self.seed + 1000)

        if self.algo_name == "envelope":
            if Envelope is None:
                raise ImportError("morl-baselines is required to run the Envelope baseline.")

            # Turn off per to ensure torch 2.x tensor conversion stability
            envelope_kwargs = {
                "per": False,
                "learning_starts": min(5000, max(10, total_timesteps // 50)),
                "buffer_size": min(200000, max(100, total_timesteps)),
            }
            envelope_kwargs.update(self.extra_kwargs)

            self.agent = Envelope(
                env=env,
                log=bool(self.wandb_project),
                project_name=self.wandb_project or "REL301m-MORL",
                seed=self.seed,
                device=self.device,
                **envelope_kwargs
            )
            self.agent.train(
                total_timesteps=total_timesteps,
                eval_env=eval_env,
                ref_point=self.ref_point,
                eval_freq=eval_freq
            )
            return self.agent

        elif self.algo_name in ["gpi-ls", "gpils"]:
            if GPIAgentLS is None:
                raise ImportError("morl-baselines is required to run the GPI-LS baseline.")

            gpi_kwargs = {
                "learning_starts": min(5000, max(10, total_timesteps // 50)),
                "buffer_size": min(200000, max(100, total_timesteps)),
            }
            gpi_kwargs.update(self.extra_kwargs)

            self.agent = GPIAgentLS(
                env=env,
                log=bool(self.wandb_project),
                project_name=self.wandb_project or "REL301m-MORL",
                seed=self.seed,
                device=self.device,
                **gpi_kwargs
            )
            self.agent.train(
                total_timesteps=total_timesteps,
                eval_env=eval_env,
                ref_point=self.ref_point,
                eval_freq=eval_freq
            )
            return self.agent

        elif self.algo_name == "uniform-pcqn":
            # Uniform-PCQN baseline is trained using scripts/train.py with algo="uniform-pcqn"
            import subprocess
            cmd = [
                sys.executable,
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "scripts", "train.py"),
                "--env", self.env_id,
                "--algo", "uniform-pcqn",
                "--seed", str(self.seed),
                "--total-timesteps", str(total_timesteps),
                "--eval-freq", str(eval_freq),
                "--eval-episodes", str(eval_episodes),
                "--device", self.device
            ]
            if not self.wandb_project:
                cmd.extend(["--wandb-project", ""])
            subprocess.run(cmd, check=True)
            return True

        else:
            raise ValueError(f"Unknown baseline algorithm '{self.algo_name}'. Choose from: 'envelope', 'gpi-ls', 'uniform-pcqn'.")


def run_envelope_baseline(
    env_id: str = "mo-lunar-lander-v2",
    seed: int = 42,
    total_timesteps: int = 500000,
    wandb_project: Optional[str] = None,
    device: str = "cpu",
    **kwargs
):
    """
    Runs Envelope Q-Learning from morl-baselines with comparable interaction budget.
    """
    runner = MORLBaselineRunner(
        algo_name="envelope",
        env_id=env_id,
        seed=seed,
        device=device,
        wandb_project=wandb_project,
        extra_kwargs=kwargs
    )
    return runner.train(total_timesteps=total_timesteps)


def run_gpi_ls_baseline(
    env_id: str = "mo-lunar-lander-v2",
    seed: int = 42,
    total_timesteps: int = 500000,
    wandb_project: Optional[str] = None,
    device: str = "cpu",
    **kwargs
):
    """
    Runs GPI-LS (Generalized Policy Improvement with Linear Support) baseline.
    """
    runner = MORLBaselineRunner(
        algo_name="gpi-ls",
        env_id=env_id,
        seed=seed,
        device=device,
        wandb_project=wandb_project,
        extra_kwargs=kwargs
    )
    return runner.train(total_timesteps=total_timesteps)


def run_uniform_pcqn_baseline(
    env_id: str = "mo-lunar-lander-v2",
    seed: int = 42,
    total_timesteps: int = 500000,
    wandb_project: Optional[str] = None,
    device: str = "cpu",
    **kwargs
):
    """
    Runs Uniform-PCQN (Uniform preference sampling baseline without adaptive curriculum).
    """
    runner = MORLBaselineRunner(
        algo_name="uniform-pcqn",
        env_id=env_id,
        seed=seed,
        device=device,
        wandb_project=wandb_project,
        extra_kwargs=kwargs
    )
    return runner.train(total_timesteps=total_timesteps)

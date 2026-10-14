import os
from typing import Any


class ExperimentLogger:
    """
    Unified Experiment Tracking Logger supporting:
    1. Weights & Biases (WandB) for remote Cloud tracking (ideal for Kaggle)
    2. TensorBoard for local tracking
    3. Console stdout fallback
    """

    def __init__(
        self,
        project_name: str = "REL301m-AdaptivePreferenceMORL",
        experiment_name: str | None = None,
        config: dict[str, Any] | None = None,
        use_wandb: bool = True,
        use_tensorboard: bool = True,
        log_dir: str = "logs",
    ):
        self.use_wandb = use_wandb
        self.use_tensorboard = use_tensorboard
        self.wandb_run = None
        self.tb_writer = None

        # 1. Initialize WandB if requested
        if self.use_wandb:
            try:
                import wandb

                self.wandb = wandb
                self.wandb_run = wandb.init(
                    project=project_name,
                    name=experiment_name,
                    config=config or {},
                    reinit=True,
                )
            except Exception as e:  # noqa: BLE001 - optional remote logger must fail open
                print(f"[Logger Warning] Could not initialize WandB: {e}. Falling back.")
                self.use_wandb = False

        # 2. Initialize TensorBoard if requested
        if self.use_tensorboard:
            try:
                from torch.utils.tensorboard import SummaryWriter

                os.makedirs(log_dir, exist_ok=True)
                tb_path = os.path.join(log_dir, experiment_name or "run")
                self.tb_writer = SummaryWriter(log_dir=tb_path)
            except Exception as e:  # noqa: BLE001 - optional local logger must fail open
                print(f"[Logger Warning] Could not initialize TensorBoard: {e}.")
                self.use_tensorboard = False

    def log(self, metrics: dict[str, Any], step: int):
        """Log a dictionary of scalar metrics at a specific environment step."""
        if self.use_wandb and self.wandb_run is not None:
            self.wandb.log(metrics, step=step)

        if self.use_tensorboard and self.tb_writer is not None:
            for k, v in metrics.items():
                if isinstance(v, (int, float)):
                    self.tb_writer.add_scalar(k, v, global_step=step)

    def finish(self):
        """Close loggers cleanly."""
        if self.use_wandb and self.wandb_run is not None:
            self.wandb_run.finish()

        if self.use_tensorboard and self.tb_writer is not None:
            self.tb_writer.close()

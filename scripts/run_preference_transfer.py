"""P1: frozen-model approximate GPI by a fixed source preference bank."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import torch

from scripts.diagnose_policy_extraction import read, rollout, sha
from src.curriculum.sampler import AdaptivePreferenceSampler
from src.evaluation.protocol import load_protocol, resolve_reward_scale
from src.models.q_network import VectorQNetwork
from src.utils.provenance import collect_provenance
from src.utils.training_recovery import atomic_json, process_lease

PLAN = Path("configs/experiments/preference_transfer_p1_v1.json")
ROOT = Path("artifacts/preference-transfer-p1-v1")


class GPIMeanQ(VectorQNetwork):
    """Return per-action source-policy vectors chosen by the target utility.

    No coordinate-wise maxima: each action selects ONE source preference from
    the head-mean scalarized value, then keeps all heads' vectors at that source.
    Existing rollout mean/vector arithmetic is consequently unchanged. This is
    an approximate inference adapter, not a learned or certified policy value.
    """

    source_bank: torch.Tensor

    def __init__(self, base: VectorQNetwork, bank: torch.Tensor):
        torch.nn.Module.__init__(self)
        if bank.ndim != 2 or bank.shape[1] != base.reward_dim or len(bank) == 0:
            raise ValueError("Source preferences must be a nonempty reward-dimensional matrix")
        if (
            not torch.isfinite(bank).all()
            or (bank < 0).any()
            or not torch.allclose(bank.sum(-1), torch.ones_like(bank[:, 0]))
        ):
            raise ValueError("Source preferences must be finite simplex weights")
        self.base = base
        self.register_buffer("source_bank", bank.detach().clone())
        self.state_dim = base.state_dim
        self.action_dim = base.action_dim
        self.reward_dim = base.reward_dim
        self.num_heads = base.num_heads

    def forward(self, state: torch.Tensor, preference: torch.Tensor) -> torch.Tensor:
        batch, bank_size = len(state), len(self.source_bank)
        states = state[:, None, :].expand(-1, bank_size, -1).reshape(-1, self.state_dim)
        weights = self.source_bank[None].expand(batch, -1, -1).reshape(-1, self.reward_dim)
        q = self.base(states, weights).reshape(self.num_heads, batch, bank_size, self.action_dim, self.reward_dim)
        # Matmul preserves the existing head-mean then scalarize convention.
        utility = torch.matmul(q.mean(0), preference[:, None, :, None]).squeeze(-1)
        source_index = utility.argmax(1)
        return q.gather(
            2, source_index[None, :, None, :, None].expand(self.num_heads, -1, 1, -1, self.reward_dim)
        ).squeeze(2)


def source_bank(protocol: dict[str, Any]) -> np.ndarray:
    pool = protocol["training_preference_pool"]
    return AdaptivePreferenceSampler(
        protocol["reward_dim"], pool_size=pool["count"], seed=0, pool_seed=pool["seed"]
    ).pool.copy()


def run(name: str, device: str, qualify: bool = False) -> None:
    plan = read(PLAN)
    assert all(sha(Path(path)) == expected for path, expected in plan["protocol_sha256"].items())
    if not qualify and subprocess.check_output(["git", "status", "--porcelain"], text=True).strip():
        raise ValueError("P1 evidence requires a clean committed tree")
    spec = next(s for s in plan["models"] if s["name"] == name)
    directory = ROOT / ("qualification" if qualify else "runs") / name
    directory.mkdir(parents=True, exist_ok=True)
    with process_lease(directory / "worker.lock"):
        if any(p.name != "worker.lock" for p in directory.iterdir()):
            raise ValueError("Do not overwrite or automatically retry P1")
        assert sha(Path(spec["checkpoint"])) == spec["checkpoint_sha256"]
        torch.set_num_threads(1)
        torch.use_deterministic_algorithms(True)
        torch.backends.cudnn.benchmark = False
        checkpoint = torch.load(spec["checkpoint"], map_location="cpu", weights_only=True)
        model = VectorQNetwork(**checkpoint["architecture"]).to(device)
        model.load_state_dict(checkpoint["model_state_dict"])
        model.eval().requires_grad_(False)
        protocol, _ = load_protocol(spec["protocol"], "validation")
        spec = dict(spec, reward_scale=resolve_reward_scale(protocol).tolist())
        bank = source_bank(protocol)
        np.testing.assert_array_equal(bank, plan["source_banks"][spec["env_id"]])
        transferred = GPIMeanQ(model, torch.as_tensor(bank, device=device)).eval().requires_grad_(False)
        start_provenance = collect_provenance({"job": name, "qualify": qualify, "device": device})
        records = []
        seeds = plan["qualification_environment_seeds"] if qualify else plan["development_environment_seeds"]
        for pref_index, preference in enumerate(plan["preferences"][spec["env_id"]]):
            for seed in seeds:
                initial = None
                for policy in plan["policies"]:
                    actor = transferred if policy.startswith("gpi_") else model
                    record = rollout(
                        actor,
                        spec,
                        plan,
                        policy,
                        preference,
                        seed,
                        directory / f"pref{pref_index}_seed{seed}_{policy}.npz",
                        device,
                    )
                    if initial is None:
                        initial = record["initial_state_sha256"]
                    assert initial == record["initial_state_sha256"]
                    record["preference_index"] = pref_index
                    records.append(record)
                atomic_json(
                    directory / "progress.json",
                    {
                        "episodes": len(records),
                        "diagnostic_steps": sum(r["steps"] for r in records),
                        "pid": os.getpid(),
                        "updated_unix": time.time(),
                    },
                )
                print(name, "episodes", len(records), flush=True)
        assert sha(Path(spec["checkpoint"])) == spec["checkpoint_sha256"]
        for key, original in checkpoint["model_state_dict"].items():
            torch.testing.assert_close(model.state_dict()[key].cpu(), original, rtol=0, atol=0)
        end_provenance = collect_provenance({"job": name, "qualify": qualify, "device": device})
        if not qualify:
            assert not start_provenance["git_dirty"] and not end_provenance["git_dirty"]
            assert start_provenance["git_commit"] == end_provenance["git_commit"]
        atomic_json(
            directory / "complete.json",
            {
                "study_id": plan["study_id"],
                "plan_sha256": sha(PLAN),
                "model": spec,
                "provenance": start_provenance,
                "end_provenance": end_provenance,
                "training_interactions": 0,
                "gradient_updates": 0,
                "final_test_steps": 0,
                "diagnostic_steps": sum(r["steps"] for r in records),
                "records": records,
                "source_bank": bank,
                "qualify": qualify,
                "probe_semantics": (
                    "GPI probes retain heads at the selected source weight PER ACTION; not Q(s,a,target)."
                ),
            },
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--job", required=True)
    parser.add_argument("--device", default="cuda", choices=["cuda", "cpu"])
    parser.add_argument("--qualify", action="store_true")
    args = parser.parse_args()
    run(args.job, args.device, args.qualify)

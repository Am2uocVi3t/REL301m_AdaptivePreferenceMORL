"""Fresh-process compatibility and forced-kill/resume witnesses on local CUDA."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import torch

from scripts import run_credit_assignment as legacy
from src.utils.training_recovery import atomic_json

ROOT = Path("artifacts/credit-recovery-qualification-v1")


def read(path: Path) -> Any:
    return json.loads(path.read_text())


def equal_state(a: Any, b: Any) -> None:
    if isinstance(a, torch.Tensor):
        torch.testing.assert_close(a, b, rtol=0, atol=0)
    elif isinstance(a, dict):
        if a.keys() != b.keys():
            raise AssertionError("Checkpoint fields differ")
        for key in a:
            equal_state(a[key], b[key])
    elif isinstance(a, (list, tuple)):
        if len(a) != len(b):
            raise AssertionError("Checkpoint sequence lengths differ")
        for x, y in zip(a, b, strict=True):
            equal_state(x, y)
    elif a != b:
        raise AssertionError("Checkpoint scalar differs")


def compare(left: Path, right: Path, total: int) -> None:
    for name in ("complete.json", "training_episodes.json", "evaluations.json", "losses.json"):
        a, b = read(left / name), read(right / name)
        if name == "complete.json":
            a.pop("wall_seconds")
            b.pop("wall_seconds")
        if a != b:
            raise AssertionError(f"Numerical trace differs: {name}, {left}, {right}")
    a, b = [torch.load(p / f"step{total}.pt", map_location="cpu", weights_only=True) for p in (left, right)]
    equal_state(a, b)


def command(protocol: str, n: int, root: Path, steps: int = 6000) -> list[str]:
    return [
        sys.executable,
        "scripts/run_credit_assignment_recoverable.py",
        "--protocol",
        protocol,
        "--n",
        str(n),
        "--seed",
        "20261511",
        "--smoke",
        "--smoke-steps",
        str(steps),
        "--qualification-root",
        str(root),
    ]


def checked(command_line: list[str], log: Path) -> None:
    with log.open("w", encoding="utf-8") as stream:
        subprocess.run(command_line, stdout=stream, stderr=subprocess.STDOUT, check=True, timeout=180)


def main() -> None:
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--legacy-worker", action="store_true")
    parser.add_argument("--protocol")
    parser.add_argument("--n", type=int)
    parser.add_argument("--root", type=Path)
    args = parser.parse_args()
    if args.legacy_worker:
        legacy.ROOT = args.root
        legacy.run(args.protocol, args.n, 20261511, "cuda", smoke=True)
        return
    ROOT.mkdir(parents=True, exist_ok=False)
    records = []
    plan = read(legacy.PLAN)
    for protocol in plan["protocols"]:
        env_id = read(Path(protocol))["env_id"]
        for n in (1, 20):
            case = ROOT / f"{env_id}_n{n}"
            case.mkdir()
            suffix = Path("smoke") / f"{env_id}_n{n}_seed20261511"
            old, new, continuous, resumed = [case / name for name in ("legacy", "new", "continuous", "resumed")]
            checked(
                [
                    sys.executable,
                    __file__,
                    "--legacy-worker",
                    "--protocol",
                    protocol,
                    "--n",
                    str(n),
                    "--root",
                    str(old),
                ],
                case / "legacy.log",
            )
            checked(command(protocol, n, new), case / "new.log")
            compare(old / suffix, new / suffix, 6000)
            checked(command(protocol, n, continuous, 12000), case / "continuous.log")
            paused_command = [*command(protocol, n, resumed, 12000), "--pause-after", "6500", "--hold-at-boundary"]
            with (case / "interrupted.log").open("w", encoding="utf-8") as stream:
                process = subprocess.Popen(paused_command, stdout=stream, stderr=subprocess.STDOUT)
                try:
                    deadline = time.monotonic() + 180
                    marker = resumed / suffix / "paused.json"
                    while not marker.exists():
                        if process.poll() is not None or time.monotonic() >= deadline:
                            raise RuntimeError("Worker did not reach a held checkpoint; inspect interrupted.log")
                        time.sleep(0.2)
                    with (case / "duplicate.log").open("w", encoding="utf-8") as duplicate_log:
                        duplicate = subprocess.run(
                            [*command(protocol, n, resumed, 12000), "--resume"],
                            stdout=duplicate_log,
                            stderr=subprocess.STDOUT,
                            timeout=60,
                        )
                    if (
                        duplicate.returncode == 0
                        or "An active process owns" not in (case / "duplicate.log").read_text()
                    ):
                        raise AssertionError("Active duplicate was not rejected")
                    subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], check=True, capture_output=True)
                    process.wait(timeout=30)
                finally:
                    if process.poll() is None:
                        subprocess.run(
                            ["taskkill", "/PID", str(process.pid), "/T", "/F"], check=True, capture_output=True
                        )
                        process.wait(timeout=30)
            checked([*command(protocol, n, resumed, 12000), "--resume"], case / "resumed.log")
            compare(continuous / suffix, resumed / suffix, 12000)
            records.append(
                {
                    "env_id": env_id,
                    "n": n,
                    "legacy_compatibility": "exact",
                    "forced_kill_resume": "exact",
                    "duplicate_rejected": True,
                    "boundary_step": read(resumed / suffix / "paused.json")["step"],
                    "directory": str(case),
                }
            )
            print(records[-1], flush=True)
    atomic_json(
        Path("research/qualification/credit_recovery_numerical_v1.json"),
        {
            "status": "pass",
            "device": "cuda",
            "records": records,
            "executed_training_interactions": 144000,
            "qualification_only": True,
            "source_sha256": {
                str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in [
                    Path("scripts/run_credit_assignment_recoverable.py"),
                    Path("src/utils/training_recovery.py"),
                    legacy.PLAN,
                    Path("configs/experiments/credit_assignment_recovery_v1.json"),
                ]
            },
        },
    )


if __name__ == "__main__":
    main()

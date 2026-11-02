"""Three-seed concurrent CUDA exact-kill/resume qualification; no main training."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import torch

from scripts.qualify_minecart_conditional import equal
from scripts.run_minecart_confirmation import PLAN, QUALIFICATION, ROOT, SOURCE, load_state, publish, sha


def launch(seed: int, name: str, extra: list[str]) -> subprocess.Popen:
    root = ROOT / "engineering"
    root.mkdir(parents=True, exist_ok=True)
    with (
        (root / f"{name}.stdout.log").open("a", encoding="utf-8") as out,
        (root / f"{name}.stderr.log").open("a", encoding="utf-8") as err,
    ):
        return subprocess.Popen(
            [
                sys.executable,
                "scripts/run_minecart_confirmation.py",
                "--engineering",
                "--name",
                name,
                "--seed",
                str(seed),
                "--steps",
                "1088",
                "--device",
                "cuda",
                *extra,
            ],
            stdout=out,
            stderr=err,
            creationflags=0x08000000 if os.name == "nt" else 0,
        )


def kill(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], check=True, capture_output=True)
    else:
        process.kill()
    process.wait(timeout=15)


def wait_all(processes: list[subprocess.Popen]) -> None:
    try:
        for process in processes:
            if process.wait(timeout=180) != 0:
                raise RuntimeError("Confirmation qualification failed; inspect engineering stderr")
    finally:
        for process in processes:
            kill(process)


def main() -> None:
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA required")
    plan = json.loads(PLAN.read_text())
    suffix = time.strftime("%Y%m%d-%H%M%S")
    reference_names = [f"reference-{seed}-{suffix}" for seed in plan["seeds"]]
    resumed_names = [f"killed-{seed}-{suffix}" for seed in plan["seeds"]]
    started = time.monotonic()
    references = [launch(seed, name, []) for seed, name in zip(plan["seeds"], reference_names, strict=True)]
    wait_all(references)
    print("Three concurrent reference jobs completed", flush=True)
    children = [
        launch(seed, name, ["--pause-at", "512", "--hold"])
        for seed, name in zip(plan["seeds"], resumed_names, strict=True)
    ]
    try:
        deadline = time.monotonic() + 120
        while not all((ROOT / "engineering" / name / "paused.json").exists() for name in resumed_names):
            if any(p.poll() is not None for p in children) or time.monotonic() > deadline:
                raise RuntimeError("Three workers did not reach durable pause")
            time.sleep(0.1)
    finally:
        for process in children:
            kill(process)
    wait_all([launch(seed, name, ["--resume"]) for seed, name in zip(plan["seeds"], resumed_names, strict=True)])
    runtimes: dict[str, Any] = {}
    hashes = []
    evaluations = 0
    for seed, ref, res in zip(plan["seeds"], reference_names, resumed_names, strict=True):
        a, b = load_state(ROOT / "engineering" / ref), load_state(ROOT / "engineering" / res)
        for key in [
            "binding",
            "learner",
            "environments",
            "observations",
            "rng",
            "counters",
            "episode_state",
            "trace_hash",
            "preferences",
            "initial_parameter_sha256",
        ]:
            equal(a[key], b[key])
        equal(a["histories"][:2], b["histories"][:2])
        assert a["step"] == 1088 and len(a["environments"]) == 8
        assert a["learner"]["actor_updates"] == 96 and a["learner"]["critic_updates"] == 192
        assert a["preferences"]["interaction_counts"].sum() == 1088
        assert a["binding"]["training_seed"] == seed
        runtimes[str(seed)] = {k: v for k, v in a["binding"].items() if k not in ("source", "total")}
        hashes.append(a["initial_parameter_sha256"])
        evaluations += 2 * a["counters"][2]
    assert len(set(hashes)) == 3
    receipt = {
        "status": "pass",
        "scope": "engineering exact-resume/concurrency only; not task competence",
        "source": {p: sha(p) for p in SOURCE},
        "runtime_by_seed": runtimes,
        "qualifier_sha256": sha(__file__),
        "seeds": plan["seeds"],
        "reference_jobs": reference_names,
        "resumed_jobs": resumed_names,
        "concurrent_workers": 3,
        "all_seed_eight_stream_exact": True,
        "killed_at_step": 512,
        "final_partial_batch": 64,
        "distinct_initial_parameter_sha256": hashes,
        "training_interactions": 6528,
        "prior_engineering_interactions": 25472,
        "combined_engineering_interactions": 32000,
        "development_evaluation_steps": evaluations,
        "final_test_steps": 0,
        "wall_seconds": time.monotonic() - started,
        "review_independence": "executor_only",
    }
    publish(QUALIFICATION, receipt)
    print(json.dumps(receipt, indent=2), flush=True)


if __name__ == "__main__":
    main()

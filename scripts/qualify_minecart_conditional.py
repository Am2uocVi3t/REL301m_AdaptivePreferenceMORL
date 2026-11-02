"""Bounded CUDA process-kill/resume qualification, not scientific task evidence."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import torch

from scripts.run_minecart_conditional import QUALIFICATION, ROOT, SOURCE, load_state, publish, sha


def equal(left: Any, right: Any) -> None:
    if isinstance(left, torch.Tensor):
        assert torch.equal(left, right), "Tensor differs across exact resume"
    elif isinstance(left, np.ndarray):
        np.testing.assert_array_equal(left, right)
    elif isinstance(left, dict):
        assert left.keys() == right.keys()
        for key in left:
            equal(left[key], right[key])
    elif isinstance(left, (list, tuple)):
        assert len(left) == len(right)
        for a, b in zip(left, right, strict=True):
            equal(a, b)
    else:
        assert left == right, f"State differs: {left!r} != {right!r}"


def launch(name: str, extra: list[str], wait: bool = True) -> subprocess.Popen:
    root = ROOT / "engineering"
    root.mkdir(parents=True, exist_ok=True)
    with (
        (root / f"{name}.stdout.log").open("a", encoding="utf-8") as out,
        (root / f"{name}.stderr.log").open("a", encoding="utf-8") as err,
    ):
        process = subprocess.Popen(
            [
                sys.executable,
                "scripts/run_minecart_conditional.py",
                "--engineering",
                "--name",
                name,
                "--steps",
                "6208",
                "--device",
                "cuda",
                *extra,
            ],
            stdout=out,
            stderr=err,
            creationflags=0x08000000 if os.name == "nt" else 0,
        )
    if wait and process.wait(timeout=180) != 0:
        raise RuntimeError(f"Qualification process failed; inspect {root}/{name}.stderr.log")
    return process


def main() -> None:
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA qualification required for GPU pilot")
    suffix = time.strftime("%Y%m%d-%H%M%S")
    reference_name, resumed_name = f"reference-{suffix}", f"killed-{suffix}"
    started = time.monotonic()
    launch(reference_name, [])
    child = launch(resumed_name, ["--pause-at", "4096", "--hold"], wait=False)
    paused = ROOT / "engineering" / resumed_name / "paused.json"
    try:
        deadline = time.monotonic() + 120
        while not paused.exists():
            if child.poll() is not None or time.monotonic() > deadline:
                raise RuntimeError("Qualification never reached durable pause")
            time.sleep(0.1)
        # Python venv on Windows redirects to a child interpreter. taskkill /T
        # kills only this explicitly-created qualification process tree.
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(child.pid), "/T", "/F"], check=True, capture_output=True)
        else:
            child.kill()
        child.wait(timeout=15)
    finally:
        if child.poll() is None:
            child.kill()
    launch(resumed_name, ["--resume"])
    reference = load_state(ROOT / "engineering" / reference_name)
    resumed = load_state(ROOT / "engineering" / resumed_name)
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
        equal(reference[key], resumed[key])
    # Losses and completed training returns match; evaluation file paths differ.
    equal(reference["histories"][:2], resumed["histories"][:2])
    completion = json.loads((ROOT / "engineering" / reference_name / "complete.json").read_text())
    assert completion["actor_updates"] == 13 * 32 and completion["critic_updates"] == 13 * 64
    assert completion["training_interactions"] == 6208
    assert len(reference["environments"]) == 8
    assert int(reference["preferences"]["interaction_counts"].sum()) == 6208
    assert int(reference["preferences"]["draw_counts"].sum()) == 8 + len(reference["histories"][0])
    assert (reference["preferences"]["draw_counts"] > 0).sum() > 1
    from scripts.run_minecart_conditional import model_hash, seed_all
    from src.models.onpolicy import ActorCritic

    seed_all(20264111)
    fresh = ActorCritic(width=256).to("cuda")
    assert model_hash(fresh) == reference["initial_parameter_sha256"]
    receipt = {
        "status": "pass",
        "scope": "engineering numerical/CUDA/exact process-kill resume only, not task competence",
        "source": {name: sha(name) for name in SOURCE},
        "runtime": {k: v for k, v in reference["binding"].items() if k not in ("source", "total")},
        "qualifier_sha256": sha(__file__),
        "reference": reference_name,
        "resumed": resumed_name,
        "eight_stream_exact": True,
        "killed_at_step": 4096,
        "final_partial_batch": 64,
        "training_interactions": 12416,
        "prior_S_engineering_interactions": 12928,
        "combined_S_C_engineering_interactions": 25344,
        "preference_rng_and_exposure_exact": True,
        "preference_draws": int(reference["preferences"]["draw_counts"].sum()),
        "pool_count": 32,
        "development_evaluation_steps": 2 * completion["development_evaluation_steps"],
        "final_test_steps": 0,
        "wall_seconds": time.monotonic() - started,
        "training_trace_sha256": reference["trace_hash"],
        "review_independence": "executor_only",
        "task_success_claim": False,
    }
    QUALIFICATION.parent.mkdir(parents=True, exist_ok=True)
    publish(QUALIFICATION, receipt)
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()

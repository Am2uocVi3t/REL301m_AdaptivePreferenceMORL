"""Frozen portable actors at default, uniform and corners; presentation only."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

from scripts.run_minecart_onpolicy import publish, sha
from src.demo.runtime import DemoRuntime, Panel, preference


def main():
    root = Path("outputs/REL301m_Course_Project_20261103_LunarPPO")
    output = Path("artifacts/ppo-demo-preference-diagnosis-v1")
    if output.exists():
        raise ValueError("Preserve completed or partial diagnosis; do not overwrite")
    output.mkdir()
    runtime = DemoRuntime(root)
    records = []
    try:
        for name in ["lunar", "mine"]:
            spec = runtime.specs[name]
            dim = len(spec["default_weights"])
            profiles = [("default", spec["default_weights"]), ("uniform", [1 / dim] * dim)]
            profiles += [(f"corner{i}", np.eye(dim)[i].tolist()) for i in range(dim)]
            model = runtime.model(name)
            for label, weights in profiles:
                for seed in range(20266511, 20266516):
                    panel = Panel({**spec, "seed": seed}, preference(weights, dim))
                    try:
                        while not panel.done:
                            panel.advance(model)
                        if name == "lunar":
                            env: Any = panel.env.unwrapped
                            inside = env.helipad_x1 <= env.lander.position.x <= env.helipad_x2
                            success = bool(panel.terminated and panel.raw[0] > 0 and inside)
                        else:
                            success = bool(np.any(panel.raw[:2] > 0))
                        trace = output / f"{name}-{label}-{seed}.json"
                        publish(trace, {"spec": spec, "seed": seed, "transitions": panel.transitions})
                        records.append(
                            {
                                "environment": name,
                                "profile": label,
                                "seed": seed,
                                "preference": panel.weights.tolist(),
                                "steps": panel.steps,
                                "raw_return": panel.raw.tolist(),
                                "discounted_scaled_return": panel.discounted.tolist(),
                                "utility": float(panel.discounted @ panel.weights),
                                "task_success": success,
                                "terminated": bool(panel.terminated),
                                "truncated": bool(panel.truncated),
                                "trace": str(trace),
                                "trace_sha256": sha(trace),
                            }
                        )
                    finally:
                        panel.close()
                print(f"{name} {label}: {sum(r['task_success'] for r in records[-5:])}/5", flush=True)
        assert len(records) == 55
        publish(
            Path("research/evidence/ppo_demo_preference_diagnosis_v1.json"),
            {
                "scope": (
                    "Presentation diagnostic on frozen actors; no candidate tuning or independent training replication"
                ),
                "package_manifest_sha256": sha(root / "MANIFEST.json"),
                "records": records,
                "diagnostic_steps": sum(r["steps"] for r in records),
                "training_interactions": 0,
                "final_test_steps": 0,
            },
        )
    finally:
        runtime.close()


if __name__ == "__main__":
    main()

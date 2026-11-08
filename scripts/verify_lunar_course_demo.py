"""Run the extracted two-PPO release on real physics, without repository imports."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import torch


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    repo = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    import src.demo.runtime as runtime_module
    from src.demo.runtime import DemoRuntime
    from src.models.onpolicy import ActorCritic

    assert Path(runtime_module.__file__).resolve().is_relative_to(root)
    manifest = json.loads((root / "MANIFEST.json").read_text())
    assert all(digest(root / name) == expected for name, expected in manifest["files"].items())
    runtime = DemoRuntime(root)
    records = []
    args.output.mkdir(parents=True, exist_ok=True)
    try:
        for name, first, other in [("lunar", 20265321, [0.25] * 4), ("mine", 20264431, [0.8, 0.1, 0.1])]:
            spec = runtime.specs[name]
            checkpoint = repo / spec["source_checkpoint"]
            assert digest(checkpoint) == spec["source_sha256"]
            source = torch.load(checkpoint, map_location="cpu", weights_only=False)  # nosec B614: hash-bound local source
            portable = torch.load(root / spec["weights_file"], map_location="cpu", weights_only=True)
            direct = ActorCritic(**portable["architecture"])
            direct.load_state_dict(source["learner"]["model"])
            direct.eval()
            for seed in range(first, first + 10):
                spec["seed"] = seed
                runtime.reset(name, other, runtime.generation)
                while not all(p.done for p in runtime.panels):
                    for panel in runtime.panels:
                        if panel.done:
                            continue
                        with torch.inference_mode():
                            expected = direct.distribution(
                                torch.tensor(panel.observation).unsqueeze(0),
                                torch.tensor(panel.weights).unsqueeze(0),
                            ).probs[0]
                        panel.advance(runtime.model(name))
                        assert panel.action == int(expected.argmax())
                        np.testing.assert_allclose(panel.scores, expected, rtol=1e-6, atol=1e-7)
                for profile, panel in enumerate(runtime.panels):
                    rewards = np.asarray([t["reward"] for t in panel.transitions])
                    np.testing.assert_allclose(rewards.sum(0), panel.raw)
                    discounted = (rewards * spec["gamma"] ** np.arange(panel.steps)[:, None]).sum(0)
                    np.testing.assert_allclose(discounted * spec["reward_scale"], panel.discounted)
                    if name == "lunar":
                        env: Any = panel.env.unwrapped
                        success = bool(
                            panel.terminated
                            and panel.raw[0] > 0
                            and env.helipad_x1 <= env.lander.position.x <= env.helipad_x2
                        )
                    else:
                        success = bool(np.any(panel.raw[:2] > 0))
                    trace = args.output / f"{name}-{seed}-p{profile}.json"
                    trace.write_text(json.dumps(panel.transitions) + "\n", encoding="utf-8")
                    records.append(
                        {
                            "environment": name,
                            "seed": seed,
                            "profile": profile,
                            "preference": panel.weights.tolist(),
                            "steps": panel.steps,
                            "raw_return": panel.raw.tolist(),
                            "discounted_scaled_return": panel.discounted.tolist(),
                            "utility": float(panel.discounted @ panel.weights),
                            "task_success": success,
                            "trace": str(trace),
                            "trace_sha256": digest(trace),
                        }
                    )
                assert all("native_frame" in p for p in runtime.snapshot(native=True)["panels"])
            print(f"{name}: 20 real task cases; portable/source probabilities and actions match", flush=True)
        assert len(records) == 40 and all(r["task_success"] for r in records)
        assert runtime.snapshot()["training_updates"] == 0
        receipt = {
            "status": "pass",
            "scope": (
                "Extracted-package CPU presentation diagnostics; reused development cases, "
                "not independent research replication"
            ),
            "package_root": str(root),
            "package_manifest_sha256": digest(root / "MANIFEST.json"),
            "imports_confined_to_package": True,
            "portable_source_actor_equivalence": True,
            "native_render_both_environments": True,
            "records": records,
            "diagnostic_steps": sum(r["steps"] for r in records),
            "training_interactions": 0,
            "final_test_steps": 0,
        }
        (args.output / "verification.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    finally:
        runtime.close()


if __name__ == "__main__":
    main()

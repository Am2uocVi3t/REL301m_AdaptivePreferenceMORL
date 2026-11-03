"""Verify portable Minecart demo on real physics with actor/source equivalence."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import torch

from scripts.run_minecart_onpolicy import load_state, publish, sha
from src.demo.runtime import DemoRuntime
from src.models.onpolicy import ActorCritic


def main():
    root = Path("outputs/REL301m_Course_Project_20261103")
    manifest = json.loads((root / "MANIFEST.json").read_text())
    assert all(sha(root / name) == expected for name, expected in manifest["files"].items())
    runtime = DemoRuntime(root)
    source = load_state(Path("artifacts/minecart-onpolicy-confirmation-v1/runs/minecart-v0_G_seed20264311"))
    direct = ActorCritic(7, 6, 3, 256)
    direct.load_state_dict(source["learner"]["model"])
    direct.eval()
    records = []
    try:
        for seed in range(20264431, 20264441):
            runtime.specs["mine"]["seed"] = seed
            runtime.reset("mine", [0.8, 0.1, 0.1], runtime.generation)
            while not all(p.done for p in runtime.panels):
                for panel in runtime.panels:
                    if panel.done:
                        continue
                    with torch.no_grad():
                        action = int(
                            direct.distribution(
                                torch.tensor(panel.observation).unsqueeze(0), torch.tensor(panel.weights).unsqueeze(0)
                            ).logits.argmax()
                        )
                    panel.advance(runtime.model("mine"))
                    assert panel.action == action
            for profile, panel in enumerate(runtime.panels):
                rewards = np.asarray([t["reward"] for t in panel.transitions])
                np.testing.assert_allclose(rewards.sum(0), panel.raw)
                records.append(
                    {
                        "seed": seed,
                        "profile": profile,
                        "steps": panel.steps,
                        "raw_return": panel.raw.tolist(),
                        "ore_delivered": bool(np.any(panel.raw[:2] > 0)),
                    }
                )
        assert all(r["ore_delivered"] for r in records)
        rendered = runtime.snapshot(native=True)
        assert all("native_frame" in panel for panel in rendered["panels"])
        assert runtime.snapshot()["training_updates"] == 0
        receipt = {
            "status": "pass",
            "scope": (
                "portable actor/source equivalence,20 real task cases and native rendering; "
                "presentation diagnostic only"
            ),
            "package_manifest_sha256": sha(root / "MANIFEST.json"),
            "records": records,
            "training_interactions": 0,
            "final_test_steps": 0,
        }
        publish(Path("research/qualification/onpolicy_course_demo_20261103.json"), receipt)
        print("Verified20 real demo cases and portable actor equivalence.")
    finally:
        runtime.close()


if __name__ == "__main__":
    main()

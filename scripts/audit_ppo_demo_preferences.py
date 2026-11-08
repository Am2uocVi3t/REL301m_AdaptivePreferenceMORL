"""Replay diagnostic actions in the pinned physics; keep expense separate."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

from scripts.run_minecart_onpolicy import publish, sha
from src.demo.runtime import Panel, preference


def main():
    evidence = Path("research/evidence/ppo_demo_preference_diagnosis_v1.json")
    result = json.loads(evidence.read_text())
    replay_steps = 0
    for row in result["records"]:
        assert sha(row["trace"]) == row["trace_sha256"]
        trace = json.loads(Path(row["trace"]).read_text())
        spec = {**trace["spec"], "seed": row["seed"]}
        panel = Panel(spec, preference(row["preference"], len(row["preference"])))
        try:
            obs = panel.observation
            rewards = []
            assert len(trace["transitions"]) == row["steps"]
            for transition in trace["transitions"]:
                np.testing.assert_array_equal(obs, transition["observation"])
                with panel.rng():
                    obs, reward, terminated, truncated, _ = panel.env.step(transition["action"])
                np.testing.assert_array_equal(obs, transition["next_observation"])
                np.testing.assert_array_equal(reward, transition["reward"])
                assert terminated == transition["terminated"] and truncated == transition["truncated"]
                rewards.append(reward)
            raw = np.asarray(rewards, dtype=np.float64)
            np.testing.assert_allclose(raw.sum(0), row["raw_return"], rtol=1e-12, atol=1e-12)
            discounted = (raw * spec["gamma"] ** np.arange(len(raw))[:, None]).sum(0)
            scaled = discounted * spec["reward_scale"]
            np.testing.assert_allclose(scaled, row["discounted_scaled_return"], rtol=1e-12, atol=1e-12)
            np.testing.assert_allclose(scaled @ row["preference"], row["utility"], rtol=1e-12, atol=1e-12)
            if row["environment"] == "lunar":
                env: Any = panel.env.unwrapped
                success = bool(
                    terminated and raw[:, 0].sum() > 0 and env.helipad_x1 <= env.lander.position.x <= env.helipad_x2
                )
            else:
                success = bool(np.any(raw.sum(0)[:2] > 0))
            assert success == row["task_success"]
            replay_steps += len(raw)
        finally:
            panel.close()
    publish(
        Path("research/qualification/ppo_demo_preference_diagnosis_v1.json"),
        {
            "status": "exact_physics_replay_and_numeric_pass",
            "scope": "Same55 action traces replayed; not new independent cases or training",
            "evidence_sha256": sha(evidence),
            "episodes": len(result["records"]),
            "diagnostic_steps": result["diagnostic_steps"],
            "additional_physics_replay_steps": replay_steps,
            "training_interactions": 0,
            "final_test_steps": 0,
            "review_independence": "executor_only",
        },
    )
    print(f"Verified all55 traces exactly; additional diagnostic replay steps={replay_steps}")


if __name__ == "__main__":
    main()

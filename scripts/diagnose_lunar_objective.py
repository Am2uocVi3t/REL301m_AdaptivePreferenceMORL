"""Paired fixed-controller positive control and objective decomposition on development cases."""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import torch
from gymnasium.envs.box2d.lunar_lander import heuristic

from src.demo.runtime import DemoRuntime, sha256
from src.envs.wrapper import make_mo_env
from src.utils.provenance import collect_provenance, write_json


def main() -> None:
    plan_path = Path("configs/experiments/lunar_objective_diagnosis_v1.json")
    plan = json.loads(plan_path.read_text())
    runtime = DemoRuntime(Path(plan["package"]))
    model = runtime.model("lunar")
    spec = runtime.specs["lunar"]
    torch.set_num_threads(1)
    output = Path("artifacts/lunar-objective-diagnosis-v1")
    output.mkdir(parents=True, exist_ok=True)
    records = []
    for seed in plan["environment_seeds"]:
        initials = []
        for policy in ("default", "landing_heavy", "gymnasium_heuristic"):
            np.random.seed(seed)
            random.seed(seed)
            env = make_mo_env(spec["env_id"], seed=seed, dynamics_shift_config=spec["nominal"])
            obs, _ = env.reset(seed=seed)
            initials.append(np.asarray(obs).copy())
            rewards, states = [], [np.asarray(obs).tolist()]
            actions: list[int] = []
            terminated = truncated = False
            weights = np.asarray(plan["model_preferences"].get(policy) or spec["default_weights"], dtype=np.float32)
            try:
                with torch.inference_mode():
                    while not (terminated or truncated) and len(actions) < plan["max_episode_steps"]:
                        if policy == "gymnasium_heuristic":
                            action = int(heuristic(env, obs))
                        else:
                            action, _ = model.predict_action(
                                torch.as_tensor(obs), torch.as_tensor(weights), head_idx=None
                            )
                        obs, reward, terminated, truncated, _ = env.step(action)
                        actions.append(action)
                        rewards.append(np.asarray(reward).tolist())
                        states.append(np.asarray(obs).tolist())
                native = np.asarray(rewards)
                body: Any = env.unwrapped
                inside = bool(body.helipad_x1 <= body.lander.position.x <= body.helipad_x2)
                raw = native.sum(axis=0)
                scores = {}
                for gamma in plan["counterfactual_rescoring_gammas"]:
                    vector = (native * np.power(gamma, np.arange(len(actions)))[:, None]).sum(axis=0)
                    scaled = vector * np.asarray(spec["reward_scale"])
                    scores[str(gamma)] = {
                        "native_discounted_return": vector,
                        "scaled_discounted_return": scaled,
                        "utilities": {},
                    }
                    for label, supplied in plan["model_preferences"].items():
                        w = np.asarray(supplied or spec["default_weights"])
                        contributions = scaled * w
                        scores[str(gamma)]["utilities"][label] = {
                            "per_objective_contributions": contributions,
                            "total": float(contributions.sum()),
                        }
                record = {
                    "seed": seed,
                    "policy": policy,
                    "steps": len(actions),
                    "native_raw_return": raw,
                    "terminated": bool(terminated),
                    "truncated": bool(truncated),
                    "inside_pad_x": inside,
                    "native_plus100": bool(raw[0] > 0 and terminated),
                    "game_over": bool(body.game_over),
                    "contact": [bool(leg.ground_contact) for leg in body.legs],
                    "scores": scores,
                }
                trace = output / f"{policy}_seed{seed}.json"
                write_json(trace, {"summary": record, "actions": actions, "states": states, "native_rewards": native})
                record["trace"] = str(trace)
                record["trace_sha256"] = sha256(trace)
                records.append(record)
                print(
                    f"{policy} seed={seed} steps={len(actions)} +100={record['native_plus100']} pad={inside}",
                    flush=True,
                )
            finally:
                env.close()
        for initial in initials[1:]:
            np.testing.assert_array_equal(initial, initials[0])
    result = {
        "study_id": plan["study_id"],
        "plan_sha256": sha256(plan_path),
        "plan": plan,
        "provenance": collect_provenance(plan),
        "model_sha256": spec["weights_sha256"],
        "training_interactions": 0,
        "final_test_steps": 0,
        "diagnostic_steps": sum(record["steps"] for record in records),
        "records": records,
    }
    path = Path("research/evidence/lunar_objective_diagnosis_v1.json")
    write_json(path, result)
    path.write_bytes(path.read_bytes().replace(b"\r\n", b"\n"))
    runtime.close()


if __name__ == "__main__":
    main()

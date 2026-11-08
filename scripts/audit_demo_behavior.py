"""Run the delivered frozen policies across a fixed preference/seed diagnostic matrix."""

from __future__ import annotations

import base64
import copy
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import torch

from src.demo.runtime import DemoRuntime, Panel, preference, sha256
from src.utils.provenance import collect_provenance, write_json

ROOT = Path(__file__).resolve().parents[1]


def position(panel: Panel, name: str) -> list[float]:
    env: Any = panel.env.unwrapped
    return list(env.lander.position) if name == "lunar" else env.cart.pos.tolist()


def run() -> dict[str, Any]:
    plan_path = ROOT / "configs/demos/behavior_audit_v1.json"
    plan = json.loads(plan_path.read_text())
    package = ROOT / plan["package"]
    for relative in ("src/demo/runtime.py", "src/envs/wrapper.py", "src/models/q_network.py"):
        if sha256(ROOT / relative) != sha256(package / relative):
            raise ValueError(f"Diagnostic runtime differs from the actual app: {relative}")
    output = ROOT / "artifacts/demo-behavior-audit-v1"
    output.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(1)
    runtime = DemoRuntime(package)
    episodes = []
    sensitivity = {}
    env: Any
    for name, cases in plan["environments"].items():
        model = runtime.model(name)
        before = {key: value.clone() for key, value in model.state_dict().items()}
        spec = runtime.specs[name]
        if spec["weights_sha256"] != cases["weights_sha256"]:
            raise ValueError("Frozen presentation checkpoint changed")
        probes = []
        for offset in plan["seed_offsets"]:
            for label, supplied_weights in cases["preferences"].items():
                weights = preference(supplied_weights or spec["default_weights"], len(spec["default_weights"]))
                case_spec = copy.deepcopy(spec)
                case_spec["seed"] = spec["seed"] + offset
                panel = Panel(case_spec, weights)
                path = [position(panel, name)]
                cargo_max = np.zeros(2)
                departed = visited_mine = False
                try:
                    while not panel.done:
                        if label == "default" and panel.steps % 10 == 0:
                            probes.append(np.asarray(panel.observation).copy())
                        panel.advance(model)
                        path.append(position(panel, name))
                        if name == "mine":
                            env = panel.env.unwrapped
                            cargo_max = np.maximum(cargo_max, env.cart.content)
                            departed = departed or bool(env.cart.departed)
                            visited_mine = visited_mine or any(mine.mineable(env.cart) for mine in env.mines)
                    result = panel.snapshot()
                    result["case"] = label
                    result["environment"] = name
                    result["seed"] = case_spec["seed"]
                    result["action_counts"] = np.bincount(
                        [transition["action"] for transition in panel.transitions], minlength=len(spec["actions"])
                    ).tolist()
                    if name == "lunar":
                        env = panel.env.unwrapped
                        result["environment_reported_landing"] = bool(panel.terminated and panel.raw[0] > 0)
                        result["environment_reported_crash_or_out_of_bounds"] = bool(
                            panel.terminated and panel.raw[0] < 0
                        )
                        result["game_over"] = bool(env.game_over)
                        result["inside_pad_x"] = bool(env.helipad_x1 <= env.lander.position.x <= env.helipad_x2)
                    else:
                        result["departed_base"] = departed
                        result["visited_mine_radius"] = visited_mine
                        result["maximum_cargo"] = cargo_max.tolist()
                        result["delivered_positive_ore"] = (panel.raw[:2] > 0).tolist()
                    trace = output / f"{name}_{label}_seed{case_spec['seed']}.json"
                    write_json(trace, {"summary": result, "positions": path, "transitions": panel.transitions})
                    result["trace"] = str(trace.relative_to(ROOT))
                    result["trace_sha256"] = sha256(trace)
                    if offset == 0:
                        image_path = output / f"{name}_{label}_native.jpg"
                        image_path.write_bytes(base64.b64decode(panel.snapshot(native=True)["native_frame"]))
                    episodes.append(result)
                    print(
                        f"{name} {label} seed={case_spec['seed']} steps={panel.steps} raw={panel.raw.tolist()}",
                        flush=True,
                    )
                finally:
                    panel.close()
        observations = torch.as_tensor(np.asarray(probes), dtype=torch.float32)
        actions, scores = {}, {}
        with torch.inference_mode():
            for label, supplied in cases["preferences"].items():
                weights_tensor = torch.as_tensor(supplied or spec["default_weights"], dtype=torch.float32)
                weights_tensor = weights_tensor.repeat(len(observations), 1)
                q_values = model(observations, weights_tensor).mean(dim=0)
                scalarized = (q_values * weights_tensor[:, None, :]).sum(dim=-1)
                actions[label] = scalarized.argmax(dim=-1).numpy()
                scores[label] = scalarized.numpy()
        baseline = actions["default"]
        sensitivity[name] = {
            "probe_source": "Every tenth observation on all five default-preference trajectories only",
            "same_state_probes": len(probes),
            "different_action_fraction_vs_default": {
                label: float(np.mean(values != baseline)) for label, values in actions.items()
            },
            "maximum_score_change_vs_default": {
                label: float(np.max(np.abs(values - scores["default"]))) for label, values in scores.items()
            },
        }
        write_json(
            output / f"{name}_same_state_probes.json",
            {"observations": observations.numpy(), "actions": actions, "scores": scores},
        )
        if not all(torch.equal(value, before[key]) for key, value in model.state_dict().items()):
            raise ValueError("Inference modified frozen model parameters")
    runtime.close()
    payload = {
        "schema_version": 1,
        "purpose": plan["purpose"],
        "plan_sha256": sha256(plan_path),
        "package_manifest_sha256": sha256(package / "MANIFEST.json"),
        "provenance": collect_provenance(plan),
        "training_updates": 0,
        "research_final_test_steps": 0,
        "presentation_diagnostic_steps": sum(row["steps"] for row in episodes),
        "parameters_unchanged": True,
        "episodes": episodes,
        "same_state_sensitivity": sensitivity,
    }
    write_json(output / "results.json", payload)
    return payload


if __name__ == "__main__":
    run()

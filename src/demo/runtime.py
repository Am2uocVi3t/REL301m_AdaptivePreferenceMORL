from __future__ import annotations

import base64
import hashlib
import io
import json
import random
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import numpy as np
import torch
from PIL import Image

from src.envs.wrapper import make_mo_env
from src.models.q_network import VectorQNetwork


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def preference(value: Any, dimension: int) -> np.ndarray:
    if not isinstance(value, list) or len(value) != dimension or any(type(v) not in (int, float) for v in value):
        raise ValueError("Preference phải là một vector số đúng kích thước")
    array = np.asarray(value, dtype=np.float32)
    if not np.all(np.isfinite(array)) or np.any(array < 0) or np.any(array > 1):
        raise ValueError("Preference cần hữu hạn trong [0, 1]")
    if not np.isclose(array.sum(), 1, atol=1e-5):
        raise ValueError("Tổng preference phải bằng 1")
    return array


class Panel:
    def __init__(self, spec: dict[str, Any], weights: np.ndarray):
        self.spec = spec
        self.weights = weights.copy()
        self.np_state = np.random.RandomState(spec["seed"]).get_state()
        self.py_state = random.Random(spec["seed"]).getstate()
        with self.rng():
            self.env = make_mo_env(spec["env_id"], render_mode="rgb_array", dynamics_shift_config=spec["nominal"])
            self.observation = self.env.reset(seed=spec["seed"])[0]
        self.steps = 0
        self.action: int | None = None
        self.scores: list[float] = []
        self.raw = np.zeros(len(weights), dtype=np.float64)
        self.discounted = np.zeros(len(weights), dtype=np.float64)
        self.terminated = self.truncated = False
        self.switches: list[dict[str, Any]] = []
        self.transitions: list[dict[str, Any]] = []

    @contextmanager
    def rng(self):
        """Minecart scipy sampling uses global RNG; isolate each panel without changing engine."""
        original_np, original_py = np.random.get_state(), random.getstate()
        np.random.set_state(self.np_state)
        random.setstate(self.py_state)
        try:
            yield
        finally:
            self.np_state, self.py_state = np.random.get_state(), random.getstate()
            np.random.set_state(original_np)
            random.setstate(original_py)

    @property
    def done(self) -> bool:
        return self.terminated or self.truncated or self.steps >= 1000

    def advance(self, network: VectorQNetwork) -> None:
        if self.done:
            return
        before = np.asarray(self.observation).tolist()
        with torch.inference_mode():
            self.action, scores = network.predict_action(
                torch.as_tensor(self.observation, dtype=torch.float32), torch.as_tensor(self.weights), head_idx=None
            )
        self.scores = scores.tolist()
        with self.rng():
            observation, reward, self.terminated, self.truncated, _ = self.env.step(self.action)
        reward = np.asarray(reward, dtype=np.float64)
        self.raw += reward
        self.discounted += self.spec["gamma"] ** self.steps * reward * np.asarray(self.spec["reward_scale"])
        self.steps += 1
        self.observation = observation
        self.transitions.append(
            {
                "step": self.steps,
                "observation": before,
                "preference": self.weights.tolist(),
                "action": self.action,
                "reward": reward.tolist(),
                "next_observation": np.asarray(observation).tolist(),
                "terminated": bool(self.terminated),
                "truncated": bool(self.truncated),
            }
        )

    def scene(self) -> dict[str, Any]:
        env: Any = self.env.unwrapped
        if self.spec["env_id"] == "minecart-v0":
            return {
                "kind": "minecart",
                "position": env.cart.pos.tolist(),
                "angle": float(env.cart.angle),
                "speed": float(env.cart.speed),
                "cargo": env.cart.content.tolist(),
                "capacity": float(env.capacity),
                "mines": [mine.pos.tolist() for mine in env.mines],
            }

        def body(part):
            return {
                "position": list(part.position),
                "angle": float(part.angle),
                "fixtures": [[list(vertex) for vertex in fixture.shape.vertices] for fixture in part.fixtures],
            }

        return {
            "kind": "lunar",
            "lander": body(env.lander),
            "legs": [body(leg) for leg in env.legs],
            "terrain": [[float(x), float(y)] for polygon in env.sky_polys for x, y in polygon[:2]],
            "pad": [float(env.helipad_x1), float(env.helipad_x2), float(env.helipad_y)],
            "contact": [bool(leg.ground_contact) for leg in env.legs],
        }

    def snapshot(self, native: bool = False) -> dict[str, Any]:
        result = {
            "steps": self.steps,
            "action": self.action,
            "action_scores": self.scores,
            "weights": self.weights.tolist(),
            "raw_return": self.raw.tolist(),
            "discounted_scaled_return": self.discounted.tolist(),
            "done": self.done,
            "terminated": bool(self.terminated),
            "truncated": bool(self.truncated),
            "presentation_cap": self.steps >= 1000,
            "observation": np.asarray(self.observation).tolist(),
            "switches": self.switches,
            "scene": self.scene(),
        }
        if native:
            np_saved, py_saved = self.np_state, self.py_state
            try:
                with self.rng():
                    frame = self.env.render()
                    if not isinstance(frame, np.ndarray):
                        raise ValueError("Native renderer did not return an RGB array")
            finally:
                self.np_state, self.py_state = np_saved, py_saved
            buffer = io.BytesIO()
            Image.fromarray(frame).save(buffer, format="JPEG", quality=85)
            result["native_frame"] = base64.b64encode(buffer.getvalue()).decode("ascii")
        return result

    def close(self) -> None:
        self.env.close()


class DemoRuntime:
    def __init__(self, root: Path):
        self.root = root
        self.config = json.loads((root / "config.json").read_text())
        self.models: dict[str, VectorQNetwork] = {}
        self.specs = self.config["environments"]
        self.panels: list[Panel] = []
        self.environment: str | None = None
        self.generation = 0
        self.tick_id = 0
        self.last_request: str | None = None
        self.last_result: dict[str, Any] | None = None
        self.total_steps = 0
        self.total_resets = 0
        self.fault: str | None = None

    def model(self, name: str) -> VectorQNetwork:
        if name not in self.models:
            spec = self.specs[name]
            path = self.root / spec["weights_file"]
            if sha256(path) != spec["weights_sha256"]:
                raise ValueError("Model hash không khớp; dừng nạp checkpoint")
            checkpoint = torch.load(path, map_location="cpu", weights_only=True)
            network = VectorQNetwork(**checkpoint["architecture"])
            network.load_state_dict(checkpoint["model_state_dict"])
            network.eval().requires_grad_(False)
            self.models[name] = network
        return self.models[name]

    def reset(self, name: Any, weights: Any, generation: Any) -> dict[str, Any]:
        if type(generation) is not int or generation != self.generation:
            raise ValueError("Generation cũ; tải lại trạng thái")
        if not isinstance(name, str) or name not in self.specs:
            raise ValueError("Môi trường không được hỗ trợ")
        spec = self.specs[name]
        user = preference(weights, len(spec["default_weights"]))
        self.model(name)
        fresh = []
        try:
            fresh.append(Panel(spec, preference(spec["default_weights"], len(user))))
            fresh.append(Panel(spec, user))
        except Exception:
            for panel in fresh:
                panel.close()
            raise
        self.close()
        self.panels = fresh
        self.environment = name
        self.generation += 1
        self.tick_id = 0
        self.last_request = None
        self.last_result = None
        self.total_resets += 1
        self.fault = None
        return self.snapshot()

    def snapshot(self, native: bool = False) -> dict[str, Any]:
        return {
            "generation": self.generation,
            "tick_id": self.tick_id,
            "environment": self.environment,
            "panels": [panel.snapshot(native) for panel in self.panels],
            "training_updates": 0,
            "presentation_steps_total": self.total_steps,
            "resets_total": self.total_resets,
            "history_dependent": any(panel.switches for panel in self.panels),
            "all_done": bool(self.panels) and all(panel.done for panel in self.panels),
            "fault": self.fault,
        }

    def tick(self, request: dict[str, Any]) -> dict[str, Any]:
        if self.fault is not None:
            raise RuntimeError("Engine đã lỗi; reset trước khi chạy tiếp")
        if not self.panels or type(request.get("generation")) is not int or request["generation"] != self.generation:
            raise ValueError("Generation cũ hoặc chưa reset")
        identifier = request.get("tick_id")
        canonical = json.dumps(request, sort_keys=True, allow_nan=False)
        if type(identifier) is not int:
            raise ValueError("Tick ID cần là số nguyên")
        if identifier == self.tick_id and self.last_result is not None:
            if canonical != self.last_request:
                raise ValueError("Tick ID trùng nhưng payload khác")
            return self.last_result
        if identifier != self.tick_id + 1:
            raise ValueError("Tick ID không đúng thứ tự")
        steps = request.get("steps", 1)
        if type(steps) is not int or not 1 <= steps <= 8 or type(request.get("native", False)) is not bool:
            raise ValueError("Steps cần trong 1..8; native cần boolean")
        if "weights" in request:
            user = preference(request["weights"], len(self.panels[1].weights))
            panel = self.panels[1]
            if not np.array_equal(user, panel.weights):
                if panel.done:
                    raise ValueError("Episode đã kết thúc; reset để đổi preference")
                panel.switches.append({"from_step": panel.steps + 1, "weights": user.tolist()})
                panel.weights = user
        network = self.model(str(self.environment))
        try:
            for _ in range(steps):
                for panel in self.panels:
                    before = panel.steps
                    panel.advance(network)
                    self.total_steps += panel.steps - before
            result = self.snapshot(request.get("native", False))
        except Exception as error:
            self.fault = type(error).__name__
            raise RuntimeError("Engine bị lỗi; dừng và reset, không retry tick") from error
        self.tick_id = identifier
        result["tick_id"] = identifier
        self.last_request = canonical
        self.last_result = result
        return self.last_result

    def trace(self) -> dict[str, Any]:
        return {
            "presentation_only": True,
            "training_updates": 0,
            "environment": self.environment,
            "generation": self.generation,
            "seed": self.specs[self.environment]["seed"] if self.environment else None,
            "spec": self.specs.get(self.environment, {}),
            "state": self.snapshot(),
            "transitions": [panel.transitions for panel in self.panels],
        }

    def close(self) -> None:
        for panel in self.panels:
            panel.close()
        self.panels = []

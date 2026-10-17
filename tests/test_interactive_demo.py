import base64
import copy
import io
import json
import threading
from http.client import HTTPConnection

import numpy as np
import pytest
import torch
from PIL import Image

from src.demo.runtime import DemoRuntime, Panel, preference, sha256
from src.demo.server import make_server
from src.models.q_network import VectorQNetwork


@pytest.fixture
def demo_root(tmp_path, monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    torch.set_num_threads(1)
    specs = {}
    for name, env, state, actions, dim in [("lunar", "mo-lunar-lander-v3", 8, 4, 4), ("mine", "minecart-v0", 7, 6, 3)]:
        architecture = {
            "state_dim": state,
            "action_dim": actions,
            "reward_dim": dim,
            "hidden_dims": [16, 16],
            "num_heads": 3,
        }
        with torch.random.fork_rng():
            torch.manual_seed(13)
            network = VectorQNetwork(**architecture)
        path = tmp_path / f"{name}.pt"
        torch.save({"architecture": architecture, "model_state_dict": network.state_dict()}, path)
        specs[name] = {
            "env_id": env,
            "seed": 20000 if name == "lunar" else 670000,
            "default_weights": [1 / dim] * dim,
            "gamma": 0.99,
            "reward_scale": [1.0] * dim,
            "nominal": {"constructor_kwargs": {}},
            "weights_file": path.name,
            "weights_sha256": sha256(path),
        }
    (tmp_path / "config.json").write_text(json.dumps({"environments": specs}))
    (tmp_path / "website").mkdir()
    (tmp_path / "website/index.html").write_text("<h1>Demo</h1>")
    return tmp_path


@pytest.mark.parametrize(
    "value",
    [
        None,
        [1],
        [0, 0, 0],
        [1, -1, 1],
        [float("nan"), 0, 1],
        [float("inf"), 0, 0],
        [True, 0, 0],
        ["1", 0, 0],
        [2, -1, 0],
    ],
)
def test_invalid_preferences_rejected(value):
    with pytest.raises(ValueError):
        preference(value, 3)


@pytest.mark.parametrize("name", ["lunar", "mine"])
def test_matched_start_native_skin_and_rng_are_read_only(demo_root, name):
    runtime = DemoRuntime(demo_root)
    try:
        default = runtime.specs[name]["default_weights"]
        state = runtime.reset(name, default, 0)
        assert state["panels"][0] == state["panels"][1]
        before_rng = np.random.get_state()
        state = runtime.tick({"generation": 1, "tick_id": 1, "steps": 8})
        np.testing.assert_array_equal(np.random.get_state()[1], before_rng[1])
        assert state["panels"][0] == state["panels"][1]
        before = runtime.snapshot()
        rendered = runtime.snapshot(True)
        assert runtime.snapshot() == before
        image = Image.open(io.BytesIO(base64.b64decode(rendered["panels"][0]["native_frame"])))
        assert image.size == ((600, 400) if name == "lunar" else (480, 480))
        runtime.tick({"generation": 1, "tick_id": 2, "steps": 8})
        assert runtime.panels[0].transitions == runtime.panels[1].transitions
    finally:
        runtime.close()


def test_live_weights_reach_network_without_reset_or_parameter_update(demo_root, monkeypatch):
    runtime = DemoRuntime(demo_root)
    try:
        runtime.reset("lunar", [0.25] * 4, 0)
        model = runtime.model("lunar")
        before = {key: value.clone() for key, value in model.state_dict().items()}
        assert not model.training and all(not p.requires_grad for p in model.parameters())
        captured = []
        predict = model.predict_action

        def record(state, weights, head_idx=None):
            captured.append(weights.tolist())
            return predict(state, weights, head_idx)

        monkeypatch.setattr(model, "predict_action", record)
        runtime.tick({"generation": 1, "tick_id": 1, "steps": 1})
        result = runtime.tick({"generation": 1, "tick_id": 2, "steps": 1, "weights": [0, 0, 1, 0]})
        assert captured[-2:] == [[0.25] * 4, [0, 0, 1, 0]]
        assert result["generation"] == 1 and result["panels"][1]["steps"] == 2
        assert result["history_dependent"] and result["panels"][0]["switches"] == []
        assert result["panels"][1]["switches"] == [{"from_step": 2, "weights": [0, 0, 1, 0]}]
        assert all(torch.equal(value, before[key]) for key, value in model.state_dict().items())
        assert all(p.grad is None for p in model.parameters())
        assert result["training_updates"] == 0
    finally:
        runtime.close()


def test_tick_duplicate_stale_reset_and_terminal_freeze(demo_root):
    runtime = DemoRuntime(demo_root)
    try:
        runtime.reset("mine", [1 / 3] * 3, 0)
        request = {"generation": 1, "tick_id": 1, "steps": 2}
        first = runtime.tick(request)
        assert runtime.tick(copy.deepcopy(request)) is first
        assert runtime.total_steps == 4
        with pytest.raises(ValueError, match="payload khác"):
            runtime.tick({**request, "steps": 3})
        for invalid in ({**request, "tick_id": 3}, {**request, "generation": 0}, {**request, "tick_id": True}):
            with pytest.raises(ValueError):
                runtime.tick(invalid)
        before = runtime.snapshot()
        with pytest.raises(ValueError):
            runtime.reset("mine", [0, 0, 0], 1)
        assert runtime.snapshot() == before
        for panel in runtime.panels:
            panel.steps = 1000
        count = runtime.total_steps
        result = runtime.tick({"generation": 1, "tick_id": 2, "steps": 8})
        assert result["all_done"] and runtime.total_steps == count
        runtime.reset("mine", [1 / 3] * 3, 1)
        assert runtime.generation == 2 and runtime.tick_id == 0
        with pytest.raises(ValueError):
            runtime.tick(request)
    finally:
        runtime.close()


def test_minecart_global_mining_rng_is_paired(demo_root):
    runtime = DemoRuntime(demo_root)
    spec = runtime.specs["mine"]
    panels = [Panel(spec, np.asarray(spec["default_weights"], dtype=np.float32)) for _ in range(2)]
    try:
        # Sampling method is from the actual environment; no physics/reward patch.
        samples = []
        for panel in panels:
            with panel.rng():
                samples.append([panel.env.unwrapped.mines[0].mine() for _ in range(3)])
        assert samples[0] == samples[1]
    finally:
        for panel in panels:
            panel.close()


def test_model_hash_fails_closed(demo_root):
    runtime = DemoRuntime(demo_root)
    (demo_root / "lunar.pt").write_bytes(b"tampered")
    with pytest.raises(ValueError, match="hash"):
        runtime.reset("lunar", [0.25] * 4, 0)
    assert runtime.total_resets == 0


def test_partial_engine_failure_blocks_further_ticks_until_reset(demo_root, monkeypatch):
    runtime = DemoRuntime(demo_root)
    try:
        runtime.reset("mine", [1 / 3] * 3, 0)

        def broken(_network):
            raise RuntimeError("Synthetic engine failure")

        monkeypatch.setattr(runtime.panels[1], "advance", broken)
        with pytest.raises(RuntimeError, match="không retry"):
            runtime.tick({"generation": 1, "tick_id": 1, "steps": 1})
        assert runtime.total_steps == 1
        assert runtime.snapshot()["fault"] == "RuntimeError"
        with pytest.raises(RuntimeError, match="reset"):
            runtime.tick({"generation": 1, "tick_id": 1, "steps": 1})
        assert runtime.total_steps == 1
        runtime.reset("mine", [1 / 3] * 3, 1)
        assert runtime.fault is None
        assert runtime.tick({"generation": 2, "tick_id": 1, "steps": 1})["presentation_steps_total"] == 3
    finally:
        runtime.close()


def test_http_auth_bounds_allowlist_and_real_inference(demo_root):
    server = make_server(demo_root, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)

    def request(method, path, value=None, headers=None):
        client.request(method, path, json.dumps(value) if value is not None else None, headers or {})
        response = client.getresponse()
        return response.status, response.read()

    try:
        status, raw = request("GET", "/api/config")
        assert status == 200
        token = json.loads(raw)["token"]
        headers = {"X-Demo-Token": token, "Content-Type": "application/json"}
        reset = {"environment": "mine", "weights": [1 / 3] * 3, "generation": 0}
        assert request("POST", "/api/reset", reset)[0] == 403
        assert request("POST", "/api/reset", reset, {**headers, "Origin": "https://evil.example"})[0] == 403
        assert request("GET", "/api/config", headers={"Host": "evil.example"})[0] == 403
        assert request("POST", "/api/reset", reset, headers)[0] == 200
        tick = {"generation": 1, "tick_id": 1, "steps": 1}
        status, first = request("POST", "/api/tick", tick, headers)
        assert status == 200 and json.loads(first)["presentation_steps_total"] == 2
        assert request("POST", "/api/tick", tick, headers)[1] == first
        assert request("POST", "/api/tick", {**tick, "tick_id": 2, "steps": 9999}, headers)[0] == 400
        assert request("POST", "/api/reset", ["not", "object"], headers)[0] == 400
        for path in ("/mine.pt", "/config.json", "/../config.json", "/%2e%2e/config.json", "/src/demo/runtime.py"):
            assert request("GET", path)[0] == 404
        status, raw = request("GET", "/api/state?native=1")
        assert status == 200 and "native_frame" in json.loads(raw)["panels"][0]
        assert request("OPTIONS", "/api/tick")[0] == 403
    finally:
        client.close()
        server.shutdown()
        thread.join(timeout=5)
        server.runtime.close()
        server.server_close()

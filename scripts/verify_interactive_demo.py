#!/usr/bin/env python3
"""Verify the packaged app, actual frozen models and isolated launch over loopback."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import zipfile
from http.client import HTTPConnection
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.verify_monday_package import Links
from src.demo.runtime import DemoRuntime

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "outputs/REL301m_Interactive_Demo"


def verify_files(package: Path) -> dict:
    manifest = json.loads((package / "MANIFEST.json").read_text())
    for name, digest in manifest["files"].items():
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Unsafe package path")
        path = package / name
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError(f"Changed package file: {name}")
        if any(part in {".env", ".aris", ".git"} for part in relative.parts):
            raise ValueError("Private file in package")
        if path.suffix in {".py", ".html", ".js", ".json", ".md", ".css", ".txt"}:
            if re.search(r"sk-(?:ant-)?[A-Za-z0-9_-]{16,}|-----BEGIN .*PRIVATE KEY-----", path.read_text()):
                raise ValueError("Potential credential in shareable text")
    if any(name.endswith((".mp4", ".gif")) or Path(name).name.startswith("train") for name in manifest["files"]):
        raise ValueError("Unexpected video/training executable")
    parser = Links()
    parser.feed((package / "website/index.html").read_text())
    aliases = {"docs/report.pdf": "docs/Bao_cao.pdf", "docs/guide.pdf": "docs/Huong_dan.pdf"}
    for link in parser.links:
        if ":" in link or link.startswith("//"):
            raise ValueError("Unexpected external page asset")
        asset_name = aliases.get(link, "website/" + link)
        if not (package / asset_name).is_file():
            raise ValueError(f"Broken local link {link}")
    with zipfile.ZipFile(package.with_suffix(".zip")) as archive:
        expected = {f"{package.name}/{name}" for name in [*manifest["files"], "MANIFEST.json"]}
        if set(archive.namelist()) != expected:
            raise ValueError("ZIP allowlist mismatch")
        for name in [*manifest["files"], "MANIFEST.json"]:
            if archive.read(f"{package.name}/{name}") != (package / name).read_bytes():
                raise ValueError("ZIP bytes mismatch")
    return {
        "status": "PASS",
        "files_hashed": len(manifest["files"]),
        "links": len(parser.links),
        "zip_matches": True,
        "credential_scan": "heuristic_clean",
        "no_videos_or_training_runner": True,
    }


def verify_real_models(package: Path) -> dict:
    runtime = DemoRuntime(package)
    outputs = {}
    try:
        for name in ("lunar", "mine"):
            spec = runtime.specs[name]
            source = torch.load(ROOT / spec["source_checkpoint"], map_location="cpu", weights_only=True)
            model = runtime.model(name)
            if not all(
                torch.equal(value, source["model_state_dict"][key]) for key, value in model.state_dict().items()
            ):
                raise ValueError("Packaged model differs from original trained checkpoint")
            before = {key: value.clone() for key, value in model.state_dict().items()}
            runtime.reset(name, spec["default_weights"], runtime.generation)
            first = runtime.tick({"generation": runtime.generation, "tick_id": 1, "steps": 8})
            if first["panels"][0] != first["panels"][1]:
                raise ValueError("Matched preference/seed panels diverged")
            paused = runtime.snapshot()
            runtime.snapshot(True)
            if runtime.snapshot() != paused:
                raise ValueError("Native render/snapshot changed simulation")
            extreme = [0.0] * len(spec["objectives"])
            extreme[0] = 1.0
            request = {"generation": runtime.generation, "tick_id": 2, "steps": 1, "weights": extreme}
            result = runtime.tick(request)
            if runtime.tick(request) is not result or runtime.panels[1].steps != 9:
                raise ValueError("Repeated tick duplicated work")
            if runtime.panels[1].transitions[-1]["preference"] != extreme or runtime.generation != paused["generation"]:
                raise ValueError("Live preference did not reach model without reset")
            while not result["all_done"]:
                result = runtime.tick({"generation": runtime.generation, "tick_id": runtime.tick_id + 1, "steps": 8})
            count = runtime.total_steps
            runtime.tick({"generation": runtime.generation, "tick_id": runtime.tick_id + 1, "steps": 8})
            if runtime.total_steps != count:
                raise ValueError("Terminal simulation continued")
            for panel in runtime.panels:
                rewards = np.asarray([transition["reward"] for transition in panel.transitions])
                if not np.allclose(rewards.sum(axis=0), panel.raw):
                    raise ValueError("Raw vector returns do not match transitions")
                discounted = (
                    rewards * np.asarray(spec["reward_scale"]) * spec["gamma"] ** np.arange(len(rewards))[:, None]
                ).sum(axis=0)
                if not np.allclose(discounted, panel.discounted):
                    raise ValueError("Discounted vector return mismatch")
            trace = runtime.trace()
            path = ROOT / "artifacts/presentation-verification/2026-10-17" / f"{name}-trace.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(trace, indent=2, ensure_ascii=False) + "\n")
            unchanged = all(torch.equal(value, before[key]) for key, value in model.state_dict().items())
            if not unchanged or any(
                parameter.grad is not None or parameter.requires_grad for parameter in model.parameters()
            ):
                raise ValueError("Model changed during inference")
            outputs[name] = {
                "source_weights_equal": True,
                "model_parameters_unchanged": True,
                "matched_first_eight_steps": True,
                "live_switch_from_step": 9,
                "episode_lengths": [p.steps for p in runtime.panels],
                "raw_returns": [p.raw.tolist() for p in runtime.panels],
                "trace": str(path.relative_to(ROOT)),
                "trace_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        return {
            "status": "PASS",
            "environments": outputs,
            "presentation_steps": runtime.total_steps,
            "training_updates": 0,
        }
    finally:
        runtime.close()


def verify_isolated_launch(package: Path) -> dict:
    # A second loopback port is test-only; no public host binding or browser workaround.
    with tempfile.TemporaryDirectory(prefix="rel301m-interactive-") as temporary:
        with zipfile.ZipFile(package.with_suffix(".zip")) as archive:
            archive.extractall(temporary)  # Trusted allowlist already verified above.
        extracted = Path(temporary) / package.name
        env = dict(os.environ, PYTHONPATH="", SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
        with subprocess.Popen(
            [sys.executable, "launch.py", "--port", "18765"],
            cwd=extracted,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ) as process:
            try:
                deadline = time.monotonic() + 15
                client = None
                while time.monotonic() < deadline:
                    if process.poll() is not None:
                        raise RuntimeError("Isolated launch exited: " + process.communicate()[1].decode()[-1500:])
                    try:
                        client = HTTPConnection("127.0.0.1", 18765, timeout=2)
                        client.request("GET", "/api/config")
                        response = client.getresponse()
                        data = json.loads(response.read())
                        break
                    except (ConnectionError, OSError):
                        if client is not None:
                            client.close()
                        time.sleep(0.15)
                else:
                    raise RuntimeError("Isolated launch timeout")
                if client is None:
                    raise RuntimeError("No loopback client")
                try:
                    headers = {"Content-Type": "application/json", "X-Demo-Token": data["token"]}
                    for name in ("lunar", "mine"):
                        client.request(
                            "POST",
                            "/api/reset",
                            json.dumps(
                                {
                                    "environment": name,
                                    "weights": data["environments"][name]["default_weights"],
                                    "generation": 0 if name == "lunar" else 1,
                                }
                            ),
                            headers,
                        )
                        response = client.getresponse()
                        body = json.loads(response.read())
                        if response.status != 200 or body["environment"] != name:
                            raise ValueError("Extracted app reset failed")
                        client.request(
                            "POST",
                            "/api/tick",
                            json.dumps({"generation": body["generation"], "tick_id": 1, "steps": 1}),
                            headers,
                        )
                        response = client.getresponse()
                        body = json.loads(response.read())
                        if response.status != 200 or body["panels"][0]["steps"] != 1:
                            raise ValueError("Extracted app inference failed")
                    return {
                        "status": "PASS",
                        "extracted_zip_launch": True,
                        "repository_import_path": False,
                        "http_reset_and_inference_both_environments": True,
                        "os": "Linux Python 3.11 CPU",
                    }
                finally:
                    client.close()
            finally:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)


def main() -> None:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    torch.set_num_threads(1)
    output = {
        "package": verify_files(PACKAGE),
        "models": verify_real_models(PACKAGE),
        "portable_launch": verify_isolated_launch(PACKAGE),
    }
    target = ROOT / "artifacts/presentation-verification/2026-10-17/verification.json"
    target.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

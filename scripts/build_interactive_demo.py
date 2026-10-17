#!/usr/bin/env python3
"""Package existing frozen weights and local interactive inference; no training."""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import zipfile
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.evaluation.protocol import load_protocol, protocol_hash

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/REL301m_Interactive_Demo"
SOURCE = ROOT / "demo/interactive"


def build() -> Path:
    paths: list[Path] = []

    def copy(source: Path, relative: str) -> None:
        destination = OUT / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        paths.append(destination)

    def text(relative: str, value: str) -> None:
        destination = OUT / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(value, encoding="utf-8")
        paths.append(destination)

    environments = {}
    for name, env, run, step, seed, labels, actions, nominal in [
        (
            "lunar",
            "mo-lunar-lander-v3",
            "artifacts/course-paired-matrix-v1/mo-lunar-lander-v3/full/adaptive-pcqn_mo-lunar-lander-v3_seed20262001",
            500000,
            20000,
            ["Hạ cánh", "Ổn định / shaping", "Tiết kiệm động cơ chính", "Tiết kiệm động cơ phụ"],
            ["Không đốt", "Động cơ trái", "Động cơ chính", "Động cơ phải"],
            {
                "constructor_kwargs": {
                    "gravity": -10.0,
                    "enable_wind": False,
                    "wind_power": 0.0,
                    "turbulence_power": 0.0,
                }
            },
        ),
        (
            "mine",
            "minecart-v0",
            "artifacts/minecart-pcqn-remediation-v2/uniform-pcqn_minecart-v0_seed20264011",
            1000000,
            670000,
            ["Quặng 1", "Quặng 2", "Tiết kiệm nhiên liệu"],
            ["Khai thác", "Rẽ trái", "Rẽ phải", "Tăng tốc", "Phanh", "Không làm gì"],
            {"constructor_kwargs": {}},
        ),
    ]:
        source = ROOT / run / f"checkpoint_step{step}.pt"
        checkpoint = torch.load(source, map_location="cpu", weights_only=True)
        protocol_path = ROOT / checkpoint["args"]["protocol"]
        protocol, preferences = load_protocol(protocol_path, "validation")
        if checkpoint["protocol_sha256"] != protocol_hash(protocol):
            raise ValueError("Source checkpoint protocol mismatch")
        index = int(np.argmin(np.sum((preferences - 1 / len(labels)) ** 2, axis=1)))
        destination = OUT / f"checkpoints/{name}.pt"
        destination.parent.mkdir(parents=True, exist_ok=True)
        torch.save(
            {"architecture": checkpoint["architecture"], "model_state_dict": checkpoint["model_state_dict"]},
            destination,
        )
        paths.append(destination)
        environments[name] = {
            "env_id": env,
            "seed": seed,
            "default_weights": preferences[index].tolist(),
            "default_validation_index": index,
            "objectives": labels,
            "actions": actions,
            "reward_scale": protocol["reward_scale"],
            "gamma": protocol["return_definition"]["gamma"],
            "nominal": nominal,
            "algorithm": checkpoint["args"]["algo"],
            "training_seed": checkpoint["args"]["seed"],
            "training_step": step,
            "weights_file": f"checkpoints/{name}.pt",
            "weights_sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
            "source_checkpoint": str(source.relative_to(ROOT)),
            "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "source_protocol_sha256": protocol_hash(protocol),
            "caveat": (
                "Minecart v2 chưa đạt qualification: slider có thể không tạo hành vi lấy quặng. "
                "Không dựng thành công giả."
            )
            if name == "mine"
            else (
                "Inference từ checkpoint đã train. Đổi preference không đảm bảo hạ cánh thành công; "
                "không phải benchmark."
            ),
        }
    for name in ("index.html", "style.css", "app.js", "renderer.js"):
        copy(SOURCE / name, f"website/{name}")
    for name in ("launch.py", "START_DEMO.sh", "START_DEMO.bat", "README_VI.md", "requirements.txt"):
        copy(SOURCE / name, name)
    for relative in (
        "src/demo/__init__.py",
        "src/demo/runtime.py",
        "src/demo/server.py",
        "src/models/q_network.py",
        "src/envs/wrapper.py",
        "src/envs/shift.py",
    ):
        copy(ROOT / relative, relative)
    for directory in ("src", "src/models", "src/envs"):
        text(f"{directory}/__init__.py", "")
    copy(ROOT / "paper/REL301m/main.pdf", "docs/Bao_cao.pdf")
    guide = ROOT / "artifacts/presentation-build/interactive-docs/Huong_dan.pdf"
    if not guide.is_file():
        raise ValueError("Build the current interactive guide before packaging")
    copy(guide, "docs/Huong_dan.pdf")
    copy(ROOT / "DESIGN.md", "DESIGN.md")
    text(
        "config.json",
        json.dumps(
            {"purpose": "interactive_inference_only", "environments": environments}, indent=2, ensure_ascii=False
        )
        + "\n",
    )
    verification = ROOT / "research/qualification/interactive_model_demo_v1.json"
    if verification.is_file():
        copy(verification, "VERIFICATION.json")
    manifest = {
        "kind": "frozen_model_interactive_website",
        "files": {str(path.relative_to(OUT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(paths)},
    }
    text("MANIFEST.json", json.dumps(manifest, indent=2) + "\n")
    with zipfile.ZipFile(OUT.with_suffix(".zip"), "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in paths:
            archive.write(path, f"{OUT.name}/{path.relative_to(OUT)}")
    print(str(OUT.with_suffix(".zip")))
    return OUT


if __name__ == "__main__":
    build()

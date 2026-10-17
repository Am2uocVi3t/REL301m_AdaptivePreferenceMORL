#!/usr/bin/env python3
"""Render four predeclared validation replays; never train or access final test."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np
import torch
from PIL import Image, ImageDraw, ImageFont, ImageOps

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.evaluate import load_network, load_shift
from src.envs.wrapper import make_mo_env
from src.evaluation.protocol import load_protocol, protocol_hash

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/visual-demo"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SPECS = (
    {
        "name": "LunarLander",
        "env": "mo-lunar-lander-v3",
        "run": "artifacts/course-paired-matrix-v1/mo-lunar-lander-v3/full/"
        "adaptive-pcqn_mo-lunar-lander-v3_seed20262001",
        "steps": [50000, 500000],
        "seed": 20000,
        "protocol": "configs/protocols/course_mo_lunar_lander_v3.json",
        "actions": ["Không đốt", "Động cơ trái", "Động cơ chính", "Động cơ phải"],
        "objectives": "hạ cánh / shaping / động cơ chính / động cơ phụ",
    },
    {
        "name": "Minecart",
        "env": "minecart-v0",
        "run": "artifacts/minecart-pcqn-remediation-v2/uniform-pcqn_minecart-v0_seed20264011",
        "steps": [100000, 1000000],
        "seed": 670000,
        "protocol": "configs/protocols/course_minecart_v0.json",
        "actions": ["Khai thác", "Rẽ trái", "Rẽ phải", "Tăng tốc", "Phanh", "Không làm gì"],
        "objectives": "quặng 1 / quặng 2 / chi phí nhiên liệu",
    },
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def centre_preference(preferences: np.ndarray) -> tuple[int, np.ndarray]:
    index = int(np.argmin(np.sum((preferences - 1 / preferences.shape[1]) ** 2, axis=1)))
    return index, preferences[index]


def save_json(path: Path, value: Any) -> None:
    pending = path.with_suffix(".pending")
    pending.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
    pending.replace(path)


def render(spec: dict[str, Any], redraw_recorded: bool = False) -> dict[str, Any]:
    name = spec["name"]
    target = OUT / f"{name}.mp4"
    trace_path = OUT / f"{name}.json"
    receipt = OUT / f"{name}.complete.json"
    marker = OUT / f"{name}.started.json"
    protocol_path = ROOT / spec["protocol"]
    protocol, preferences = load_protocol(protocol_path, "validation")
    preference_index, preference = centre_preference(preferences)
    paths = [ROOT / spec["run"] / f"checkpoint_step{step}.pt" for step in spec["steps"]]
    inputs = {
        "script": digest(Path(__file__)),
        "plan": digest(ROOT / "visual-policy-demo.md"),
        "protocol": digest(protocol_path),
        "shifts": digest(ROOT / "configs/shifts/dynamics_shifts.yaml"),
        "checkpoints": {str(path.relative_to(ROOT)): digest(path) for path in paths},
    }
    recorded = None
    if redraw_recorded:
        if not receipt.exists():
            raise ValueError("Redraw requires a completed trace")
        recorded = json.loads(trace_path.read_text())
        previous = json.loads(receipt.read_text())
        for key in ("plan", "protocol", "shifts", "checkpoints"):
            if previous["inputs"][key] != inputs[key]:
                raise ValueError("Recorded replay input changed")
        if previous["outputs"][trace_path.name] != digest(trace_path):
            raise ValueError("Recorded trace changed")
        archive = OUT / "initial-render"
        archive.mkdir(exist_ok=True)
        for path in (receipt, trace_path, target):
            if (archive / path.name).exists():
                raise ValueError("Initial render already archived; refuse repeated redraw")
            shutil.copyfile(path, archive / path.name)
    elif receipt.exists():
        previous = json.loads(receipt.read_text())
        if previous["inputs"] != inputs or previous["outputs"] != {
            target.name: digest(target),
            trace_path.name: digest(trace_path),
        }:
            raise ValueError("Completed demo changed; refuse silent replay")
        print(f"SKIP verified completed {name}", flush=True)
        return previous
    if marker.exists() and not redraw_recorded:
        raise ValueError(f"Interrupted {name}: inspect saved state before any redispatch")
    save_json(marker, {"inputs": inputs, "status": "started", "spec": spec})
    networks, environments, observations = [], [], []
    episodes: list[dict[str, Any]] = []
    for path in paths:
        checkpoint = torch.load(path, weights_only=True, map_location="cpu")
        if checkpoint["protocol_sha256"] != protocol_hash(protocol):
            raise ValueError("Checkpoint protocol mismatch")
        architecture = checkpoint["architecture"]
        network = load_network(
            checkpoint, architecture["state_dim"], architecture["action_dim"], architecture["reward_dim"], "cpu"
        )
        networks.append(network)
        env = make_mo_env(
            spec["env"],
            render_mode="rgb_array",
            dynamics_shift_config=load_shift(str(ROOT / "configs/shifts/dynamics_shifts.yaml"), spec["env"], "nominal"),
        )
        observations.append(env.reset(seed=spec["seed"])[0])
        environments.append(env)
        episodes.append(
            {
                "checkpoint": str(path.relative_to(ROOT)),
                "transitions": [],
                "raw_return": [0.0] * len(preference),
                "discounted_scaled_return": [0.0] * len(preference),
                "done": False,
            }
        )
    command = [
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        "1440x900",
        "-r",
        "25",
        "-i",
        "-",
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "21",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(target),
    ]
    fonts = [ImageFont.truetype(FONT, size) for size in (38, 25, 20)]
    frames = 0
    gamma = protocol["return_definition"]["gamma"]
    scale = np.asarray(protocol["reward_scale"])
    weight = torch.as_tensor(preference)
    try:
        with subprocess.Popen(command, stdin=subprocess.PIPE) as encoder:
            if encoder.stdin is None:
                raise RuntimeError("Encoder input unavailable")
            for step in range(1001):
                final_frame_ready = all(episode["done"] for episode in episodes)
                image = Image.new("RGB", (1440, 900), "#0d1524")
                draw = ImageDraw.Draw(image)
                draw.text((36, 18), f"{name} | Policy MORL hoạt động thật", font=fonts[0], fill="#f5f8ff")
                draw.text(
                    (36, 70),
                    "Checkpoint đầu / cuối training • replay mới, không học thêm",
                    font=fonts[1],
                    fill="#9cb1ce",
                )
                for i, (env, network, episode) in enumerate(zip(environments, networks, episodes, strict=True)):
                    x = 28 + i * 720
                    label = "GIAI ĐOẠN ĐẦU" if i == 0 else "SAU NGÂN SÁCH TRAINING"
                    draw.text((x + 12, 118), label, font=fonts[1], fill="#63dfc3" if i else "#ffcd79")
                    draw.text(
                        (x + 12, 154),
                        f"{spec['steps'][i]:,} interactions • cùng seed {spec['seed']}",
                        font=fonts[2],
                        fill="#c2d0e3",
                    )
                    frame = Image.fromarray(np.asarray(env.render()))
                    frame = ImageOps.contain(frame, (680, 480))
                    image.paste(frame, (x + (680 - frame.width) // 2 + 12, 193 + (480 - frame.height) // 2))
                    transitions = episode["transitions"]
                    action_text = spec["actions"][transitions[-1]["action"]] if transitions else "Bắt đầu"
                    state_text = "Kết thúc episode" if episode["done"] else "Đang chạy"
                    draw.text(
                        (x + 12, 688), f"Bước {len(transitions):04d} | {action_text}", font=fonts[1], fill="#f5f8ff"
                    )
                    reward_text = " / ".join(f"{r:.2f}" for r in episode["raw_return"])
                    draw.text((x + 12, 727), f"Raw return: {reward_text}", font=fonts[2], fill="#63dfc3")
                    draw.text((x + 12, 760), state_text, font=fonts[2], fill="#9cb1ce")
                    if step < 1000 and not episode["done"]:
                        before = np.asarray(observations[i]).tolist()
                        if recorded is not None:
                            action = recorded["episodes"][i]["transitions"][step]["action"]
                        else:
                            with torch.no_grad():
                                action, _ = network.predict_action(
                                    torch.as_tensor(observations[i], dtype=torch.float32), weight, head_idx=None
                                )
                        observation, reward, terminated, truncated, _ = env.step(action)
                        reward = np.asarray(reward)
                        if recorded is not None:
                            saved = recorded["episodes"][i]["transitions"][step]
                            if not np.array_equal(observation, saved["next_observation"]) or not np.array_equal(
                                reward, saved["reward"]
                            ):
                                raise ValueError("Recorded replay diverged; stop")
                        episode["raw_return"] = (np.asarray(episode["raw_return"]) + reward).tolist()
                        episode["discounted_scaled_return"] = (
                            np.asarray(episode["discounted_scaled_return"]) + gamma**step * scale * reward
                        ).tolist()
                        transitions.append(
                            {
                                "step": step + 1,
                                "observation": before,
                                "action": action,
                                "reward": reward.tolist(),
                                "next_observation": np.asarray(observation).tolist(),
                                "terminated": bool(terminated),
                                "truncated": bool(truncated),
                            }
                        )
                        observations[i] = observation
                        episode["done"] = bool(terminated or truncated)
                draw.text(
                    (40, 811),
                    f"w = {np.array2string(preference, precision=3)} • {spec['objectives']}",
                    font=fonts[2],
                    fill="#c2d0e3",
                )
                draw.text(
                    (40, 849),
                    "Nominal validation • 25 bước/giây phát • 1 episode/checkpoint • không phải benchmark",
                    font=fonts[2],
                    fill="#9cb1ce",
                )
                encoder.stdin.write(image.tobytes())
                frames += 1
                if step in (0, 120, 400, 999):
                    image.save(OUT / f"{name}-frame-{step}.jpg")
                if final_frame_ready or step == 1000:
                    image.save(OUT / f"{name}-final.jpg")
                    for _ in range(50):
                        encoder.stdin.write(image.tobytes())
                    frames += 50
                    break
            encoder.stdin.close()
            if encoder.wait(timeout=60) != 0:
                raise RuntimeError("Video encoding failed")
    finally:
        for env in environments:
            env.close()
    trace = {
        "presentation_only": True,
        "split": "validation",
        "shift": "nominal",
        "training_updates": 0,
        "not_original_training_footage": True,
        "preference_index": preference_index,
        "preference": preference.tolist(),
        "episode_seed": spec["seed"],
        "selection": "predeclared; no outcome-dependent retries",
        "episodes": episodes,
        "frames": frames,
        "fps": 25,
        "demo_cap": 1000,
        "render_correction": (
            "final state held after terminal action; recorded actions replayed without new policy selection"
        )
        if recorded is not None
        else None,
    }
    save_json(trace_path, trace)
    result = {
        "inputs": inputs,
        "outputs": {target.name: digest(target), trace_path.name: digest(trace_path)},
        "frames": frames,
        "episode_lengths": [len(e["transitions"]) for e in episodes],
        "raw_returns": [e["raw_return"] for e in episodes],
    }
    save_json(receipt, result)
    print(json.dumps({"name": name, **result}, ensure_ascii=False), flush=True)
    return result


def main() -> None:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    torch.set_num_threads(1)
    OUT.mkdir(parents=True, exist_ok=True)
    for spec in SPECS:
        render(spec, redraw_recorded="--redraw-recorded" in sys.argv)


if __name__ == "__main__":
    main()

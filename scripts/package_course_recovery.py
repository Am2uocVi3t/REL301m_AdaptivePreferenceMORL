#!/usr/bin/env python3
"""Package replacement policies, evidence, report and D-only Windows installers."""

from __future__ import annotations

import base64
import csv
import hashlib
import io
import json
import shutil
import sys
import zipfile
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.run_recovery_demo import PLAN, build_jobs, digest
from src.evaluation.protocol import load_protocol, protocol_hash

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/REL301m_Course_Recovery_20261101"


def native_wheel() -> tuple[Path, dict]:
    receipt = json.loads((ROOT / "artifacts/runtime/box2d-native-source.json").read_text())
    archive = ROOT / "artifacts/runtime" / receipt["url"].rsplit("/", 1)[-1]
    if digest(archive) != receipt["sha256"]:
        raise ValueError("Native Box2D source archive changed")
    # Installed files were extracted from this verified conda-forge archive.
    site = ROOT / ".venv/Lib/site-packages"
    dist = "box2d_py-2.3.8.dist-info"
    files = {
        path.relative_to(site).as_posix(): path.read_bytes()
        for folder in (site / "Box2D", site / dist)
        for path in folder.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.name not in {"RECORD", "INSTALLER", "REQUESTED", "direct_url.json"}
    }
    original = list(csv.reader(io.StringIO((site / dist / "RECORD").read_text())))
    for name, recorded, _ in original:
        if name in files and recorded:
            actual = base64.urlsafe_b64encode(hashlib.sha256(files[name]).digest()).rstrip(b"=").decode()
            if recorded != "sha256=" + actual:
                raise ValueError(f"Native Box2D installed file changed: {name}")
    files[dist + "/RECOVERY_PROVENANCE.json"] = json.dumps(
        {
            "source_url": receipt["url"],
            "source_sha256": receipt["sha256"],
            "operation": "Repacked verified exact-version binary; native code unmodified",
        },
        indent=2,
    ).encode()
    records = [
        [
            name,
            "sha256=" + base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode(),
            str(len(data)),
        ]
        for name, data in sorted(files.items())
    ]
    records.append([dist + "/RECORD", "", ""])
    buffer = io.StringIO(newline="")
    csv.writer(buffer, lineterminator="\n").writerows(records)
    files[dist + "/RECORD"] = buffer.getvalue().encode()
    wheel = ROOT / "artifacts/runtime/box2d_py-2.3.8-cp311-cp311-win_amd64.whl"
    with zipfile.ZipFile(wheel, "w", zipfile.ZIP_DEFLATED) as packed:
        for name, data in sorted(files.items()):
            packed.writestr(name, data)
    return wheel, {"source_url": receipt["url"], "source_sha256": receipt["sha256"], "wheel_sha256": digest(wheel)}


def build() -> Path:
    if ROOT.drive.lower() != "d:":
        raise ValueError("Course packaging is restricted to D:")
    plan = json.loads(PLAN.read_text())
    jobs = build_jobs(plan)
    execution = json.loads((ROOT / plan["output_root"] / "execution_status.json").read_text())
    if execution["plan_sha256"] != digest(PLAN) or execution["course_evidence"] is not False:
        raise ValueError("Replacement execution does not bind the presentation-only plan")
    OUT.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    def copy(source: Path, relative: str) -> None:
        target = OUT / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        paths.append(target)

    def text(relative: str, value: str) -> None:
        target = OUT / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(value, encoding="utf-8", newline="\n")
        paths.append(target)

    environments = {}
    for job in jobs:
        record = execution["jobs"][job["id"]]
        source = ROOT / job["checkpoint"]
        if record["status"] != "complete" or digest(source) != record["checkpoint_sha256"]:
            raise ValueError("Replacement checkpoint is incomplete or changed")
        checkpoint = torch.load(source, map_location="cpu", weights_only=True)
        protocol, preferences = load_protocol(ROOT / job["protocol"], "validation")
        if checkpoint["protocol_sha256"] != protocol_hash(protocol) or checkpoint["protocol"] != protocol:
            raise ValueError("Replacement checkpoint protocol mismatch")
        if checkpoint["counters"] != {
            "training_interactions": 100000,
            "gradient_updates": 23751,
            "curriculum_evaluation_steps": 0,
            "validation_evaluation_steps": 0,
        }:
            raise ValueError("Unexpected replacement training budget")
        name = job["id"]
        target = OUT / f"checkpoints/{name}.pt"
        target.parent.mkdir(parents=True, exist_ok=True)
        torch.save(
            {"architecture": checkpoint["architecture"], "model_state_dict": checkpoint["model_state_dict"]}, target
        )
        paths.append(target)
        index = int(np.argmin(np.sum((preferences - 1 / protocol["reward_dim"]) ** 2, axis=1)))
        lunar = name == "lunar"
        environments[name] = {
            "env_id": job["environment"],
            "seed": job["presentation_seed"],
            "default_weights": preferences[index].tolist(),
            "default_validation_index": index,
            "objectives": ["Hạ cánh", "Shaping", "Tiết kiệm động cơ chính", "Tiết kiệm động cơ phụ"]
            if lunar
            else ["Quặng 1", "Quặng 2", "Tiết kiệm nhiên liệu"],
            "actions": ["Không đốt", "Động cơ trái", "Động cơ chính", "Động cơ phải"]
            if lunar
            else ["Khai thác", "Rẽ trái", "Rẽ phải", "Tăng tốc", "Phanh", "Không làm gì"],
            "reward_scale": protocol["reward_scale"],
            "gamma": protocol["return_definition"]["gamma"],
            "nominal": {
                "constructor_kwargs": {
                    "gravity": -10.0,
                    "enable_wind": False,
                    "wind_power": 0.0,
                    "turbulence_power": 0.0,
                }
            }
            if lunar
            else {"constructor_kwargs": {}},
            "algorithm": "uniform-pcqn",
            "training_seed": job["training_seed"],
            "training_step": 100000,
            "weights_file": f"checkpoints/{name}.pt",
            "weights_sha256": digest(target),
            "source_checkpoint": job["checkpoint"],
            "source_sha256": digest(source),
            "source_protocol_sha256": protocol_hash(protocol),
            "training_provenance": checkpoint["provenance"],
            "evidence_role": "presentation_replacement_only",
            "model_origin": "new_training_not_recovered_historical_weights",
            "caveat": "Model Uniform-PCQN mới, 100.000 bước để phục hồi demo; không phải checkpoint cũ hoặc benchmark. "
            + (
                "Không đảm bảo hạ cánh thành công."
                if lunar
                else (
                    "Minecart lịch sử chưa đạt qualification; model trình diễn mới có thể zero ore. "
                    "Không dựng thành công giả."
                )
            ),
        }
    for name in ("index.html", "style.css", "app.js", "renderer.js"):
        copy(ROOT / "demo/interactive" / name, "website/" + name)
    for name in ("launch.py", "START_DEMO.sh"):
        copy(ROOT / "demo/interactive" / name, name)
    for folder in ("src/demo", "src/models", "src/envs"):
        for path in (ROOT / folder).glob("*.py"):
            copy(path, path.relative_to(ROOT).as_posix())
    text("src/__init__.py", "")
    copy(ROOT / "outputs/course-report/REL301m_Course_Report.pdf", "docs/Bao_cao.pdf")
    copy(ROOT / "outputs/course-report/Huong_dan_Demo.pdf", "docs/Huong_dan.pdf")
    copy(ROOT / "paper/course-recovery/REPORT.md", "docs/REPORT.md")
    copy(ROOT / "paper/course-recovery/GUIDE_VI.md", "docs/GUIDE_VI.md")
    for name in ("PAPER_CLAIM_AUDIT.json", "PAPER_CLAIM_AUDIT.md", "PAPER_CLAIM_AUDIT_PRE_REVISION.md"):
        copy(ROOT / "paper/course-recovery" / name, "docs/" + name)
    copy(PLAN, "PROVENANCE_PLAN.json")
    copy(ROOT / plan["output_root"] / "execution_status.json", "REPLACEMENT_EXECUTION.json")
    for relative in (
        "research/evidence/course_primary_validation_v1.json",
        "research/evidence/course_primary_execution_audit_v1.json",
        "research/qualification/minecart_pcqn_replay_f1.json",
        "configs/protocols/course_minecart_v0.json",
        "configs/protocols/course_mo_lunar_lander_v3.json",
        "configs/experiments/course_paired_matrix_v1.json",
    ):
        copy(ROOT / relative, relative)
    wheel, native = native_wheel()
    copy(wheel, "wheels/" + wheel.name)
    text("NATIVE_BOX2D_PROVENANCE.json", json.dumps(native, indent=2) + "\n")
    copy(ROOT / "artifacts/bootstrap/bin/uv.exe", "tools/uv.exe")
    for path in (ROOT / "artifacts/bootstrap/uv-0.13.6.dist-info/licenses").glob("*"):
        copy(path, "tools/licenses/" + path.name)
    requirements = (
        (ROOT / "demo/interactive/requirements.txt").read_text().replace("box2d-py==2.3.8", "wheels/" + wheel.name)
    )
    text("requirements-windows.txt", requirements)
    for name in ("INSTALL_D.ps1", "SET_D_ENV.ps1", "START_DEMO.ps1", "START_DEMO.bat", "README_VI.md"):
        copy(ROOT / "demo/recovery" / name, name)
    text(
        "config.json",
        json.dumps(
            {"purpose": "interactive_inference_only", "environments": environments}, indent=2, ensure_ascii=False
        )
        + "\n",
    )
    manifest = {
        "kind": "course_recovery_inference_and_report",
        "course_evidence": False,
        "files": {path.relative_to(OUT).as_posix(): digest(path) for path in sorted(paths)},
    }
    text("MANIFEST.json", json.dumps(manifest, indent=2) + "\n")
    with zipfile.ZipFile(OUT.with_suffix(".zip"), "w", zipfile.ZIP_DEFLATED) as archive:
        for path in paths:
            archive.write(path, f"{OUT.name}/{path.relative_to(OUT).as_posix()}")
    print(OUT.with_suffix(".zip"))
    return OUT


if __name__ == "__main__":
    build()

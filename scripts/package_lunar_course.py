"""Export the audited final Lunar actor into a separate course release."""

from __future__ import annotations

import json
import shutil
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import torch

from scripts.run_minecart_onpolicy import load_state, publish, sha

OUTPUT = Path("outputs/REL301m_Course_Project_20261103_LunarPPO")
EVIDENCE = Path("research/evidence/lunar_onpolicy_specialist_v1.json")


def build():
    if OUTPUT.exists() or OUTPUT.with_suffix(".zip").exists():
        raise ValueError("Versioned release already exists; preserve it")
    evidence = json.loads(EVIDENCE.read_text())
    if not evidence["final_specialist_gate_pass"]:
        raise ValueError("Audited final pilot gate required")
    for name, expected in evidence["source_sha256"].items():
        if sha(name) != expected:
            raise ValueError(f"Audited source changed: {name}")
    source = Path("artifacts/lunar-onpolicy-specialist-v1/runs/mo-lunar-lander-v3_L_seed20265311")
    checkpoint = source / "resume_step004000000.pt"
    if sha(checkpoint) != evidence["files"][str(checkpoint)]:
        raise ValueError("Audited checkpoint changed")
    saved = load_state(source)
    base = Path("outputs/REL301m_Course_Project_20261103")
    old_manifest = json.loads((base / "MANIFEST.json").read_text())
    if any(sha(base / name) != expected for name, expected in old_manifest["files"].items()):
        raise ValueError("Prior release integrity check failed")
    shutil.copytree(base, OUTPUT, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    target = OUTPUT / "checkpoints/lunar_ppo_seed20265311.pt"
    torch.save(
        {
            "model_kind": "categorical_ppo",
            "architecture": {"state_dim": 8, "action_dim": 4, "reward_dim": 4, "width": 256},
            "model_state_dict": saved["learner"]["model"],
        },
        target,
    )
    config = json.loads((OUTPUT / "config.json").read_text())
    spec = config["environments"]["lunar"]
    spec.pop("training_provenance", None)
    spec.update(
        algorithm="Landing-specialist PPO + GAE (argmax)",
        training_seed=20265311,
        training_step=4000000,
        seed=20265321,
        default_weights=[0.7, 0.1, 0.1, 0.1],
        default_validation_index=None,
        weights_file=target.relative_to(OUTPUT).as_posix(),
        weights_sha256=sha(target),
        source_checkpoint=checkpoint.as_posix(),
        source_sha256=sha(checkpoint),
        source_protocol_sha256=sha("configs/protocols/course_mo_lunar_lander_v3.json"),
        model_kind="categorical_ppo",
        action_score_kind="probability",
        training_provenance={"study_id": evidence["study_id"], "source_commit": evidence["source_commit"]},
        caveat=(
            "Lunar PPO: pilot 1 seed, final 4M; 10/10 hạ cánh đúng bãi ở preference train trong cả hai mode. "
            "Chưa xác nhận nhiều seed; chưa bảo đảm mọi preference. Uniform đáp được nhưng utility âm."
        ),
    )
    # Earlier exports inherited PCQN provenance; replace it with the actual PPO study.
    config["environments"]["mine"]["training_provenance"] = {
        "study_id": "minecart-onpolicy-confirmation-v1",
        "evidence": "research/evidence/minecart_onpolicy_confirmation_v1.json",
    }
    publish(OUTPUT / "config.json", config)
    shutil.copy2("outputs/course-report-latex/REL301m_Course_Project_Report.pdf", OUTPUT / "docs/Bao_cao.pdf")
    historical = OUTPUT / "docs/historical-release"
    historical.mkdir(exist_ok=True)
    for name in ["GUIDE_VI.md", "COURSE_PRESENTATION_VI.md", "REPORT.md", "REVIEW_STATUS.md", "Huong_dan.pdf"]:
        (OUTPUT / "docs" / name).rename(historical / name)
    shutil.copy2("docs/research/LUNAR_PPO_DEMO_GUIDE_20261103.md", OUTPUT / "docs/GUIDE_VI.md")
    shutil.copy2("artifacts/lunar-course-delivery/Huong_dan.pdf", OUTPUT / "docs/Huong_dan.pdf")
    shutil.copytree("paper/REL301m", OUTPUT / "paper/REL301m", dirs_exist_ok=True)
    for name in [
        str(EVIDENCE),
        "docs/research/LUNAR_PPO_RESULTS_20261103.md",
        "docs/research/LUNAR_PPO_SPECIALIST_V1.md",
        "configs/experiments/lunar_onpolicy_specialist_v1.json",
        "configs/protocols/course_mo_lunar_lander_v3.json",
        "research/qualification/course_report_lunar_update_20261103.json",
    ]:
        destination = OUTPUT / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(name, destination)
    html = OUTPUT / "website/index.html"
    html.write_text(
        html.read_text().replace(
            "Policy(state, w) → action. Minecart: PPO actor argmax; Lunar: legacy Q ensemble.",
            "Policy(state, w) → action. PPO actor argmax: Minecart 3 seeds; Lunar specialist 1 seed.",
        ),
        encoding="utf-8",
    )
    (OUTPUT / "README_VI.md").write_text(
        "# REL301m — Lunar PPO delivery, 03/11/2026\n\n"
        "Báo cáo theo mẫu nhóm: docs/Bao_cao.pdf. Chạy START_DEMO.bat hoặc launch.py.\n\n"
        "Lunar: final 4M seed20265311, preference train [.7,.1,.1,.1]; pilot một seed. "
        "Minecart: final 4M seed20264311, chọn seed nhỏ nhất trong 3 seed xác nhận. "
        "Cả hai dùng actor argmax, không train trong demo.\n\n"
        "Slider thay đổi đầu vào preference; không bảo đảm mọi trọng số đều tốt. Lunar uniform "
        "đáp được trong 10 ca phát triển nhưng utility âm. Không có adaptive-allocation-benefit claim.\n\n"
        "Đặt bản giải nén trên D:. Dùng INSTALL_D.ps1 để cài dependency Python 3.11 nếu cần; "
        "runtime/cache/temp theo cấu hình D:. Training monitor ở native terminal riêng. "
        "README cũ trong các tài liệu lịch sử mô tả phiên bản cũ; config.json/MANIFEST.json là bản này.\n",
        encoding="utf-8",
    )
    files = sorted(p for p in OUTPUT.rglob("*") if p.is_file() and p.name != "MANIFEST.json")
    publish(
        OUTPUT / "MANIFEST.json",
        {
            "kind": "course_report_and_minecart_lunar_ppo_demo",
            "selection": "final4M only; Minecart lowest seed; Lunar sole predeclared pilot seed",
            "minecart_training_seeds": 3,
            "lunar_training_seeds": 1,
            "lunar_specialist_gate_pass": True,
            "arbitrary_preference_guarantee": False,
            "evidence_sha256": sha(EVIDENCE),
            "base_manifest_sha256": sha(base / "MANIFEST.json"),
            "files": {p.relative_to(OUTPUT).as_posix(): sha(p) for p in files},
        },
    )
    with zipfile.ZipFile(OUTPUT.with_suffix(".zip"), "w", zipfile.ZIP_DEFLATED) as archive:
        for p in [*files, OUTPUT / "MANIFEST.json"]:
            archive.write(p, f"{OUTPUT.name}/{p.relative_to(OUTPUT).as_posix()}")
    print(OUTPUT)


if __name__ == "__main__":
    build()

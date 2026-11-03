"""Build a versioned course package with audited Minecart PPO and group report."""

from __future__ import annotations

import json
import shutil
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import torch

from scripts.run_minecart_onpolicy import load_state, publish, sha


def build():
    base = Path("outputs/REL301m_Course_Project_20261101_httpfix")
    output = Path("outputs/REL301m_Course_Project_20261103")
    if output.exists():
        raise ValueError("Versioned package already exists; preserve it")
    evidence_path = Path("research/evidence/minecart_onpolicy_confirmation_v1.json")
    evidence = json.loads(evidence_path.read_text())
    if not evidence["all_seed_both_mode_both_profile_gate_pass"]:
        raise ValueError("Audited confirmation required")
    shutil.copytree(base, output, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    config = json.loads((output / "config.json").read_text())
    seeds = sorted(j["seed"] for j in evidence["jobs"])
    for seed in seeds:
        source = Path("artifacts/minecart-onpolicy-confirmation-v1/runs") / f"minecart-v0_G_seed{seed}"
        saved = load_state(source)
        checkpoint = source / "resume_step004000000.pt"
        if sha(checkpoint) != next(j for j in evidence["jobs"] if j["seed"] == seed)["files"][str(checkpoint)]:
            raise ValueError("Audited source checkpoint changed")
        target = output / f"checkpoints/mine_seed{seed}.pt"
        torch.save(
            {
                "model_kind": "categorical_ppo",
                "architecture": {"state_dim": 7, "action_dim": 6, "reward_dim": 3, "width": 256},
                "model_state_dict": saved["learner"]["model"],
            },
            target,
        )
    spec = config["environments"]["mine"]
    spec.update(
        algorithm="Uniform-preference PPO (argmax)",
        training_seed=seeds[0],
        training_step=4000000,
        seed=20264431,
        default_weights=[0.45, 0.45, 0.1],
        default_validation_index=None,
        weights_file=f"checkpoints/mine_seed{seeds[0]}.pt",
        model_kind="categorical_ppo",
        action_score_kind="probability",
        source_checkpoint=f"artifacts/minecart-onpolicy-confirmation-v1/runs/minecart-v0_G_seed{seeds[0]}/resume_step004000000.pt",
        caveat=(
            "Minecart PPO: gate hai profile đã đạt ở 3 seed. Demo chọn seed nhỏ nhất, không chọn điểm tốt nhất. "
            "Chưa bảo đảm mọi preference/dynamics; không chứng minh adaptive allocation."
        ),
    )
    spec["weights_sha256"] = sha(output / spec["weights_file"])
    spec["source_sha256"] = sha(spec["source_checkpoint"])
    config["environments"]["lunar"]["caveat"] = (
        "Lunar legacy PCQN: chưa đạt tiêu chí hạ cánh ổn định. "
        "Pilot PPO mới chưa có kết quả; đây không phải model PPO mới."
    )
    publish(output / "config.json", config)
    for relative in ["src/demo/runtime.py", "src/demo/onpolicy.py", "src/demo/server.py", "src/models/onpolicy.py"]:
        shutil.copy2(relative, output / relative)
    shutil.copy2("outputs/course-report-latex/REL301m_Course_Project_Report.pdf", output / "docs/Bao_cao.pdf")
    shutil.copytree("paper/REL301m", output / "paper/REL301m", dirs_exist_ok=True)
    for relative in [
        str(evidence_path),
        "research/evidence/minecart_onpolicy_conditional_v1.json",
        "research/evidence/minecart_onpolicy_specialist_v1.json",
        "docs/research/ONPOLICY_CONFIRMATION_RESULTS_20261103.md",
        "outputs/course-report-latex/minecart_confirmation.pdf",
    ]:
        destination = output / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(relative, destination)
    html = output / "website/index.html"
    html.write_text(
        html.read_text().replace(
            "Q(state, w) → action. Ensemble mean, greedy.",
            "Policy(state, w) → action. Minecart: PPO actor argmax; Lunar: legacy Q ensemble.",
        ),
        encoding="utf-8",
    )
    (output / "README_VI.md").write_text(
        "# REL301m — cập nhật 03/11/2026\n\nBáo cáo theo mẫu nhóm: docs/Bao_cao.pdf.\n"
        "Minecart dùng final4M PPO seed20264311, chọn seed nhỏ nhất, không best-score. "
        "Cả3 seed đã qua gate hai profile; raw evidence kèm theo. Lunar vẫn là PCQN cũ, chưa qualified.\n"
        "Chạy START_DEMO.bat hoặc launch.py; chỉ inference. Training được theo dõi ở native terminal riêng. "
        "Không bảo đảm mọi preference và chưa có adaptive-benefit claim.\n",
        encoding="utf-8",
    )
    files = sorted(p for p in output.rglob("*") if p.is_file() and p.name != "MANIFEST.json")
    publish(
        output / "MANIFEST.json",
        {
            "kind": "course_report_and_verified_minecart_ppo_demo",
            "selection": "lowest seed final4M argmax",
            "minecart_seed": seeds[0],
            "lunar_qualified": False,
            "evidence_sha256": sha(evidence_path),
            "files": {p.relative_to(output).as_posix(): sha(p) for p in files},
        },
    )
    with zipfile.ZipFile(output.with_suffix(".zip"), "w", zipfile.ZIP_DEFLATED) as archive:
        for p in [*files, output / "MANIFEST.json"]:
            archive.write(p, f"{output.name}/{p.relative_to(output).as_posix()}")
    print(output)
    return output


if __name__ == "__main__":
    build()

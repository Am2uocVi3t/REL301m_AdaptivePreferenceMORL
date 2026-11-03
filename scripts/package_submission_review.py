"""Package the current report and unchanged verified actors for course review."""

import argparse
import json
import shutil
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.run_minecart_onpolicy import publish, sha


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--base", type=Path, default=Path("outputs/REL301m_Course_Project_20261103_LunarPPO"))
    parser.add_argument("--output", type=Path, default=Path("outputs/REL301m_Course_Submission_Review_20261103"))
    args = parser.parse_args()
    base, output = args.base, args.output
    if not output.resolve().is_relative_to(Path("outputs").resolve()) or output.resolve() == Path("outputs").resolve():
        raise ValueError("Versioned package must be a child of repository outputs")
    if output.resolve().is_relative_to(base.resolve()):
        raise ValueError("New release must not be nested inside its preserved base")
    if output.exists() or output.with_suffix(".zip").exists():
        raise ValueError("Preserve existing versioned review release")
    manifest = json.loads((base / "MANIFEST.json").read_text())
    assert all(sha(base / name) == digest for name, digest in manifest["files"].items())
    shutil.copytree(base, output, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copy2("outputs/course-report-latex/REL301m_Course_Project_Report.pdf", output / "docs/Bao_cao.pdf")
    shutil.copytree("paper/REL301m", output / "paper/REL301m", dirs_exist_ok=True)
    shutil.copytree("research/literature", output / "research/literature", dirs_exist_ok=True)
    for name in [
        "lunar_confirmation.pdf",
        "preference_diagnosis.pdf",
        "minecart_confirmation.pdf",
        "recovered_learning_curves.pdf",
    ]:
        destination = output / "outputs/course-report-latex" / name
        destination.parent.mkdir(exist_ok=True, parents=True)
        shutil.copy2(Path("outputs/course-report-latex") / name, destination)
    for name in [
        "research/evidence/lunar_onpolicy_confirmation_v1.json",
        "research/evidence/ppo_demo_preference_diagnosis_v1.json",
        "docs/research/LUNAR_CONFIRMATION_RESULTS_20261103.md",
        "docs/research/PPO_PREFERENCE_DIAGNOSIS_20261103.md",
        "docs/research/COURSE_TALK_VI_20261103.md",
        "docs/research/RESEARCH_REFERENCE_REVIEW_20261103.md",
        "research/qualification/research_reference_review_20261103.json",
    ]:
        destination = output / name
        destination.parent.mkdir(exist_ok=True, parents=True)
        shutil.copy2(name, destination)
    (output / "README_VI.md").write_text(
        "# REL301m — gói review nộp môn, 03/11/2026\n\n"
        "Report hiện tại: docs/Bao_cao.pdf; hình và nguồn LaTeX kèm theo. "
        "Kịch bản trình bày ở docs/research/COURSE_TALK_VI_20261103.md.\n\n"
        "Model demo giữ nguyên bản đã kiểm tra: Lunar pilot seed20265311 và Minecart seed20264311. "
        "Report bổ sung kết quả hai fresh seed Lunar; chúng không được âm thầm thay vào demo. "
        "Không chọn model theo điểm tốt nhất. Cả hai panel dùng actor argmax.\n\n"
        "Giải nén trên D:, dùng INSTALL_D.ps1 nếu chưa có dependency Python3.11; "
        "sau đó START_DEMO.bat. Đọc docs/GUIDE_VI.md. Không cần training hoặc API key.\n\n"
        "Đây là gói review kỹ thuật, chưa xác nhận rubric/hạn nộp. "
        "Không bảo đảm mọi preference; adaptive-allocation advantage và dynamics robustness chưa được chứng minh. "
        "Chưa có slide PPTX/video mới; tài liệu lịch sử được ghi nhãn riêng.\n",
        encoding="utf-8",
    )
    files = sorted(p for p in output.rglob("*") if p.is_file() and p.name != "MANIFEST.json")
    publish(
        output / "MANIFEST.json",
        {
            "kind": "course_submission_review",
            "base_manifest_sha256": sha(base / "MANIFEST.json"),
            "model_weights_unchanged": True,
            "lunar_demo_seed": 20265311,
            "minecart_demo_seed": 20264311,
            "lunar_confirmation_seeds_in_report": [20266311, 20266312],
            "lecturer_acceptance_confirmed": False,
            "files": {p.relative_to(output).as_posix(): sha(p) for p in files},
        },
    )
    with zipfile.ZipFile(output.with_suffix(".zip"), "w", zipfile.ZIP_DEFLATED) as archive:
        for p in [*files, output / "MANIFEST.json"]:
            archive.write(p, f"{output.name}/{p.relative_to(output).as_posix()}")
    print(output)


if __name__ == "__main__":
    main()

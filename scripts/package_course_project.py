"""Package the verified LaTeX course report, retained evidence and inference demo."""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.analyze_envelope_feasibility import audit
from src.utils.provenance import write_json

ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build() -> Path:
    cohort = audit(
        ROOT / "artifacts/envelope-feasibility-v1", ROOT / "configs/experiments/envelope_feasibility_v1.json"
    )
    report = ROOT / "outputs/course-report-latex/REL301m_Course_Project_Report.pdf"
    if not report.is_file():
        raise FileNotFoundError("Compile and inspect the current LaTeX PDF first")
    base = ROOT / "outputs/REL301m_Course_Recovery_20261101"
    old_manifest = json.loads((base / "MANIFEST.json").read_text())
    for name, expected in old_manifest["files"].items():
        if digest(base / name) != expected:
            raise ValueError(f"Recovery package changed: {name}")
    output = ROOT / "outputs/REL301m_Course_Project_20261101"
    shutil.copytree(base, output, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copy2(report, output / "docs/Bao_cao.pdf")
    for name in ("PAPER_CLAIM_AUDIT.json", "PAPER_CLAIM_AUDIT.md", "PAPER_CLAIM_AUDIT_PRE_REVISION.md"):
        history = output / "docs/historical-review"
        history.mkdir(exist_ok=True)
        shutil.move(str(output / "docs" / name), str(history / name))
    shutil.copytree(ROOT / "paper/REL301m", output / "paper/REL301m", dirs_exist_ok=True)
    for name in ("library.bib",):
        destination = output / "research/literature" / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / "research/literature" / name, destination)
    for relative in (
        "research/evidence/envelope_feasibility_v1.json",
        "configs/experiments/envelope_feasibility_v1.json",
        "docs/research/COURSE_COMPLETION_SCOPE_V2.md",
        "docs/GPU_COURSE_RUNTIME.md",
        "docs/COURSE_PRESENTATION_VI.md",
        "research/qualification/cuda_course_runtime_20261101.json",
        "outputs/course-report-latex/recovered_learning_curves.pdf",
    ):
        destination = output / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, destination)
    for seed in (20261121, 20261122, 20261123):
        source = ROOT / "artifacts/envelope-feasibility-v1" / f"seed{seed}"
        destination = output / "research/envelope-feasibility-v1" / f"seed{seed}"
        destination.mkdir(parents=True, exist_ok=True)
        for pattern in ("*.tar", "*.json"):
            for path in source.glob(pattern):
                shutil.copy2(path, destination / path.name)
    (output / "docs/REPORT.md").write_text(
        "# Báo cáo hiện tại\n\nBản chính: Bao_cao.pdf, biên dịch từ mẫu LaTeX của nhóm ở paper/REL301m.\n"
        "Bản Markdown recovery trước đây đã được thay bằng báo cáo LaTeX này.\n"
        "Ba seed Envelope đã chạy đủ ngân sách; xem bảng trong PDF và raw tensors trong research/evidence.\n"
        "Các model dùng trong app vẫn là Uniform-PCQN thay thế, không phải Envelope hoặc weights lịch sử.\n"
        "Full matrix/ablations/final test của proposal gốc chưa hoàn tất.\n",
        encoding="utf-8",
    )
    (output / "docs/REVIEW_STATUS.md").write_text(
        "# Review scope\n\nThe LaTeX report has deterministic numerical/source checks and visual inspection.\n"
        "No independent final semantic-review PASS is claimed. The historical-review directory\n"
        "contains reviews of the earlier recovery report only (pre-revision WARN and later quota ERROR).\n"
        "They are not reviews of this new LaTeX report or Envelope cohort.\n",
        encoding="utf-8",
    )
    readme = output / "README_VI.md"
    readme.write_text(
        "# REL301m — báo cáo theo mẫu nhóm và demo\n\n"
        "Báo cáo: docs/Bao_cao.pdf. Nguồn sửa được: paper/REL301m/main.tex.\n"
        "Nguồn BibTeX: research/literature/library.bib; hình kết quả ở outputs/course-report-latex.\n"
        "Dữ liệu 3 seed Envelope và 6 checkpoint mới đi kèm, tách khỏi models của app.\n"
        "Mỗi seed chạy đủ 100.000 bước; final test không được dùng. Đây là feasibility, không phải\n"
        "so sánh adaptive với baseline. Original proposal còn thiếu ablations/final test.\n\n"
        + (base / "README_VI.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    files = sorted(path for path in output.rglob("*") if path.is_file() and path.name != "MANIFEST.json")
    manifest = {
        "kind": "course_project_latex_report_evidence_and_inference",
        "demo_models_are_comparative_evidence": False,
        "full_original_proposal_complete": False,
        "new_cohort": {
            key: cohort[key]
            for key in (
                "study_id",
                "audit",
                "training_interactions",
                "gradient_updates",
                "episodes",
                "validation_steps",
                "final_test_steps",
            )
        },
        "files": {path.relative_to(output).as_posix(): digest(path) for path in files},
    }
    write_json(output / "MANIFEST.json", manifest)
    archive_path = output.with_suffix(".zip")
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in [*files, output / "MANIFEST.json"]:
            archive.write(path, f"{output.name}/{path.relative_to(output).as_posix()}")
    print(archive_path)
    return output


if __name__ == "__main__":
    build()

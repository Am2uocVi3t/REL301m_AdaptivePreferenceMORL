"""Copy the English hand-in to the established desktop folder, preserving older files."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    desktop = (
        Path(os.environ.get("USERPROFILE", "C:/Users/ghcoo")) / "OneDrive/Desktop"
        if os.name == "nt"
        else Path("/mnt/c/Users/ghcoo/OneDrive/Desktop")
    )
    destination = desktop / "REL301m_Final_Defense/English_Submission_20261112"
    if destination.exists():
        raise ValueError("Delivery already exists; preserve it and use a new version")
    report = ROOT / "outputs/english-course-report-20261112"
    demo = ROOT / "outputs/REL301m_English_Demo_20261112"
    for source in [report / "REL301m_English_Course_Report.pdf", report / "REL301m_English_Report_Editable_Source.zip"]:
        if not source.is_file():
            raise FileNotFoundError(source)
    if not (demo / "MANIFEST.json").is_file():
        raise FileNotFoundError("Build and verify the English demo first")
    destination.mkdir(parents=True)
    for name in ["REL301m_English_Course_Report.pdf", "REL301m_English_Report_Editable_Source.zip"]:
        shutil.copy2(report / name, destination / name)
    shutil.copytree(demo, destination / "English_Demo", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    (destination / "OPEN_ENGLISH_DEMO.bat").write_text(
        '@echo off\r\nset "REL301M_PYTHON=C:\\REL301m_Demo\\.venv\\Scripts\\python.exe"\r\n'
        'call "%~dp0English_Demo\\START_DEMO.bat"\r\n',
        encoding="ascii",
    )
    (destination / "README.md").write_text(
        "# REL301m — English submission\n\n"
        "Open REL301m_English_Course_Report.pdf. The ZIP contains editable LaTeX sources and figures.\n\n"
        "On this laptop, OPEN_ENGLISH_DEMO.bat uses the existing Python 3.11 demo runtime. "
        "Open http://127.0.0.1:8765; Ctrl+C stops the server. On another machine, "
        "install the dependencies and follow English_Demo/README.md.\n\n"
        "Models are unchanged. No new training/final-test or video. Older delivery files are preserved.\n",
        encoding="utf-8",
    )
    print(destination)


if __name__ == "__main__":
    main()

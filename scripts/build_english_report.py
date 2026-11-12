"""Build the English report from recorded evidence; never launch experiments."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compiler", default="tectonic", help="Path to an existing Tectonic installation")
    parser.add_argument("--bundle", default="https://data1b.fullyjustified.net/tlextras-2022.0r0.tar")
    parser.add_argument("--output", type=Path, default=ROOT / "outputs/english-course-report-20261112")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(exist_ok=True, parents=True)
    for script in [
        "plot_course_validation.py",
        "plot_onpolicy_confirmation.py",
        "plot_lunar_confirmation.py",
        "plot_preference_diagnosis.py",
    ]:
        subprocess.run([sys.executable, str(ROOT / "scripts" / script)], cwd=ROOT, check=True)  # nosec B603
    subprocess.run(  # nosec B603
        [
            sys.executable,
            str(ROOT / "scripts/audit_course_report.py"),
            "--allow-text-line-endings",
            "--write",
            str(output / "source-audit.json"),
        ],
        cwd=ROOT,
        check=True,
    )
    with (output / "build.log").open("w", encoding="utf-8") as log:
        subprocess.run(  # nosec B603: explicitly selected local compiler
            [args.compiler, "-b", args.bundle, "--keep-logs", "--outdir", str(output), "paper/REL301m/main.tex"],
            cwd=ROOT,
            stdout=log,
            stderr=subprocess.STDOUT,
            check=True,
        )
    target = output / "REL301m_English_Course_Report.pdf"
    shutil.copy2(output / "main.pdf", target)
    archive = output / "REL301m_English_Report_Editable_Source.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for folder in [ROOT / "paper/REL301m", ROOT / "research/literature"]:
            for path in sorted(folder.rglob("*")):
                if path.is_file() and path.suffix.lower() in {".tex", ".bib", ".png", ".md", ".json"}:
                    bundle.write(path, path.relative_to(ROOT))
        for name in [
            "recovered_learning_curves",
            "minecart_confirmation",
            "lunar_confirmation",
            "preference_diagnosis",
        ]:
            path = ROOT / "outputs/course-report-latex" / f"{name}.pdf"
            bundle.write(path, path.relative_to(ROOT))
        bundle.write(ROOT / "scripts/build_english_report.py", "scripts/build_english_report.py")
        bundle.write(ROOT / "paper/REL301m/BUILD_ENGLISH.md", "README.md")
    print(target)
    print(archive)


if __name__ == "__main__":
    main()

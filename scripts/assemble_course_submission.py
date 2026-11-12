"""Assemble the assessed Group 2 package, enforcing the Form's decimal 10 MB limit."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

REPOSITORY = "https://github.com/Am2uocVi3t/REL301m_AdaptivePreferenceMORL/tree/codex/course-submission-20261112"
TITLE = "Hard, Uncertain, or Learnable? A Controlled Study of Preference Allocation in Preference-Conditioned MORL"


def assemble(artifacts: Path, target: Path) -> dict:
    if target.exists():
        raise FileExistsError(f"Preserve the existing delivery and choose a new target: {target}")
    names = ["REL301m_Report.pdf", "REL301m_Slides.pdf", "REL301m_Demo.mp4"]
    files = {}
    for name in names:
        source = artifacts / name
        if not source.is_file():
            raise FileNotFoundError(source)
        files[name] = {"bytes": source.stat().st_size, "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
    manifest = {"group": 2, "title": TITLE, "repository": REPOSITORY, "files": files}
    readme = (
        f"REL301m - Group 2\n{TITLE}\n\n"
        "REL301m_Report.pdf: English report, 26 pages; text preserved during image optimization.\n"
        "REL301m_Slides.pdf: 12 English slides, fixed 16:9 layout.\n"
        "REL301m_Demo.mp4: narrated real-application demonstration, 720p H.264/AAC.\n"
        "The original 1080p narrated recording is available from the repository README.\n\n"
        f"Source code and editable report/slide sources: {REPOSITORY}\n\n"
        "The original final-test gate remains locked. Adaptive-allocation superiority is unestablished.\n"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in names:
            archive.write(artifacts / name, name)
        archive.writestr("README.txt", readme)
        archive.writestr("MANIFEST.json", json.dumps(manifest, indent=2) + "\n")
    with zipfile.ZipFile(target) as archive:
        if archive.testzip() is not None:
            raise ValueError("ZIP checksum validation failed")
        for name, info in files.items():
            if hashlib.sha256(archive.read(name)).hexdigest() != info["sha256"]:
                raise ValueError(f"ZIP content hash differs: {name}")
    size = target.stat().st_size
    if size >= 10_000_000:
        raise ValueError(f"Package exceeds the decimal 10 MB limit: {size} bytes. Optimize and use a new target.")
    return {**manifest, "zip_bytes": size, "zip_sha256": hashlib.sha256(target.read_bytes()).hexdigest()}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(assemble(args.artifacts, args.target), indent=2))

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import pytest

from scripts.verify_monday_package import ROOT, verify


@pytest.fixture
def package(tmp_path: Path) -> Path:
    directory = tmp_path / "team"
    directory.mkdir()
    source = json.loads((ROOT / "research/qualification/minecart_pcqn_backbone_v2.json").read_text())
    (directory / "index.html").write_text('<main id="results"><a href="#results">Results</a></main>')
    (directory / "data.js").write_text("window.DEMO_DATA = " + json.dumps({"v2": source}) + ";\n")
    return directory


def archive(directory: Path) -> None:
    files = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in directory.iterdir()
        if path.name != "MANIFEST.json"
    }
    (directory / "MANIFEST.json").write_text(json.dumps({"files": files}))
    with zipfile.ZipFile(directory.with_suffix(".zip"), "w") as packed:
        for path in directory.iterdir():
            packed.write(path, str(Path(directory.name) / path.name))


def test_portable_manifest_and_zip_agree(package: Path) -> None:
    archive(package)
    assert verify(package)["status"] == "PASS"


def test_tampered_artifact_is_rejected(package: Path) -> None:
    archive(package)
    (package / "data.js").write_text("tampered")
    with pytest.raises(ValueError, match="Hash mismatch"):
        verify(package)


def test_broken_local_links_are_rejected(package: Path) -> None:
    (package / "index.html").write_text('<a href="missing.pdf">PDF</a>')
    archive(package)
    with pytest.raises(ValueError, match="Broken local link"):
        verify(package)


def test_unexpected_archive_content_is_rejected(package: Path) -> None:
    archive(package)
    with zipfile.ZipFile(package.with_suffix(".zip"), "a") as packed:
        packed.writestr("team/private.txt", "not in allowlist")
    with pytest.raises(ValueError, match="Unexpected or missing ZIP"):
        verify(package)


def test_suspected_key_is_not_shareable(package: Path) -> None:
    (package / "notes.md").write_text("sk-ant-" + "x" * 20)
    archive(package)
    with pytest.raises(ValueError, match="credential"):
        verify(package)

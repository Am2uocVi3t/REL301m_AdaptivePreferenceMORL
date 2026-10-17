#!/usr/bin/env python3
"""Verify portable package hashes, links and evidence without invoking a browser."""

from __future__ import annotations

import hashlib
import json
import re
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "outputs/monday-team/REL301m_Team_Review_2026-10-19"


class Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.ids: set[str] = set()

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if "id" in attributes:
            self.ids.add(attributes["id"])
        for key in ("href", "src"):
            if key in attributes:
                self.links.append(attributes[key])


def verify(directory: Path) -> dict:
    manifest = json.loads((directory / "MANIFEST.json").read_text())
    for name, digest in manifest["files"].items():
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Unsafe package path")
        if hashlib.sha256((directory / relative).read_bytes()).hexdigest() != digest:
            raise ValueError(f"Hash mismatch: {name}")
    parser = Links()
    parser.feed((directory / "index.html").read_text())
    for link in parser.links:
        parsed = urlsplit(link)
        if parsed.scheme or parsed.netloc:
            raise ValueError("Demo must not depend on network assets")
        if parsed.path and not (directory / unquote(parsed.path)).is_file():
            raise ValueError(f"Broken local link: {link}")
        if not parsed.path and parsed.fragment and parsed.fragment not in parser.ids:
            raise ValueError(f"Broken section: {link}")
    snapshot = (directory / "data.js").read_text()
    data = json.loads(snapshot.removeprefix("window.DEMO_DATA = ").removesuffix(";\n"))
    source = json.loads((ROOT / "research/qualification/minecart_pcqn_backbone_v2.json").read_text())
    if data["v2"] != source:
        raise ValueError("Demo data differs from the qualification")
    archive = directory.with_suffix(".zip")
    with zipfile.ZipFile(archive) as package:
        expected = {str(Path(directory.name) / name) for name in [*manifest["files"], "MANIFEST.json"]}
        if set(package.namelist()) != expected:
            raise ValueError("Unexpected or missing ZIP contents")
        for name in package.namelist():
            if any(part in {".git", ".env", ".aris", "checkpoints"} for part in Path(name).parts):
                raise ValueError("Private/runtime files in ZIP")
            if package.read(name) != (directory / Path(name).relative_to(directory.name)).read_bytes():
                raise ValueError("ZIP bytes differ from final artifacts")
    for relative in manifest["files"]:
        path = directory / relative
        if path.suffix in {".html", ".js", ".json", ".md", ".tex", ".bib", ".css"}:
            text = path.read_text()
            if re.search(r"sk-(?:ant-)?[A-Za-z0-9_-]{16,}|-----BEGIN .*PRIVATE KEY-----", text):
                raise ValueError("Suspected credential in shareable text")
    return {
        "status": "PASS",
        "files_hashed": len(manifest["files"]),
        "html_links_checked": len(parser.links),
        "zip_matches_final_files": True,
        "real_qualification_snapshot_matches": True,
        "credential_scan": "heuristic_clean",
        "browser_rendering_verified": False,
    }


if __name__ == "__main__":
    print(json.dumps(verify(PACKAGE), indent=2))

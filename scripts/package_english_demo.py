"""Create an English inference package without modifying any frozen policies."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE = ROOT / "outputs/REL301m_Course_Reference_Review_20261103"
DEFAULT_OUTPUT = ROOT / "outputs/REL301m_English_Demo_20261112"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(base: Path, output: Path, report: Path | None = None) -> Path:
    if output.exists():
        raise ValueError("Output already exists; preserve the existing package and choose a new directory")
    config = json.loads((base / "config.json").read_text(encoding="utf-8"))
    for spec in config["environments"].values():
        if digest(base / spec["weights_file"]) != spec["weights_sha256"]:
            raise ValueError("Base policy hash mismatch")
    output.mkdir(parents=True)
    shutil.copytree(base / "src", output / "src", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copytree(
        ROOT / "src/demo",
        output / "src/demo",
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    (output / "website").mkdir()
    for asset in ["index.html", "app.js", "renderer.js", "style.css", "guide.html"]:
        shutil.copy2(ROOT / "demo/interactive" / asset, output / "website" / asset)
    shutil.copy2(ROOT / "demo/interactive/launch.py", output / "launch.py")
    shutil.copy2(ROOT / "demo/interactive/requirements.txt", output / "requirements.txt")
    shutil.copy2(ROOT / "demo/interactive/README_EN.md", output / "README.md")
    (output / "START_DEMO.bat").write_text(
        '@echo off\r\npushd "%~dp0"\r\n'
        'if defined REL301M_PYTHON ("%REL301M_PYTHON%" launch.py %*) else '
        '(if exist ".venv\\Scripts\\python.exe" (.venv\\Scripts\\python.exe launch.py %*) '
        "else (py -3.11 launch.py %*))\r\npopd\r\npause\r\n",
        encoding="ascii",
    )
    for name, spec in config["environments"].items():
        target = output / spec["weights_file"]
        target.parent.mkdir(exist_ok=True, parents=True)
        shutil.copy2(base / spec["weights_file"], target)
        if name == "lunar":
            spec["objectives"] = ["Landing outcome", "Shaping", "Main-engine cost", "Side-engine cost"]
            spec["actions"] = ["Coast", "Left engine", "Main engine", "Right engine"]
            spec["caveat"] = (
                "Lunar PPO: this demo uses the single-seed specialist pilot (20265311, final 4M). "
                "Its trained-profile gate passed 10/10 in both modes. Separate prospective confirmation "
                "used two other seeds; those models are not shown here. Arbitrary preferences are not guaranteed."
            )
        elif name == "mine":
            spec["objectives"] = ["Ore 1 delivered", "Ore 2 delivered", "Fuel cost"]
            spec["actions"] = ["Mine", "Turn left", "Turn right", "Accelerate", "Brake", "Idle"]
            spec["caveat"] = (
                "Minecart PPO: the two-profile task gate passed across three training seeds. "
                "This demo uses the lowest seed (20264311), not the highest score. "
                "No arbitrary-preference, dynamics-robustness or adaptive-allocation advantage is established."
            )
    config["interface_language"] = "en"
    config["localization"] = {
        "base_config_sha256": digest(base / "config.json"),
        "policy_parameters_changed": False,
        "training_interactions": 0,
        "final_test_steps": 0,
    }
    (output / "config.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    if report is not None:
        (output / "docs").mkdir()
        shutil.copy2(report, output / "docs/Bao_cao.pdf")
    manifest = {p.relative_to(output).as_posix(): digest(p) for p in output.rglob("*") if p.is_file()}
    (output / "MANIFEST.json").write_text(
        json.dumps({"kind": "english_inference_demo", "files": manifest}, indent=2) + "\n", encoding="utf-8"
    )
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, default=DEFAULT_BASE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    print(build(args.base, args.output, args.report))

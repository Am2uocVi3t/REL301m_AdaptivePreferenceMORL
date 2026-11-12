"""Package the local recording desk and existing demo without replacing older deliveries."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.recording_studio import resolve_ffmpeg

ROOT = Path(__file__).resolve().parents[1]


def package(media: Path, output: Path, ffmpeg: str) -> None:
    if output.exists():
        raise ValueError("Versioned package already exists; choose a new output and preserve it")
    if not media.is_file():
        raise FileNotFoundError(media)
    for relative in [
        "demo/recording/index.html",
        "demo/recording/style.css",
        "demo/recording/app.js",
        "scripts/recording_studio.py",
        "docs/course/video/SCRIPT_EN.md",
        "docs/course/video/README.md",
        "docs/course/video/recording-desk.png",
        "docs/course/video/storyboard.json",
        "research/qualification/video-studio-20261112.json",
        "paper/REL301m/Figures/0. General/fpt_logo_red_small.png",
    ]:
        target = output / relative
        target.parent.mkdir(exist_ok=True, parents=True)
        shutil.copy2(ROOT / relative, target)
    (output / "media").mkdir()
    shutil.copy2(media, output / "media/demo.mp4")
    (output / "tools").mkdir()
    (output / "tools/ffmpeg-path.txt").write_text(ffmpeg, encoding="utf-8")
    (output / "START_RECORDING_STUDIO.bat").write_text(
        '@echo off\r\npowershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1"\r\npause\r\n',
        encoding="ascii",
    )
    (output / "start.ps1").write_text(
        "$ErrorActionPreference='Stop'\n"
        "$python=$env:REL301M_PYTHON\n"
        "if(-not $python){$python='C:/REL301m_Demo/.venv/Scripts/python.exe'}\n"
        "if(-not (Test-Path -LiteralPath $python)){$python=(Get-Command python).Source}\n"
        "$takes=Join-Path $env:USERPROFILE 'Everything/REL301m_Recordings'\n"
        "$ffmpeg=(Get-Content -Raw (Join-Path $PSScriptRoot 'tools/ffmpeg-path.txt')).Trim()\n"
        "if(Test-Path -LiteralPath $ffmpeg){$env:FFMPEG_PATH=$ffmpeg}\n"
        "& $python (Join-Path $PSScriptRoot 'scripts/recording_studio.py') "
        "--media (Join-Path $PSScriptRoot 'media/demo.mp4') "
        "--output $takes --port 0 --open\n",
        encoding="utf-8",
    )
    (output / "README.md").write_text(
        "# REL301m Recording Desk\n\n"
        "Open START_RECORDING_STUDIO.bat. It opens the local desk in your browser. "
        "Keep its terminal open; Ctrl+C stops it. Python 3.11+ is required. "
        "The laptop launcher uses the existing demo interpreter and external FFmpeg runtime; "
        "no pip install is needed on this laptop. For another machine, set REL301M_PYTHON "
        "and install imageio-ffmpeg==0.6.0 into that Python, or set FFMPEG_PATH. "
        "The codec binary is not redistributed in this package.\n\n"
        "The captioned MP4 is media/demo.mp4. Its human narration has not been recorded yet. "
        "Choose My microphone or import an audio file, select Record, read the editable script, "
        "then stop, review and export MP4. Original takes are downloadable before export.\n\n"
        "Text size and scrolling speed are adjustable. The prompter is not recorded. "
        "Optional music ducks under your voice. Check the finished sound with headphones.\n\n"
        "Local exports and original uploaded takes are saved outside OneDrive at "
        "~/Everything/REL301m_Recordings. Download a finished MP4 using the desk. "
        "The app makes no provider calls or automatic publication. "
        "Synthetic audio tests do not certify your actual microphone quality.\n",
        encoding="utf-8",
    )
    files = {
        p.relative_to(output).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in output.rglob("*")
        if p.is_file()
    }
    (output / "MANIFEST.json").write_text(json.dumps({"kind": "local_recording_desk", "files": files}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--media", type=Path, default=ROOT / "outputs/video-course-20261112/demo.mp4")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ffmpeg")
    args = parser.parse_args()
    package(args.media, args.output, resolve_ffmpeg(args.ffmpeg))
    print(args.output)

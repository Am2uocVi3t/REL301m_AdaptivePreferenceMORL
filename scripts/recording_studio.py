"""Local narration desk and bounded FFmpeg export. No provider or training calls."""

from __future__ import annotations

import argparse
import hmac
import json
import mimetypes
import os
import re
import secrets
import shutil
import subprocess
import threading
import uuid
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
MAX_UPLOAD = 300 * 1024 * 1024


def resolve_ffmpeg(explicit: str | None = None) -> str:
    candidate = explicit or os.environ.get("FFMPEG_PATH") or shutil.which("ffmpeg")
    if candidate:
        return str(Path(candidate).resolve())
    try:
        import imageio_ffmpeg

        return str(imageio_ffmpeg.get_ffmpeg_exe())
    except ImportError as error:
        raise RuntimeError(
            "FFmpeg not found. Set FFMPEG_PATH or install the pinned imageio-ffmpeg dependency."
        ) from error


def spoken_script(path: Path) -> str:
    return "\n\n".join(
        p.strip()
        for p in path.read_text(encoding="utf-8").split("\n\n")
        if p.strip() and not p.lstrip().startswith(("#", "Target:"))
    )


def export_mp4(source: Path, target: Path, ffmpeg: str, log: Path) -> dict[str, Any]:
    command = [
        ffmpeg,
        "-nostdin",
        "-hide_banner",
        "-i",
        str(source),
        "-map",
        "0:v:0",
        "-map",
        "0:a:0?",
        "-vf",
        "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1",
        "-r",
        "30",
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        "-af",
        "loudnorm=I=-16:TP=-1.5:LRA=11",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-movflags",
        "+faststart",
        str(target),
    ]
    with log.open("w", encoding="utf-8") as stream:
        subprocess.run(command, stdout=stream, stderr=stream, check=True, timeout=900)  # nosec B603
    if not target.is_file() or target.stat().st_size < 100:
        raise RuntimeError("Encoder did not produce an MP4")
    # Decode the output, not merely its filename, before offering it as complete.
    checked = subprocess.run(  # nosec B603
        [ffmpeg, "-v", "error", "-i", str(target), "-f", "null", "-"],
        capture_output=True,
        text=True,
        timeout=600,
        check=True,
    )
    if checked.stderr.strip():
        raise RuntimeError("Output decoder reported errors; inspect the export log")
    return {"bytes": target.stat().st_size, "width": 1920, "height": 1080, "fps": 30, "decoded_without_errors": True}


class StudioServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, media: Path, output: Path, ffmpeg: str, port: int = 0):
        self.media, self.output, self.ffmpeg = media.resolve(), output.resolve(), ffmpeg
        self.output.mkdir(parents=True, exist_ok=True)
        self.token = secrets.token_urlsafe(32)
        self.jobs: dict[str, dict[str, Any]] = {}
        self.jobs_lock = threading.Lock()
        self.slots = threading.BoundedSemaphore(2)
        super().__init__(("127.0.0.1", port), StudioHandler)

    def encode(self, identifier: str, source: Path) -> None:
        try:
            with self.jobs_lock:
                self.jobs[identifier]["status"] = "running"
            info = export_mp4(source, self.output / f"{identifier}.mp4", self.ffmpeg, self.output / f"{identifier}.log")
            with self.jobs_lock:
                self.jobs[identifier].update(status="complete", url=f"/exports/{identifier}.mp4", **info)
        except (subprocess.SubprocessError, OSError, RuntimeError) as error:
            with self.jobs_lock:
                self.jobs[identifier].update(
                    status="failed", error=f"{type(error).__name__}: encoding failed. Original take retained."
                )
        finally:
            self.slots.release()


class StudioHandler(BaseHTTPRequestHandler):
    server: StudioServer

    def setup(self) -> None:
        super().setup()
        self.connection.settimeout(60)

    def trusted(self) -> bool:
        host = self.headers.get("Host", "")
        return (
            host in {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}
            and self.headers.get("Origin", f"http://{host}") == f"http://{host}"
        )

    def reply(self, status: int, value: dict[str, Any]) -> None:
        data = json.dumps(value).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    def file(self, path: Path) -> None:
        if not path.is_file():
            self.reply(404, {"error": "File not found"})
            return
        size = path.stat().st_size
        start, end = 0, size - 1
        header = self.headers.get("Range")
        if header:
            match = re.fullmatch(r"bytes=(\d+)-(\d*)", header)
            if not match or int(match[1]) >= size:
                self.reply(416, {"error": "Unsupported range"})
                return
            start = int(match[1])
            end = min(int(match[2]) if match[2] else size - 1, size - 1)
            if end < start:
                self.reply(416, {"error": "Invalid range"})
                return
        self.send_response(206 if header else 200)
        self.send_header("Content-Type", mimetypes.guess_type(path.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(end - start + 1))
        self.send_header("Accept-Ranges", "bytes")
        if header:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", "default-src 'self'; img-src 'self' blob:; media-src 'self' blob:;")
        self.end_headers()
        with path.open("rb") as stream:
            stream.seek(start)
            remaining = end - start + 1
            while remaining:
                data = stream.read(min(1024 * 1024, remaining))
                if not data:
                    break
                try:
                    self.wfile.write(data)
                except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                    # Seeking or closing the video cancels a streaming response normally.
                    return
                remaining -= len(data)

    def do_GET(self) -> None:
        if not self.trusted():
            self.reply(403, {"error": "Local origin only"})
            return
        path = urlsplit(self.path).path
        if path == "/api/config":
            self.reply(
                200,
                {
                    "token": self.server.token,
                    "media_url": "/demo.mp4",
                    "max_upload_bytes": MAX_UPLOAD,
                    "script": spoken_script(ROOT / "docs/course/video/SCRIPT_EN.md"),
                    "timeline": (
                        json.loads(self.server.media.with_name("narration-timeline.json").read_text(encoding="utf-8"))
                        if self.server.media.with_name("narration-timeline.json").is_file()
                        else None
                    ),
                },
            )
        elif path.startswith("/api/jobs/"):
            with self.server.jobs_lock:
                value = dict(self.server.jobs.get(path.rsplit("/", 1)[-1], {"status": "missing"}))
            self.reply(200 if value["status"] != "missing" else 404, value)
        elif re.fullmatch(r"/exports/[a-f0-9]{32}\.mp4", path):
            self.file(self.server.output / path.rsplit("/", 1)[-1])
        elif path == "/demo.mp4":
            self.file(self.server.media)
        elif path == "/logo.png":
            self.file(ROOT / "paper/REL301m/Figures/0. General/fpt_logo_red_small.png")
        elif path in {"/", "/style.css", "/app.js"}:
            self.file(ROOT / "demo/recording" / ("index.html" if path == "/" else path[1:]))
        else:
            self.reply(404, {"error": "Not found"})

    def do_POST(self) -> None:
        if not self.trusted() or not hmac.compare_digest(self.headers.get("X-Studio-Token", ""), self.server.token):
            self.close_connection = True
            self.reply(403, {"error": "Local origin and session token required"})
            return
        if urlsplit(self.path).path != "/api/export":
            self.reply(404, {"error": "Not found"})
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            size = 0
        content_type = self.headers.get("Content-Type", "").split(";")[0]
        if not 1 <= size <= MAX_UPLOAD or content_type not in {"video/webm", "video/mp4"}:
            self.close_connection = True
            self.reply(400, {"error": "Expected a video/webm or video/mp4 take, up to 300 MiB"})
            return
        if not self.server.slots.acquire(blocking=False):
            self.close_connection = True
            self.reply(429, {"error": "Two exports are already running. Keep your take and retry later."})
            return
        identifier = uuid.uuid4().hex
        source = self.server.output / (identifier + (".webm" if content_type == "video/webm" else ".source.mp4"))
        try:
            with source.open("xb") as stream:
                remaining = size
                while remaining:
                    data = self.rfile.read(min(1024 * 1024, remaining))
                    if not data:
                        raise OSError("Incomplete upload")
                    stream.write(data)
                    remaining -= len(data)
        except OSError:
            self.server.slots.release()
            self.reply(400, {"error": "Upload incomplete. Original browser take is still available."})
            return
        with self.server.jobs_lock:
            self.server.jobs[identifier] = {"id": identifier, "status": "queued"}
        threading.Thread(target=self.server.encode, args=(identifier, source), daemon=True).start()
        self.reply(202, {"id": identifier})

    def log_message(self, *_args: Any) -> None:
        pass


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--media", type=Path, default=ROOT / "outputs/video-course-20261112/demo.mp4")
    parser.add_argument("--output", type=Path, default=ROOT / "outputs/video-course-20261112/takes")
    parser.add_argument("--ffmpeg")
    parser.add_argument("--port", type=int, default=8779)
    parser.add_argument("--open", action="store_true", help="Open the desk in the default browser")
    args = parser.parse_args()
    if not args.media.is_file():
        raise SystemExit("Demo video not found. Build it first, or pass --media /path/to/video.mp4")
    server = StudioServer(args.media, args.output, resolve_ffmpeg(args.ffmpeg), args.port)
    print(f"Recording Desk: http://127.0.0.1:{server.server_port} | Ctrl+C to stop", flush=True)
    if args.open:
        webbrowser.open(f"http://127.0.0.1:{server.server_port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

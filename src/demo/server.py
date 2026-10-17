from __future__ import annotations

import argparse
import hmac
import json
import mimetypes
import os
import secrets
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, cast
from urllib.parse import urlsplit

import torch

from src.demo.runtime import DemoRuntime

ASSETS = {
    "/": "website/index.html",
    "/style.css": "website/style.css",
    "/app.js": "website/app.js",
    "/renderer.js": "website/renderer.js",
    "/docs/report.pdf": "docs/Bao_cao.pdf",
    "/docs/guide.pdf": "docs/Huong_dan.pdf",
}


def make_server(root: Path, port: int = 8765) -> HTTPServer:
    runtime = DemoRuntime(root)
    token = secrets.token_urlsafe(32)

    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(5)

        def reply(self, status: int, value: Any, content_type: str = "application/json") -> None:
            data = json.dumps(value, allow_nan=False).encode() if content_type == "application/json" else value
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Cross-Origin-Resource-Policy", "same-origin")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; img-src 'self' data:; "
                "style-src 'self'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'",
            )
            self.end_headers()
            self.wfile.write(data)

        def trusted(self) -> bool:
            port = cast(HTTPServer, self.server).server_port
            hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
            host = self.headers.get("Host", "")
            origin = self.headers.get("Origin")
            return host in hosts and (origin is None or origin == f"http://{host}")

        def do_GET(self):
            if not self.trusted():
                self.reply(403, {"error": "Local origin only"})
                return
            path = urlsplit(self.path).path
            if path == "/api/config":
                self.reply(200, {"environments": runtime.specs, "token": token, "state": runtime.snapshot()})
            elif path == "/api/state":
                self.reply(200, runtime.snapshot(native=urlsplit(self.path).query == "native=1"))
            elif path == "/api/trace":
                self.reply(200, runtime.trace())
            elif path in ASSETS and (root / ASSETS[path]).is_file():
                asset = root / ASSETS[path]
                content_type = mimetypes.guess_type(asset.name)[0] or "application/octet-stream"
                self.reply(200, asset.read_bytes(), content_type)
            else:
                self.reply(404, {"error": "Not found"})

        def do_POST(self):
            if not self.trusted() or not hmac.compare_digest(self.headers.get("X-Demo-Token", ""), token):
                self.reply(403, {"error": "Local origin/token required"})
                return
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 32768 or self.headers.get_content_type() != "application/json":
                    raise ValueError("JSON payload cần trong 1..32768 bytes")
                request = json.loads(self.rfile.read(size))
                if not isinstance(request, dict):
                    raise ValueError("JSON object required")
                path = urlsplit(self.path).path
                if path == "/api/reset":
                    result = runtime.reset(
                        request.get("environment"), request.get("weights"), request.get("generation")
                    )
                elif path == "/api/tick":
                    result = runtime.tick(request)
                else:
                    self.reply(404, {"error": "Not found"})
                    return
                self.reply(200, result)
            except (ValueError, TypeError, KeyError) as error:
                self.reply(400, {"error": str(error)})
            except RuntimeError as error:
                self.reply(503, {"error": str(error)})

        def do_OPTIONS(self):
            self.reply(403, {"error": "Cross-origin requests disabled"})

        def log_message(self, *_args):
            return

    server = HTTPServer(("127.0.0.1", port), Handler)
    server.runtime = runtime  # type: ignore[attr-defined]
    return server


def main(root: Path | None = None) -> None:
    parser = argparse.ArgumentParser(description="Local frozen-policy interactive demo; inference only")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    torch.set_num_threads(1)
    root = root or Path(__file__).resolve().parents[2] / "outputs/REL301m_Interactive_Demo"
    server = make_server(root, args.port)
    print(f"MORL Lab: http://127.0.0.1:{server.server_port} | Ctrl+C để dừng | inference only", flush=True)
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        pass
    finally:
        server.runtime.close()  # type: ignore[attr-defined]
        server.server_close()


if __name__ == "__main__":
    main()

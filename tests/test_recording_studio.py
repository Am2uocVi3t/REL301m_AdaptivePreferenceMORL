from __future__ import annotations

import json
import subprocess
import threading
import time
from http.client import HTTPConnection

import pytest

from scripts.recording_studio import StudioServer, resolve_ffmpeg, spoken_script


def test_script_omits_editing_headings(tmp_path):
    path = tmp_path / "script.md"
    path.write_text("# Heading\n\nTarget: two minutes.\n\nHello, this is spoken.\n\n## Cue\n\nThank you.")
    assert spoken_script(path) == "Hello, this is spoken.\n\nThank you."


def test_local_recording_export_range_and_auth(tmp_path):
    try:
        ffmpeg = resolve_ffmpeg()
    except RuntimeError:
        pytest.skip("Recording integration requires FFmpeg")
    video = tmp_path / "fixture.mp4"
    subprocess.run(
        [
            ffmpeg,
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "color=c=navy:s=320x180:r=30",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:sample_rate=48000",
            "-t",
            "0.4",
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            str(video),
        ],
        check=True,
        capture_output=True,
    )
    server = StudioServer(video, tmp_path / "takes", ffmpeg)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    def request(method, path, body=None, headers=None):
        connection = HTTPConnection("127.0.0.1", server.server_port, timeout=30)
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        result = response.status, response.read()
        connection.close()
        return result

    try:
        status, raw = request("GET", "/api/config")
        assert status == 200
        token = json.loads(raw)["token"]
        assert json.loads(raw)["timeline"] is None
        timeline = {"reading_wpm": 95, "words": [{"word": "Hello", "start": 0, "end": 0.3}]}
        video.with_name("narration-timeline.json").write_text(json.dumps(timeline), encoding="utf-8")
        assert json.loads(request("GET", "/api/config")[1])["timeline"] == timeline
        assert request("GET", "/demo.mp4", headers={"Range": "bytes=0-9"}) == (206, video.read_bytes()[:10])
        assert request("GET", "/../AGENTS.md")[0] == 404
        assert request("POST", "/api/export", b"invalid")[0] == 403
        assert request("GET", "/api/config", headers={"Origin": "https://example.com"})[0] == 403
        status, result = request(
            "POST",
            "/api/export",
            video.read_bytes(),
            {"X-Studio-Token": token, "Content-Type": "video/mp4"},
        )
        assert status == 202
        identifier = json.loads(result)["id"]
        job = {}
        for _ in range(100):
            job = json.loads(request("GET", f"/api/jobs/{identifier}")[1])
            if job["status"] in {"complete", "failed"}:
                break
            time.sleep(0.1)
        assert job["status"] == "complete", job
        assert job["decoded_without_errors"] and job["width"] == 1920
        assert request("GET", job["url"])[0] == 200
        assert (server.output / f"{identifier}.source.mp4").read_bytes() == video.read_bytes()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

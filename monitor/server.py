"""Local read-only telemetry server. No Torch import, training or process controls."""

from __future__ import annotations

import argparse
import ctypes
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from ctypes import wintypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, cast
from urllib.parse import parse_qs, urlsplit

REPO = Path(__file__).resolve().parents[1]
ASSETS = Path(__file__).parent
JOB_NAME = re.compile(r"minecart-v0_[ABCD]_seed\d+\Z")


def shared_read(path: Path, limit: int = 5_000_000, tail: bool = False) -> str:
    """Read append-only or finalized files. Never call on rotating training JSON."""
    if sys.platform == "win32":
        import msvcrt

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.CreateFileW.argtypes = [
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            ctypes.c_void_p,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.HANDLE,
        ]
        kernel.CreateFileW.restype = wintypes.HANDLE
        handle = kernel.CreateFileW(str(path.resolve()), 0x80000000, 7, None, 3, 0, None)
        if handle == ctypes.c_void_p(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
        descriptor = msvcrt.open_osfhandle(handle, os.O_RDONLY | os.O_BINARY)
    else:
        descriptor = os.open(path, os.O_RDONLY)
    with os.fdopen(descriptor, "rb") as stream:
        size = os.fstat(stream.fileno()).st_size
        if not tail and size > limit:
            raise ValueError(f"Telemetry exceeds {limit} bytes")
        if tail:
            stream.seek(max(0, size - limit))
        return stream.read(limit).decode("utf-8", errors="replace")


def worker_state(
    declared: str, complete: bool, alive: bool | None, age: float | None, launcher_alive: bool | None = None
) -> str:
    if complete:
        return "complete"
    if alive is True:
        return "running" if age is not None and age < 60 else "stale"
    if launcher_alive is True:
        return "starting"
    if declared in ("technical_failure", "failed", "interrupted_without_resume_checkpoint"):
        return "failed"
    if declared == "pending_resume":
        return "resume pending"
    if declared == "running":
        return "interrupted" if alive is False else "unknown"
    return "pending"


class Monitor:
    def __init__(self, repo: Path = REPO):
        self.repo = repo
        self.root = repo / "artifacts/preference-recovery-p2-v1"
        self.runs = self.root / "runs"
        self.cache: dict[str, tuple[int, Any]] = {}
        self.lock = threading.Lock()
        self.last_snapshot: dict[str, Any] = {}
        self.sampled = 0.0
        self.gpu_sampled = 0.0
        self.gpu: dict[str, Any] = {"available": False}

    def read_json(self, path: Path, warnings: list[str]) -> Any:
        try:
            modified = path.stat().st_mtime_ns
            key = str(path)
            if key not in self.cache or self.cache[key][0] != modified:
                self.cache[key] = (modified, json.loads(shared_read(path)))
            return self.cache[key][1]
        except FileNotFoundError:
            return None
        except (OSError, ValueError) as exc:
            warnings.append(f"{path.name}: {type(exc).__name__}")
            return None

    def directory(self, name: str) -> Path:
        if not JOB_NAME.fullmatch(name):
            raise ValueError("Unknown job name")
        path = (self.runs / name).resolve()
        if not path.is_relative_to(self.runs.resolve()):
            raise ValueError("Job directory escapes the run root")
        return path

    def hardware(self) -> dict[str, Any]:
        if time.monotonic() - self.gpu_sampled < 15:
            return self.gpu
        self.gpu_sampled = time.monotonic()
        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=3,
                creationflags=0x08000000 if os.name == "nt" else 0,
                check=True,
            )
            name, utilization, used, total, temperature = result.stdout.strip().splitlines()[0].split(", ")
            self.gpu = {
                "available": True,
                "name": name,
                "utilization": int(utilization),
                "memory_used": int(used),
                "memory_total": int(total),
                "temperature": int(temperature),
            }
        except (OSError, ValueError, IndexError, subprocess.SubprocessError):
            self.gpu = {"available": False}
        return self.gpu

    def processes(self) -> list[dict[str, Any]] | None:
        if os.name != "nt":
            return None
        command = (
            "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
            "ForEach-Object { [pscustomobject]@{pid=$_.ProcessId;parent=$_.ParentProcessId;"
            "command=$_.CommandLine} } | ConvertTo-Json -Compress"
        )
        try:
            result = subprocess.run(
                ["powershell.exe", "-NoProfile", "-Command", command],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=0x08000000,
                check=True,
            )
            records = json.loads(result.stdout) if result.stdout.strip() else []
            return records if isinstance(records, list) else [records]
        except (OSError, ValueError, subprocess.SubprocessError):
            return None

    def log_progress(self, name: str) -> tuple[dict[str, Any], str]:
        path = self.root / f"{name}.stdout.log"
        try:
            text = shared_read(path, 12_000, tail=True)
            matches = list(re.finditer(r"step=(\d+) updates=(\d+) sps=(\d+)", text))
            if matches:
                step, updates, rate = map(int, matches[-1].groups())
                return {"step": step, "updates": updates, "rate": rate, "updated_unix": path.stat().st_mtime}, text
            return {}, text
        except FileNotFoundError:
            return {}, ""

    def snapshot(self) -> dict[str, Any]:
        with self.lock:
            if time.monotonic() - self.sampled < 3:
                return self.last_snapshot
            warnings: list[str] = []
            plan = self.read_json(self.repo / "configs/experiments/preference_recovery_p2_v1.json", warnings) or {}
            # Never open rotating telemetry JSON. Even FILE_SHARE_DELETE did not
            # permit MoveFileEx replacement under an open reader in our witness.
            # Use OS enumeration, append-only logs, metadata and finalized files.
            processes = self.processes()
            if processes is None:
                warnings.append("OS process query unavailable; liveness is unknown")
            local = [p for p in (processes or []) if str(self.repo).lower() in (p.get("command") or "").lower()]
            coordinators = [
                p for p in local if re.search(r"run_preference_recovery(?:_io)?_cohort\.py", p.get("command") or "")
            ]
            coordinator_alive = bool(coordinators) if processes is not None else None
            now = time.time()
            jobs, source_commit = [], None
            budget = plan.get("training_interactions_per_job", 500000)
            for seed in plan.get("seeds", []):
                for arm in plan.get("factorial_arms", {}):
                    name = f"minecart-v0_{arm}_seed{seed}"
                    directory = self.directory(name)
                    candidates = [
                        p
                        for p in local
                        if re.search(r"run_preference_recovery(?:_io)?\.py", p.get("command") or "")
                        and re.search(rf"--arm\s+{arm}(?:\s|$)", p["command"])
                        and re.search(rf"--seed\s+{seed}(?:\s|$)", p["command"])
                    ]
                    # Prefer the actual base-interpreter child over the venv redirector.
                    ids = {p["pid"] for p in candidates}
                    process = next(
                        (p for p in candidates if p.get("parent") in ids), candidates[0] if candidates else None
                    )
                    alive = bool(process) if processes is not None else None
                    complete = self.read_json(directory / "complete.json", warnings)
                    completed = bool(complete and complete.get("training_interactions") == budget)
                    progress, stdout = self.log_progress(name)
                    try:
                        stderr = shared_read(self.root / f"{name}.stderr.log", 8000, tail=True)
                    except FileNotFoundError:
                        stderr = ""
                    declared = (
                        "technical_failure"
                        if "Traceback (most recent call last)" in stderr
                        else ("running" if stdout else "pending")
                    )
                    signal_age = max(0, now - progress["updated_unix"]) if progress else None
                    if completed:
                        state = "complete"
                    elif alive:
                        state = "running"
                    elif processes is None:
                        state = "unknown"
                    else:
                        state = worker_state(declared, False, False, signal_age)
                    snapshots = [
                        int(p.stem.removeprefix("resume_step"))
                        for p in directory.glob("resume_step*.pt")
                        if p.stem.removeprefix("resume_step").isdigit()
                    ]
                    # Evaluations and losses stop changing before complete.json is
                    # published. They are read ONLY after this completion marker.
                    evaluation = (self.read_json(directory / "evaluations.json", warnings) or []) if completed else []
                    task = []
                    if evaluation and evaluation[-1].get("step") == budget:
                        cases = evaluation[-1].get("task", {}).get("records", [])
                        for profile in range(2):
                            rows = [r for r in cases if r.get("preference_index") == profile]
                            if rows:
                                task.append(
                                    {
                                        "profile": profile,
                                        "successes": sum(bool(r.get("ore_delivered")) for r in rows),
                                        "episodes": len(rows),
                                        "utility": sum(r["utility"] for r in rows) / len(rows),
                                    }
                                )
                    manifest = self.read_json(directory / "manifest.json", warnings)
                    if manifest and source_commit is None:
                        source_commit = manifest.get("provenance", {}).get("git_commit")
                    jobs.append(
                        {
                            "name": name,
                            "arm": arm,
                            "seed": seed,
                            "state": state,
                            "declared_state": declared,
                            "step": budget if completed else progress.get("step"),
                            "budget": budget,
                            "updates": complete.get("gradient_updates") if completed else progress.get("updates"),
                            "pid": process["pid"] if process else None,
                            "alive": alive,
                            "heartbeat_age": signal_age,
                            "heartbeat_unix": progress.get("updated_unix"),
                            "resume_step": max(snapshots) if snapshots else None,
                            "resume_available": bool(snapshots),
                            "task": task,
                            "rate": progress.get("rate"),
                        }
                    )
            counts = {
                state: sum(j["state"] == state for j in jobs)
                for state in ("complete", "running", "stale", "starting", "failed", "interrupted", "pending", "unknown")
            }
            failures = counts["failed"] + counts["interrupted"]
            analysis = (
                self.read_json(self.root / "analysis.json", warnings)
                if jobs and counts["complete"] == len(jobs)
                else None
            )
            if processes is None:
                phase = "unknown"
            elif coordinator_alive:
                phase = "draining" if failures else "running"
            elif counts["running"]:
                phase = "orphaned"
            elif failures:
                phase = "blocked"
            elif jobs and counts["complete"] == len(jobs):
                phase = "complete_audited" if analysis else "training_complete"
            else:
                phase = "not_started" if plan else "unavailable"
            disks: dict[str, float | None] = {}
            for label, path in (("workspace", self.repo), ("system", Path("C:/"))):
                try:
                    disks[label] = round(shutil.disk_usage(path).free / 1024**3, 1)
                except OSError:
                    disks[label] = None
            snapshot = {
                "observed_unix": now,
                "study_id": plan.get("study_id", "preference-recovery-p2-v1"),
                "state": phase,
                "coordinator_alive": coordinator_alive,
                "jobs": jobs,
                "counts": counts,
                "total_steps": sum(j["step"] or 0 for j in jobs),
                "budget": plan.get("training_interactions_total", 6000000),
                "source_commit": source_commit,
                "segments": None,
                "gpu": self.hardware(),
                "disks_gib": disks,
                "warnings": warnings,
                "progress_source": "append-only stdout, 25k intervals; finalized counts are exact",
                "analysis": {"audit": analysis.get("audit"), "passing_arms": analysis.get("passing_arms", [])}
                if analysis
                else None,
            }
            self.last_snapshot, self.sampled = snapshot, time.monotonic()
            return snapshot

    def detail(self, name: str, stream: str) -> dict[str, Any]:
        directory = self.directory(name)
        if name not in {j["name"] for j in self.snapshot()["jobs"]}:
            raise ValueError("Unknown job")
        if stream not in ("stderr", "stdout"):
            raise ValueError("Unknown stream")
        log = self.root / f"{name}.{stream}.log"
        try:
            text = shared_read(log, 24_000, tail=True)
            modified = log.stat().st_mtime
        except FileNotFoundError:
            text, modified = "No log has been written for this job.", None
        warnings: list[str] = []
        finalized = next(j["state"] == "complete" for j in self.snapshot()["jobs"] if j["name"] == name)
        losses = (self.read_json(directory / "losses.json", warnings) or []) if finalized else []
        return {
            "name": name,
            "stream": stream,
            "log": "\n".join(text.splitlines()[-65:]),
            "modified_unix": modified,
            "losses": losses[-200:],
            "warnings": warnings,
        }


def handler_for(monitor: Monitor) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            expected_hosts = {
                f"127.0.0.1:{cast(ThreadingHTTPServer, self.server).server_port}",
                f"localhost:{cast(ThreadingHTTPServer, self.server).server_port}",
            }
            if self.headers.get("Host") not in expected_hosts:
                self.respond(403, b"Local access only", "text/plain")
                return
            origin = self.headers.get("Origin")
            if origin and origin not in {f"http://{h}" for h in expected_hosts}:
                self.respond(403, b"Cross-origin access denied", "text/plain")
                return
            path = urlsplit(self.path)
            try:
                if path.path == "/api/state":
                    payload = monitor.snapshot()
                elif path.path == "/api/job":
                    args = parse_qs(path.query)
                    payload = monitor.detail(args.get("name", [""])[0], args.get("stream", ["stderr"])[0])
                elif path.path in ("/", "/app.js", "/style.css"):
                    filename = {"/": "index.html", "/app.js": "app.js", "/style.css": "style.css"}[path.path]
                    content_type = {"/": "text/html", "/app.js": "text/javascript", "/style.css": "text/css"}[path.path]
                    self.respond(200, (ASSETS / filename).read_bytes(), content_type)
                    return
                elif path.path == "/favicon.ico":
                    self.respond(204, b"", "image/x-icon")
                    return
                else:
                    self.respond(404, b"Not found", "text/plain")
                    return
                self.respond(200, json.dumps(payload, allow_nan=False).encode(), "application/json")
            except ValueError:
                self.respond(400, b"Invalid request", "text/plain")
            except OSError:
                self.respond(503, b"Telemetry temporarily unavailable", "text/plain")

        def do_POST(self) -> None:
            self.respond(405, b"Read-only monitor", "text/plain")
            self.close_connection = True

        def respond(self, status: int, payload: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type + "; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-MORL-Monitor", "read-only-v1")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; script-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'",
            )
            self.end_headers()
            try:
                self.wfile.write(payload)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def log_message(self, message: str, *args: Any) -> None:
            pass

    return Handler


def main() -> None:
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--port", type=int, default=8770)
    args = parser.parse_args()
    log_directory = REPO / "artifacts/training-monitor"
    log_directory.mkdir(parents=True, exist_ok=True)
    sys.stdout = (log_directory / "server.log").open("a", encoding="utf-8", buffering=1)
    sys.stderr = sys.stdout
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler_for(Monitor()))
    print(f"MORL Training Console: http://127.0.0.1:{args.port} (read-only)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

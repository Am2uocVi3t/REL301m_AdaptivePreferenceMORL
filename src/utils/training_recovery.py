"""Atomic local checkpoints and process leases for bounded training jobs."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import random
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from importlib import import_module
from pathlib import Path
from typing import Any

import numpy as np
import torch


def atomic_json(path: Path, payload: Any) -> None:
    def convert(value: Any) -> Any:
        if isinstance(value, np.ndarray):
            return value.tolist()
        if isinstance(value, np.generic):
            return value.item()
        raise TypeError(type(value).__name__)

    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(payload, indent=2, default=convert, allow_nan=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


@contextmanager
def process_lease(path: Path) -> Iterator[None]:
    """The OS releases the byte lock even if the owning process is killed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as stream:
        if path.stat().st_size == 0:
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        try:
            if os.name == "nt":
                windows_lock: Any = import_module("msvcrt")
                windows_lock.locking(stream.fileno(), windows_lock.LK_NBLCK, 1)
            else:
                posix_lock: Any = import_module("fcntl")
                posix_lock.flock(stream.fileno(), posix_lock.LOCK_EX | posix_lock.LOCK_NB)
        except OSError as error:
            raise RuntimeError(f"An active process owns {path}") from error
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == "nt":
                windows_lock.locking(stream.fileno(), windows_lock.LK_UNLCK, 1)
            else:
                posix_lock.flock(stream.fileno(), posix_lock.LOCK_UN)


def reset_snapshot(env: Any) -> dict[str, Any]:
    return {
        "numpy": np.random.get_state(),
        "python": random.getstate(),
        "environment": copy.deepcopy(env.unwrapped.np_random.bit_generator.state),
    }


def reconstruct_reset(env: Any, snapshot: dict[str, Any], expected: np.ndarray) -> None:
    np.random.set_state(snapshot["numpy"])
    random.setstate(snapshot["python"])
    env.unwrapped.np_random.bit_generator.state = snapshot["environment"]
    observation, _ = env.reset()
    np.testing.assert_array_equal(observation, expected)


def global_rng_state() -> dict[str, Any]:
    return {
        "numpy": np.random.get_state(),
        "python": random.getstate(),
        "torch": torch.get_rng_state(),
        "cuda": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else [],
    }


def restore_global_rng(state: dict[str, Any]) -> None:
    np.random.set_state(state["numpy"])
    random.setstate(state["python"])
    torch.set_rng_state(state["torch"].cpu())
    if state["cuda"]:
        torch.cuda.set_rng_state_all([item.cpu() for item in state["cuda"]])


def save_boundary(directory: Path, step: int, state: dict[str, Any]) -> None:
    path = directory / f"resume_step{step:09}.pt"
    temporary = path.with_suffix(".tmp")
    with temporary.open("wb") as stream:
        torch.save(state, stream)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    atomic_json(directory / "resume_latest.json", {"file": path.name, "sha256": digest, "step": step})
    # Retain two generations so a killed write cannot invalidate the previous one.
    for older in sorted(directory.glob("resume_step*.pt"))[:-2]:
        older.unlink()


def load_boundary(directory: Path) -> dict[str, Any]:
    pointer = json.loads((directory / "resume_latest.json").read_text())
    name = pointer["file"]
    if Path(name).name != name or not name.startswith("resume_step") or not name.endswith(".pt"):
        raise ValueError("Invalid checkpoint filename")
    path = directory / name
    if hashlib.sha256(path.read_bytes()).hexdigest() != pointer["sha256"]:
        raise ValueError("Checkpoint checksum mismatch")
    # Only load trusted, locally generated training state after checking its receipt.
    return torch.load(path, map_location="cpu", weights_only=False)  # nosec B614: trusted local state


def process_birth(pid: int) -> str | None:
    """Creation identity prevents a stale PID from identifying an unrelated process."""
    if sys.platform != "win32":
        try:
            return Path(f"/proc/{pid}/stat").read_text().rsplit(") ", 1)[1].split()[19]
        except FileNotFoundError:
            return None
    import ctypes
    from ctypes import wintypes

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
    kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    handle = kernel.OpenProcess(0x1000, False, pid)
    if not handle:
        if ctypes.get_last_error() in (87, 1168):
            return None
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        exit_code = wintypes.DWORD()
        if not kernel.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
            raise ctypes.WinError(ctypes.get_last_error())
        if exit_code.value != 259:
            return None
        times = [wintypes.FILETIME() for _ in range(4)]
        if not kernel.GetProcessTimes(handle, *[ctypes.byref(value) for value in times]):
            raise ctypes.WinError(ctypes.get_last_error())
        return str((times[0].dwHighDateTime << 32) | times[0].dwLowDateTime)
    finally:
        kernel.CloseHandle(handle)

"""Exact old/new CUDA and lock-contention witnesses for the P2 I/O amendment."""

from __future__ import annotations

import ctypes
import subprocess
import sys
import threading
import time
from ctypes import wintypes
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.diagnose_policy_extraction import read, sha
from scripts.preference_recovery_io import AMENDMENT, QUALIFICATION, atomic_json_retry
from scripts.qualify_credit_recovery import compare
from src.utils.training_recovery import atomic_json

ROOT = Path("artifacts/preference-recovery-p2-io-qualification-v1")


def source_files() -> dict[str, str]:
    result = dict(read(Path("research/qualification/preference_recovery_p2_v1.json"))["source_sha256"])
    for filename, expected in result.items():
        assert sha(Path(filename)) == expected
    for path in (
        AMENDMENT,
        Path(__file__),
        Path("scripts/preference_recovery_io.py"),
        Path("scripts/run_preference_recovery_io.py"),
        Path("scripts/run_preference_recovery_io_cohort.py"),
        Path("scripts/analyze_preference_recovery_io.py"),
    ):
        result[path.as_posix()] = sha(path)
    return result


def lock_witness() -> dict[str, Any]:
    if sys.platform != "win32":
        raise RuntimeError("The real lock witness requires Windows")
    path = (ROOT / "lock.json").resolve()
    atomic_json(path, {"old": True})
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
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]

    def acquire() -> Any:
        handle = kernel.CreateFileW(str(path), 0x80000000, 7, None, 3, 0, None)
        if handle == ctypes.c_void_p(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
        return handle

    handle = acquire()
    original_failed = False
    try:
        try:
            atomic_json(path, {"unexpected": True})
        except PermissionError as exc:
            original_failed = getattr(exc, "winerror", None) == 5
    finally:
        kernel.CloseHandle(handle)
    assert original_failed
    handle = acquire()

    def release_handle() -> None:
        time.sleep(0.15)
        kernel.CloseHandle(handle)

    release = threading.Thread(target=release_handle)
    release.start()
    atomic_json_retry(path, {"new": True})
    release.join()
    assert read(path) == {"new": True}
    handle = acquire()
    started, failed = time.monotonic(), False
    try:
        try:
            atomic_json_retry(path, {"must_not_replace": True})
        except PermissionError:
            failed = True
    finally:
        kernel.CloseHandle(handle)
    assert failed and read(path) == {"new": True}
    assert time.monotonic() - started < 5
    return {
        "original_error_reproduced": True,
        "transient_lock": "passed",
        "persistent_lock": "bounded failure, original target retained",
    }


def command(arm: str, root: Path, adapted: bool) -> list[str]:
    script = "scripts/run_preference_recovery_io.py" if adapted else "scripts/run_preference_recovery.py"
    return [
        sys.executable,
        script,
        "--protocol",
        "configs/protocols/course_minecart_v0.json",
        "--arm",
        arm,
        "--seed",
        "20263081",
        "--smoke",
        "--smoke-steps",
        "12000",
        "--qualification-root",
        str(root),
    ]


def checked(args: list[str], path: Path) -> None:
    with path.open("w", encoding="utf-8") as log:
        subprocess.run(args, stdout=log, stderr=subprocess.STDOUT, timeout=300, check=True)


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=False)
    sources = source_files()
    locks = lock_witness()
    records = []
    for arm in "ABCD":
        case = ROOT / arm
        case.mkdir()
        old, new = case / "old", case / "adapted"
        suffix = Path("smoke") / f"minecart-v0_{arm}_seed20263081"
        checked(command(arm, old, False), case / "old.log")
        checked(command(arm, new, True), case / "adapted.log")
        compare(old / suffix, new / suffix, 12000)
        records.append({"arm": arm, "old_new_numerical_equality": "exact", "engineering_interactions": 24000})
        print(records[-1], flush=True)
    case = ROOT / "D"
    resumed = case / "resumed"
    suffix = Path("smoke/minecart-v0_D_seed20263081")
    with (case / "held.log").open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            [*command("D", resumed, True), "--pause-after", "6500", "--hold-at-boundary"],
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        try:
            marker = resumed / suffix / "paused.json"
            deadline = time.monotonic() + 300
            while not marker.exists():
                if process.poll() is not None or time.monotonic() > deadline:
                    raise RuntimeError("I/O-adapted worker failed before held boundary")
                time.sleep(0.2)
            with (case / "duplicate.log").open("w", encoding="utf-8") as duplicate_log:
                duplicate = subprocess.run(
                    [*command("D", resumed, True), "--resume"],
                    stdout=duplicate_log,
                    stderr=subprocess.STDOUT,
                    timeout=30,
                )
            assert duplicate.returncode != 0 and "An active process owns" in (case / "duplicate.log").read_text()
            subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], check=True, capture_output=True)
            process.wait(timeout=30)
        finally:
            if process.poll() is None:
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], check=True, capture_output=True)
                process.wait(timeout=30)
    checked([*command("D", resumed, True), "--resume"], case / "resumed.log")
    compare(case / "adapted" / suffix, resumed / suffix, 12000)
    assert source_files() == sources
    atomic_json_retry(
        QUALIFICATION,
        {
            "amendment_id": "preference-recovery-p2-io-v1",
            "status": "pass",
            "source_sha256": sources,
            "locks": locks,
            "records": records,
            "D_forced_kill_resume": "exact",
            "duplicate_rejected": True,
            "engineering_training_interactions": 108000,
            "final_test_steps": 0,
            "review_independence": "executor_only",
            "scope": "Mechanical I/O equivalence; no task-success evidence.",
        },
    )
    print("I/O amendment qualification PASS", flush=True)


if __name__ == "__main__":
    if not __debug__:
        raise RuntimeError("Qualification assertions must be enabled")
    main()

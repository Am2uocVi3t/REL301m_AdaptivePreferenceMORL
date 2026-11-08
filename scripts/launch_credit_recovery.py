"""Windows breakaway bootstrap; never fall back to a session-bound process."""

from __future__ import annotations

import argparse
import ctypes
import json
import os
import subprocess
import sys
import time
from ctypes import wintypes
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.utils.training_recovery import atomic_json, process_birth


class BasicLimits(ctypes.Structure):
    _fields_ = [
        ("process_time", ctypes.c_longlong),
        ("job_time", ctypes.c_longlong),
        ("flags", wintypes.DWORD),
        ("minimum", ctypes.c_size_t),
        ("maximum", ctypes.c_size_t),
        ("active", wintypes.DWORD),
        ("affinity", ctypes.c_size_t),
        ("priority", wintypes.DWORD),
        ("scheduling", wintypes.DWORD),
    ]


class ExtendedLimits(ctypes.Structure):
    _fields_ = [
        ("basic", BasicLimits),
        ("io", ctypes.c_ulonglong * 6),
        ("process_memory", ctypes.c_size_t),
        ("job_memory", ctypes.c_size_t),
        ("peak_process_memory", ctypes.c_size_t),
        ("peak_job_memory", ctypes.c_size_t),
    ]


def kernel_api() -> Any:
    if sys.platform != "win32":
        raise RuntimeError("This launcher is qualified only on Windows")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    kernel.CreateJobObjectW.restype = wintypes.HANDLE
    kernel.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    kernel.IsProcessInJob.argtypes = [wintypes.HANDLE, wintypes.HANDLE, ctypes.POINTER(wintypes.BOOL)]
    kernel.QueryInformationJobObject.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.c_void_p,
    ]
    return kernel


def job_information() -> dict[str, Any]:
    kernel = kernel_api()
    member = wintypes.BOOL()
    if not kernel.IsProcessInJob(kernel.GetCurrentProcess(), None, ctypes.byref(member)):
        raise OSError("Could not inspect Windows job membership")
    limits = ExtendedLimits()
    if member.value and not kernel.QueryInformationJobObject(
        None, 9, ctypes.byref(limits), ctypes.sizeof(limits), None
    ):
        raise OSError("Could not inspect Windows job limits")
    return {
        "member": bool(member.value),
        "flags": limits.basic.flags,
        "kill_on_job_close": bool(limits.basic.flags & 0x2000),
    }


def create_test_kill_job() -> Any:
    kernel = kernel_api()
    handle = kernel.CreateJobObjectW(None, None)
    limits = ExtendedLimits()
    limits.basic.flags = 0x2000 | 0x0800
    if not handle or not kernel.SetInformationJobObject(handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
        raise OSError("Could not create qualification kill-on-close job")
    if not kernel.AssignProcessToJobObject(handle, kernel.GetCurrentProcess()):
        raise OSError("Could not assign qualification parent to test job")
    return handle


def main() -> None:
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--test-parent", action="store_true")
    args = parser.parse_args()
    request = json.loads(args.request.read_text())
    directory = Path(request["directory"]).resolve()
    workspace = Path(__file__).resolve().parents[1]
    if directory.drive.upper() != "D:" or not directory.is_relative_to(workspace / "artifacts"):
        raise ValueError("Launch directory must remain under D-drive workspace artifacts")
    if request["mode"] not in ("qualification", "main"):
        raise ValueError("Unknown launch mode")
    role = "worker" if args.worker else "bootstrap"
    sys.stdout = (directory / f"{role}.stdout.log").open("a", encoding="utf-8")
    sys.stderr = (directory / f"{role}.stderr.log").open("a", encoding="utf-8")
    if args.worker:
        constraints = job_information()
        if constraints["kill_on_job_close"]:
            raise RuntimeError("Worker still belongs to a kill-on-close Windows job")
        import torch

        generator = torch.Generator(device="cuda").manual_seed(20261512)
        tensor = torch.randn(8, 32, device="cuda", generator=generator, requires_grad=True)
        loss = tensor.square().mean()
        loss.backward()
        if tensor.grad is None or not torch.isfinite(tensor.grad).all():
            raise RuntimeError("Independent-process CUDA witness failed")
        atomic_json(
            directory / "worker_identity.json",
            {
                "pid": os.getpid(),
                "birth": process_birth(os.getpid()),
                "token": request["token"],
                "job": constraints,
                "runtime": {
                    "prefix": sys.prefix,
                    "torch": torch.__version__,
                    "cuda_kernel_loss": float(loss.item()),
                    "device": torch.cuda.get_device_name(),
                },
            },
        )
        if request["mode"] == "main":
            from scripts.run_credit_recovery_cohort import main as cohort_main

            cohort_main(resume_existing=bool(request.get("resume_existing", False)))
        else:
            for tick in range(180):
                atomic_json(
                    directory / "witness_heartbeat.json",
                    {
                        "pid": os.getpid(),
                        "birth": process_birth(os.getpid()),
                        "tick": tick,
                        "updated_unix": time.time(),
                        "token": request["token"],
                    },
                )
                time.sleep(1)
            atomic_json(directory / "witness_complete.json", {"status": "complete", "ticks": 180})
        return
    if args.test_parent:
        if request["mode"] != "qualification":
            raise ValueError("Kill-on-close injection is forbidden for main training")
        test_handle = create_test_kill_job()
        atomic_json(
            directory / "test_parent.json",
            {
                "pid": os.getpid(),
                "birth": process_birth(os.getpid()),
                "job": job_information(),
                "handle": int(test_handle),
            },
        )
    with (
        (directory / "worker.stdout.log").open("a", encoding="utf-8") as stdout,
        (directory / "worker.stderr.log").open("a", encoding="utf-8") as stderr,
    ):
        # The Windows venv redirector creates its own kill-on-close job. Invoke
        # the same base interpreter with the venv marker instead, preserving the
        # qualified site-packages without introducing another redirector parent.
        base_interpreter = getattr(sys, "_base_executable", None)
        if not isinstance(base_interpreter, str):
            raise RuntimeError("Qualified base interpreter is unavailable")
        process = subprocess.Popen(
            [base_interpreter, __file__, "--request", str(args.request), "--worker"],
            cwd=workspace,
            stdout=stdout,
            stderr=stderr,
            close_fds=True,
            env=dict(os.environ, __PYVENV_LAUNCHER__=sys.executable),
            creationflags=0x01000000 | 0x00000008 | 0x00000200,
        )
    atomic_json(
        directory / "launch_receipt.json",
        {
            "bootstrap_pid": os.getpid(),
            "child_pid": process.pid,
            "created_unix": time.time(),
            "flags": "BREAKAWAY_FROM_JOB | DETACHED_PROCESS | NEW_PROCESS_GROUP",
            "token": request["token"],
        },
    )
    if args.test_parent:
        # Exit without closing the test job explicitly: Windows closes the handle
        # and kills its remaining members. The breakaway witness must survive.
        os._exit(0)


if __name__ == "__main__":
    main()

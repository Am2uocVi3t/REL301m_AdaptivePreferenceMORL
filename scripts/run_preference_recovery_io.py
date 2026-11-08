"""Run the frozen P2 learner with an explicitly recorded atomic-JSON adapter."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import preference_recovery_io as adapter
from scripts import run_preference_recovery as legacy
from src.utils import training_recovery
from src.utils.provenance import collect_provenance


def main() -> None:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--arm", required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--qualification-root", type=Path)
    args, _ = parser.parse_known_args()
    name = f"minecart-v0_{args.arm}_seed{args.seed}"
    if not args.smoke:
        adapter.verify_qualification()
        amendment = json.loads(adapter.AMENDMENT.read_text())
        if name not in amendment["remaining_jobs"]:
            raise ValueError("The I/O adapter cannot run completed or out-of-scope jobs")
    root = args.qualification_root or legacy.ROOT
    receipt_path = root / "io_segments" / name / f"segment_{os.getpid()}_{time.time_ns()}.json"
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt = {
        "job": name,
        "pid": os.getpid(),
        "started_unix": time.time(),
        "status": "running",
        "qualification_only": args.smoke,
        "adapter_sha256": hashlib.sha256(Path(adapter.__file__).read_bytes()).hexdigest(),
        "wrapper_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "amendment_sha256": hashlib.sha256(adapter.AMENDMENT.read_bytes()).hexdigest(),
        "provenance": collect_provenance({"atomic_json_adapter": "p2-io-v1", "job": name}),
        "semantics": "Only JSON replacement retries; original learner, source binding, RNG and budget unchanged.",
    }
    adapter.atomic_json_retry(receipt_path, receipt)
    # Both direct heartbeat/progress writes and recovery-pointer publication use
    # the same bounded adapter. The historical modules on disk stay untouched.
    legacy.atomic_json = adapter.atomic_json_retry
    training_recovery.atomic_json = adapter.atomic_json_retry
    try:
        legacy.main()
        receipt["status"] = "returned"
    finally:
        if receipt["status"] == "running":
            receipt["status"] = "failed"
        receipt["ended_unix"] = time.time()
        receipt["json_retries"] = adapter.RETRIES
        adapter.atomic_json_retry(receipt_path, receipt)


if __name__ == "__main__":
    main()

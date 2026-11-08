#!/usr/bin/env python3
"""Inspect ARIS installation, quota, and recorded action policy without dispatching work."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.research_harness.aris import preflight
from src.research_harness.store import write_registry


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--action", default="offline-tests")
    parser.add_argument("--remaining-percent", type=float, help="Fresh minimum remaining across quota windows")
    parser.add_argument("--write-snapshot", action="store_true")
    parser.add_argument("--quota-observed-at", help="ISO timestamp with timezone; maximum age 300 seconds")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    try:
        report = preflight(root, args.action, args.remaining_percent, args.quota_observed_at)
    except (OSError, ValueError, KeyError) as exc:
        print(json.dumps({"status": "ERROR", "dispatch_performed": False, "error": str(exc)}))
        return 2
    if args.write_snapshot:
        write_registry(root / ".aris" / "preflight.json", report)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())

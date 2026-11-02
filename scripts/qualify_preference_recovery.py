"""P2 four-cell CUDA and fresh-process kill/resume qualification."""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.diagnose_policy_extraction import read, sha
from scripts.qualify_credit_recovery import compare
from src.utils.training_recovery import atomic_json

ROOT = Path("artifacts/preference-recovery-p2-qualification-v1")
PLAN = Path("configs/experiments/preference_recovery_p2_v1.json")


def source_files() -> dict[str, str]:
    paths = [
        *Path("src").rglob("*.py"),
        PLAN,
        Path("scripts/run_preference_recovery.py"),
        Path("scripts/preference_recovery_core.py"),
        Path("scripts/run_preference_recovery_cohort.py"),
        Path("scripts/analyze_preference_recovery.py"),
        Path("scripts/diagnose_policy_extraction.py"),
        Path("scripts/start_preference_recovery.ps1"),
        Path(__file__),
    ]
    return {p.as_posix(): sha(p) for p in paths}


def command(arm: str, root: Path) -> list[str]:
    return [
        sys.executable,
        "scripts/run_preference_recovery.py",
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


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=False)
    snapshots = source_files()
    records = []
    for arm in ("A", "B", "C", "D"):
        case = ROOT / arm
        case.mkdir()
        suffix = Path("smoke") / f"minecart-v0_{arm}_seed20263081"
        continuous, resumed = case / "continuous", case / "resumed"
        with (case / "continuous.log").open("w", encoding="utf-8") as stream:
            subprocess.run(command(arm, continuous), stdout=stream, stderr=subprocess.STDOUT, check=True, timeout=300)
        with (case / "interrupted.log").open("w", encoding="utf-8") as stream:
            process = subprocess.Popen(
                [*command(arm, resumed), "--pause-after", "6500", "--hold-at-boundary"],
                stdout=stream,
                stderr=subprocess.STDOUT,
            )
            try:
                deadline = time.monotonic() + 300
                marker = resumed / suffix / "paused.json"
                while not marker.exists():
                    if process.poll() is not None or time.monotonic() > deadline:
                        raise RuntimeError("P2 qualification did not reach saved episode boundary")
                    time.sleep(0.2)
                with (case / "duplicate.log").open("w", encoding="utf-8") as duplicate_log:
                    duplicate = subprocess.run(
                        [*command(arm, resumed), "--resume"], stdout=duplicate_log, stderr=subprocess.STDOUT, timeout=30
                    )
                assert duplicate.returncode != 0 and "An active process owns" in (case / "duplicate.log").read_text()
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True, check=True)
                process.wait(timeout=30)
            finally:
                if process.poll() is None:
                    subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True, check=True)
                    process.wait(timeout=30)
        with (case / "resumed.log").open("w", encoding="utf-8") as stream:
            subprocess.run(
                [*command(arm, resumed), "--resume"], stdout=stream, stderr=subprocess.STDOUT, timeout=300, check=True
            )
        compare(continuous / suffix, resumed / suffix, 12000)
        final = read(continuous / suffix / "complete.json")
        assert final["training_interactions"] == 12000 and final["gradient_updates"] == 1751
        records.append(
            {
                "arm": arm,
                "initial_hash": final["initial_parameter_sha256"],
                "final_hash": final["final_parameter_sha256"],
                "kill_resume": "exact model/target/optimizer/episodes/losses/returns",
                "duplicate_rejected": True,
                "boundary_step": read(marker)["step"],
                "engineering_interactions": 24000,
                "validation_steps": 2 * final["validation_evaluation_steps"],
            }
        )
        print(records[-1], flush=True)
    assert len({r["initial_hash"] for r in records}) == 1
    assert len({r["final_hash"] for r in records}) == 4
    assert snapshots == source_files()
    atomic_json(
        Path("research/qualification/preference_recovery_p2_v1.json"),
        {
            "study_id": "preference-recovery-p2-v1",
            "status": "pass",
            "device": "cuda",
            "plan_sha256": sha(PLAN),
            "source_sha256": snapshots,
            "records": records,
            "engineering_training_interactions": 96000,
            "engineering_validation_steps": sum(r["validation_steps"] for r in records),
            "review_independence": "executor_only",
            "final_test_steps": 0,
            "qualification_only": True,
            "scope": (
                "Four cells: finite gradients, paired initialization and exact RNG/loss/relabel restoration. "
                "Old Windows launcher/tail qualification retained; no old-trajectory equivalence claimed."
            ),
        },
    )


if __name__ == "__main__":
    if not __debug__:
        raise RuntimeError("Qualification assertions must be enabled")
    main()

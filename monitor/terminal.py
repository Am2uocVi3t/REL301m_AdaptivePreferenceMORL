"""Native terminal monitor. Direct passive telemetry; no browser or HTTP required."""

from __future__ import annotations

import argparse
import ctypes
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from rich import box
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from monitor.server import Monitor

COLORS = {
    "running": "#70e4c4",
    "complete": "#70e4c4",
    "failed": "#ff8a94",
    "interrupted": "#ff8a94",
    "pending": "#ffd08b",
    "blocked": "#ff8a94",
}
MUTED = "#a7b8cc"


def safe_text(value: str) -> str:
    value = re.sub(r"\x1b\][^\x07]*(?:\x07|\x1b\\)", "", value)
    value = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", value)
    return "".join(c for c in value if c == "\n" or c.isprintable())


class Selection:
    def __init__(self) -> None:
        self.index = 0
        self.stream = "stderr"
        self.paused = False

    def key(self, key: str, count: int) -> str | None:
        if key in ("q", "\x03"):
            return "quit"
        if key in ("j", "down"):
            self.index = (self.index + 1) % max(count, 1)
        elif key in ("k", "up"):
            self.index = (self.index - 1) % max(count, 1)
        elif key == "\t":
            self.stream = "stdout" if self.stream == "stderr" else "stderr"
        elif key == " ":
            self.paused = not self.paused
        return "refresh" if key == "r" else None


def render(
    state: dict[str, Any], detail: dict[str, Any] | None, selection: Selection, width: int, height: int
) -> Group:
    jobs, counts = state["jobs"], state["counts"]
    total, budget = state["total_steps"], state["budget"]
    percentage = min(100, 100 * total / budget)
    color = COLORS.get(state["state"], MUTED)
    header = Text(" MORL // TRAINING MONITOR", style="bold #70e4c4")
    header.append("   REL301m / " + state.get("study_label", "P2 Minecart"), style=MUTED)
    header.append(
        "   " + datetime.fromtimestamp(state["observed_unix"], timezone(timedelta(hours=7))).strftime("%H:%M:%S ICT"),
        style=MUTED,
    )
    if selection.paused:
        header.append("   VIEW PAUSED", style="bold yellow")
    bar_width = max(12, min(55, width - 40))
    filled = round(bar_width * percentage / 100)
    progress = Text(f" {percentage:5.1f}% ", style="bold white")
    progress.append("━" * filled, style="#70e4c4")
    progress.append("━" * (bar_width - filled), style="#293a4e")
    progress.append(f"  {total:,} / {budget:,}", style=MUTED)
    summary = Text(
        f" {counts['complete']}/{len(jobs)} COMPLETE  ·  {counts['running']} ACTIVE  ·  "
        f"{counts['failed'] + counts['interrupted']} FAILED  ·  {counts['pending']} PENDING",
        style=MUTED,
    )
    summary.append("   " + state["state"].upper(), style=f"bold {color}")
    gpu = state["gpu"]
    hardware = (
        f" GPU {gpu['utilization']}%  VRAM {gpu['memory_used']}/{gpu['memory_total']} MiB  {gpu['temperature']}°C"
        if gpu["available"]
        else " GPU telemetry unavailable"
    )
    hardware += f"  |  D: {state['disks_gib'].get('workspace', '—')} GiB free"
    note = " Live counts: stdout every 25k steps. Completion is separate from task success."
    if state.get("entropy"):
        note += f" Entropy {state['entropy'][0]} / target {state['entropy'][1]}."
    alert = (
        " Dispatch stopped: recovery required. No training workers are running."
        if state["state"] == "blocked"
        else " Dispatch halted; existing workers are finishing."
        if state["state"] == "draining"
        else " Monitor observes only. Closing it does not stop training."
    )
    top = Panel(
        Group(
            header, progress, summary, Text(hardware, style=MUTED), Text(note, style="dim"), Text(alert, style=color)
        ),
        border_style="#293a4e",
        padding=(0, 1),
    )
    table = Table(box=box.SIMPLE_HEAD, expand=True, border_style="#293a4e", padding=(0, 1))
    table.add_column("", width=1)
    table.add_column("ARM", width=3)
    table.add_column("SEED", width=8)
    table.add_column("STATE", width=11)
    table.add_column(f"STEPS / {jobs[0].get('budget', 500000):,}" if jobs else "STEPS", justify="right")
    if width >= 105:
        table.add_column("UPDATES", justify="right")
        table.add_column(state.get("task_label", "DELIVERIES"), justify="right")
    table.add_column("SNAPSHOT", justify="right")
    # Keep selection visible even in a short terminal window.
    visible = max(3, min(12, height - 22))
    start = max(0, min(selection.index - visible + 1, len(jobs) - visible))
    for index in range(start, min(start + visible, len(jobs))):
        job = jobs[index]
        selected = index == selection.index
        values: list[Any] = [
            Text(">" if selected else "", style="#70e4c4"),
            job["arm"],
            str(job["seed"]),
            Text(job["state"].upper(), style=COLORS.get(job["state"], MUTED)),
            f"{job['step']:,}" if job["step"] is not None else "—",
        ]
        if width >= 105:
            values.extend(
                [
                    f"{job['updates']:,}" if job["updates"] is not None else "—",
                    " · ".join(
                        f"{t.get('mode', '')}/p{t['profile']} {t['successes']}/{t['episodes']}".strip()
                        for t in job["task"]
                    )
                    or "—",
                ]
            )
        values.append(f"{job['resume_step']:,}" if job["resume_step"] is not None else "—")
        table.add_row(*values, style="on #142c31" if selected else "")
    worker_panel = Panel(table, title="[bold]WORKER MATRIX[/bold]", border_style="#293a4e", padding=(0, 0))
    lines = max(2, min(8, height - visible - 18))
    text = safe_text((detail or {}).get("log", "No worker log available."))
    log = Text(
        "\n".join(text.splitlines()[-lines:]) or "No log output yet.", style=MUTED, overflow="ellipsis", no_wrap=True
    )
    label = f"ARM {jobs[selection.index]['arm']} / {jobs[selection.index]['seed']}" if jobs else "NO WORKER"
    log_panel = Panel(
        log,
        title=f"{label} · {selection.stream.upper()} · retained history",
        border_style="#293a4e",
        padding=(0, 1),
        height=lines + 2,
    )
    footer = Text(" ↑/↓ or J/K select   TAB log   SPACE pause view   R refresh   Q close monitor", style=MUTED)
    return Group(top, worker_panel, log_panel, footer)


def read_key() -> str | None:
    if sys.platform != "win32":
        return None
    import msvcrt

    if not msvcrt.kbhit():
        return None
    key = msvcrt.getwch()
    if key in ("\x00", "\xe0"):
        return {"H": "up", "P": "down"}.get(msvcrt.getwch())
    return key.lower()


def main() -> None:
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--once", action="store_true", help="Print one actual telemetry frame and exit")
    parser.add_argument("--export-svg", type=Path, help="Save the once-mode frame for verification")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stdout.isatty() and os.environ.get("TERM", "dumb") in ("dumb", "unknown"):
        os.environ["TERM"] = "xterm-256color"
    console = Console(
        record=bool(args.export_svg), no_color=False, color_system="truecolor" if sys.stdout.isatty() else None
    )
    monitor, selection = Monitor(), Selection()
    state = monitor.snapshot()
    selection.index = next((i for i, j in enumerate(state["jobs"]) if j["state"] == "failed"), 0)

    def frame() -> Group:
        size = console.size
        detail = monitor.detail(state["jobs"][selection.index]["name"], selection.stream) if state["jobs"] else None
        return render(state, detail, selection, size.width, size.height)

    if args.once or not console.is_terminal:
        console.print(frame())
        if args.export_svg:
            args.export_svg.parent.mkdir(parents=True, exist_ok=True)
            console.save_svg(str(args.export_svg), title="MORL Training Monitor — actual terminal frame")
        return
    if sys.platform == "win32":
        ctypes.windll.kernel32.SetConsoleTitleW("MORL Training Monitor | REL301m")
    refreshed = time.monotonic()
    try:
        with Live(
            frame(), console=console, screen=True, auto_refresh=False, redirect_stdout=False, redirect_stderr=False
        ) as live:
            while True:
                key = read_key()
                action = selection.key(key, len(state["jobs"])) if key else None
                if action == "quit":
                    break
                if action == "refresh" or (not selection.paused and time.monotonic() - refreshed >= 5):
                    state = monitor.snapshot()
                    refreshed = time.monotonic()
                if key or time.monotonic() - refreshed < 0.15:
                    live.update(frame(), refresh=True)
                time.sleep(0.08)
    except KeyboardInterrupt:
        pass
    console.print("Monitor closed. Training is unaffected.", style=MUTED)


if __name__ == "__main__":
    main()

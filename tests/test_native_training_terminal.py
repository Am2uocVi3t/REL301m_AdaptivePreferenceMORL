import io

from rich.console import Console

from monitor.terminal import Selection, render, safe_text


def test_native_key_controls_only_change_view_selection():
    state = Selection()
    state.key("up", 12)
    assert state.index == 11
    state.key("j", 12)
    assert state.index == 0
    state.key("\t", 12)
    assert state.stream == "stdout"
    state.key(" ", 12)
    assert state.paused
    assert state.key("r", 12) == "refresh"
    assert state.key("q", 12) == "quit"
    assert safe_text("\x1b[2Jsafe\x07\x1b]0;evil\x07") == "safe"


def test_native_render_reports_blocked_and_separates_job_completion_from_task_success():
    state = {
        "observed_unix": 1793613993,
        "state": "blocked",
        "total_steps": 300000,
        "budget": 6000000,
        "counts": {"complete": 0, "running": 0, "failed": 1, "interrupted": 0, "pending": 0},
        "gpu": {"available": False},
        "disks_gib": {"workspace": 180},
        "jobs": [
            {
                "arm": "D",
                "seed": 20263212,
                "state": "failed",
                "step": 300000,
                "updates": 73751,
                "resume_step": 297188,
                "task": [],
            }
        ],
    }
    output = io.StringIO()
    Console(file=output, width=120, color_system=None).print(
        render(state, {"log": "PermissionError: access denied"}, Selection(), 120, 40)
    )
    text = output.getvalue()
    assert "BLOCKED" in text and "0 ACTIVE" in text
    assert "PermissionError" in text and "297,188" in text
    assert "Completion is separate from task success" in text
    assert "Q close monitor" in text

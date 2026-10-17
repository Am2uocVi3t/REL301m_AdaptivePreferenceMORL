"""Exercise the pinned upstream MCP and resume CLI with synthetic provider output."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from tests.test_aris_review_guard import prepare, result

REPO = Path(__file__).resolve().parents[1]
UPSTREAM = Path(json.loads((REPO / "configs/aris/project.json").read_text())["upstream_root"])


def rpc(env: dict, messages: list[dict]) -> list[dict]:
    completed = subprocess.run(
        [sys.executable, str(UPSTREAM / "mcp-servers/claude-review/server.py")],
        input="".join(json.dumps(message) + "\n" for message in messages),
        capture_output=True,
        text=True,
        check=True,
        timeout=10,
        env=env,
    )
    return [json.loads(line) for line in completed.stdout.splitlines()]


def call(name: str, args: dict, request_id: int = 1) -> dict:
    return {"jsonrpc": "2.0", "id": request_id, "method": "tools/call", "params": {"name": name, "arguments": args}}


def test_real_mcp_disabled_bridge_preserves_legacy_ledger(tmp_path: Path) -> None:
    legacy = Path("/home/hei/.local/share/rel301m-aris-setup/reserved-calls.txt")
    before = legacy.read_bytes()
    env = {
        **os.environ,
        "CLAUDE_BIN": str(REPO / "scripts/aris_review_guard.py"),
        "CLAUDE_REVIEW_STATE_DIR": str(tmp_path / "state"),
        "CLAUDE_REVIEW_DEBUG_LOG": os.devnull,
    }
    # Use a tiny executable adapter so the tracked Python file needs no mode mutation.
    adapter = tmp_path / "guard"
    adapter.write_text(
        f"#!{sys.executable}\nimport runpy\n"
        f"runpy.run_path({str(REPO / 'scripts/aris_review_guard.py')!r}, run_name='__main__')\n"
    )
    adapter.chmod(0o700)
    env["CLAUDE_BIN"] = str(adapter)
    responses = rpc(
        env, [{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, call("review", {"prompt": "offline fixture"}, 2)]
    )
    assert len(responses[0]["result"]["tools"]) == 5
    assert responses[1]["result"]["isError"] is True
    assert "disabled" in responses[1]["result"]["content"][0]["text"]
    assert legacy.read_bytes() == before


def test_installed_launcher_remains_disabled() -> None:
    external = Path("/home/hei/.local/share/rel301m-aris-setup")
    legacy = (external / "reserved-calls.txt").read_bytes()
    response = subprocess.run(
        ["bash", str(external / "start-review-server.sh")],
        input=json.dumps(call("review", {"prompt": "offline disabled gate only"})) + "\n",
        capture_output=True,
        text=True,
        timeout=10,
        check=True,
    )
    result = json.loads(response.stdout)["result"]
    assert result["isError"] is True
    assert "disabled" in result["content"][0]["text"]
    assert (external / "reserved-calls.txt").read_bytes() == legacy


def test_async_mcp_status_survives_server_restart(tmp_path: Path) -> None:
    # This stand-in replaces Claude entirely; it cannot issue a provider request.
    fake = tmp_path / "fixture-provider"
    prepare(tmp_path)
    output = result()
    fake.write_text(f"#!{sys.executable}\nprint({json.dumps(output)!r})\n")
    fake.chmod(0o700)
    adapter = tmp_path / "offline-guard"
    adapter.write_text(
        f"#!{sys.executable}\nimport sys\nfrom pathlib import Path\n"
        f"sys.path.insert(0, {str(REPO)!r})\nfrom scripts import aris_review_guard as guard\n"
        f"guard.CLI=Path({str(fake)!r})\n"
        f"code, result = guard.execute(Path({str(tmp_path)!r}), sys.argv[1:])\n"
        "import json\nprint(json.dumps(result))\nsys.exit(code)\n"
    )
    adapter.chmod(0o700)
    env = {
        **os.environ,
        "CLAUDE_BIN": str(adapter),
        "CLAUDE_REVIEW_STATE_DIR": str(tmp_path / "state"),
        "CLAUDE_REVIEW_DEBUG_LOG": os.devnull,
    }
    response = rpc(env, [call("review_start", {"prompt": "synthetic fixture", "tools": ""})])[0]
    started = json.loads(response["result"]["content"][0]["text"])
    job_id = started["jobId"]
    # A fresh server process recovers the same job; no new review is dispatched.
    response = rpc(env, [call("review_status", {"jobId": job_id, "waitSeconds": 3})])[0]
    finished = json.loads(response["result"]["content"][0]["text"])
    assert finished["done"] is True
    assert finished["model"] == "claude-synthetic-test"
    assert len(list((tmp_path / "state/jobs").glob("*.json"))) == 1


def test_upstream_resume_never_accepts_unreviewed_done(tmp_path: Path) -> None:
    cli = UPSTREAM / "tools/run_state.py"

    def run(*args: str) -> str:
        return subprocess.run(
            [sys.executable, str(cli), *args], capture_output=True, text=True, timeout=5, check=True
        ).stdout.strip()

    root = str(tmp_path)
    run("start", root, "offline", "--phases", "mechanical,semantic", "--executor", "codex-gpt-6")
    run("set", root, "offline", "mechanical", "done", "--artifact", "synthetic-fixture")
    assert run("resume", root, "offline") == "mechanical"
    run(
        "accept",
        root,
        "offline",
        "mechanical",
        "--verdict-id",
        "synthetic-check-exit-0",
        "--reviewer",
        "deterministic:fixture-check",
    )
    run("set", root, "offline", "semantic", "done")
    assert run("resume", root, "offline") == "semantic"
    run(
        "mark-provisional",
        root,
        "offline",
        "semantic",
        "--verdict-id",
        "synthetic-provisional",
        "--reviewer",
        "codex-gpt-6",
    )
    assert run("resume", root, "offline") == "semantic"


@pytest.mark.parametrize("bad", ["reserved\ncorrupt\n", "\x00"])
def test_corrupt_legacy_never_manufactures_capacity(tmp_path: Path, bad: str) -> None:
    from scripts.aris_review_guard import import_legacy

    (tmp_path / "reserved-calls.txt").write_text(bad)
    with pytest.raises(ValueError):
        import_legacy(tmp_path)

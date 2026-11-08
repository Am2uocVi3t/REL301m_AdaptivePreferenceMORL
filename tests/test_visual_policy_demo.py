import json

import numpy as np
import pytest

from scripts import render_policy_demo as demo


def test_centre_preference_is_deterministic_and_first_tie():
    values = np.asarray([[0.9, 0.1], [0.6, 0.4], [0.4, 0.6]], dtype=np.float32)
    index, preference = demo.centre_preference(values)
    assert index == 1
    np.testing.assert_array_equal(preference, values[1])


def completed_fixture(tmp_path, monkeypatch):
    monkeypatch.setattr(demo, "ROOT", tmp_path)
    output = tmp_path / "output"
    output.mkdir()
    monkeypatch.setattr(demo, "OUT", output)
    spec = {"name": "Fixture", "protocol": "protocol.json", "run": "run", "steps": [1, 2]}
    paths = [
        "visual-policy-demo.md",
        "protocol.json",
        "configs/shifts/dynamics_shifts.yaml",
        "run/checkpoint_step1.pt",
        "run/checkpoint_step2.pt",
    ]
    for relative in paths:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture")
    monkeypatch.setattr(demo, "load_protocol", lambda *_: ({}, np.asarray([[0.5, 0.5]])))
    for name in ("Fixture.mp4", "Fixture.json"):
        (output / name).write_text("fixture")
    inputs = {
        "script": demo.digest(demo.Path(demo.__file__)),
        "plan": demo.digest(tmp_path / paths[0]),
        "protocol": demo.digest(tmp_path / paths[1]),
        "shifts": demo.digest(tmp_path / paths[2]),
        "checkpoints": {relative: demo.digest(tmp_path / relative) for relative in paths[3:]},
    }
    receipt = {
        "inputs": inputs,
        "outputs": {name: demo.digest(output / name) for name in ("Fixture.mp4", "Fixture.json")},
    }
    (output / "Fixture.complete.json").write_text(json.dumps(receipt))
    return spec, output, receipt


def test_completed_resume_skips_before_checkpoint_or_environment_load(tmp_path, monkeypatch):
    spec, _, receipt = completed_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(demo.torch, "load", lambda *_args, **_kwargs: pytest.fail("Duplicate checkpoint load"))
    assert demo.render(spec) == receipt


@pytest.mark.parametrize("changed", ["Fixture.mp4", "Fixture.json"])
def test_resume_rejects_changed_outputs(tmp_path, monkeypatch, changed):
    spec, output, _ = completed_fixture(tmp_path, monkeypatch)
    (output / changed).write_text("tampered")
    with pytest.raises(ValueError, match="refuse silent replay"):
        demo.render(spec)


def test_interruption_does_not_silently_replay(tmp_path, monkeypatch):
    spec, output, _ = completed_fixture(tmp_path, monkeypatch)
    (output / "Fixture.complete.json").unlink()
    (output / "Fixture.started.json").write_text("{}")
    with pytest.raises(ValueError, match="Interrupted"):
        demo.render(spec)

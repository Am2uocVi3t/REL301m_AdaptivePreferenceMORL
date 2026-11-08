import json
import os

import pytest
import torch

from src.utils.training_recovery import load_boundary, process_birth, process_lease, save_boundary


def test_boundary_commit_keeps_previous_generation_and_detects_corruption(tmp_path):
    for step in (1, 2, 3):
        save_boundary(tmp_path, step, {"step": step, "tensor": torch.tensor([step])})
    assert len(list(tmp_path.glob("resume_step*.pt"))) == 2
    assert load_boundary(tmp_path)["step"] == 3
    pointer = json.loads((tmp_path / "resume_latest.json").read_text())
    (tmp_path / pointer["file"]).write_bytes(b"interrupted or corrupted data")
    with pytest.raises(ValueError, match="checksum"):
        load_boundary(tmp_path)


def test_process_lease_excludes_duplicates_and_releases_on_exit(tmp_path):
    path = tmp_path / "worker.lock"
    with process_lease(path):
        with pytest.raises(RuntimeError, match="active process"):
            with process_lease(path):
                pytest.fail("Duplicate lease acquired")
    with process_lease(path):
        assert process_birth(os.getpid()) is not None

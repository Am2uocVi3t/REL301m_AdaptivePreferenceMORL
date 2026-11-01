from __future__ import annotations

import copy

import pytest

from scripts import evaluate
from src.evaluation.protocol import load_protocol, protocol_hash
from src.utils.resources import peak_rss_kib


def test_peak_resident_memory_is_available_on_the_running_platform():
    assert peak_rss_kib() > 0


def test_evaluator_defaults_to_validation():
    args = evaluate.parse_args(["--model-path", "unused.pt", "--protocol", "unused.json"])
    assert args.split == "validation"


def test_final_test_rejected_before_loading_protocol_or_checkpoint(monkeypatch):
    args = evaluate.parse_args(["--model-path", "missing.pt", "--protocol", "missing.json", "--split", "test"])
    monkeypatch.setattr(evaluate, "parse_args", lambda: args)
    with pytest.raises(ValueError, match="Final-test evaluation remains locked"):
        evaluate.main()


def test_checkpoint_rejects_different_reward_scale_with_same_dimensions_and_gamma():
    protocol, _ = load_protocol("configs/protocols/course_minecart_v0.json")
    checkpoint = {
        "protocol": copy.deepcopy(protocol),
        "protocol_sha256": protocol_hash(protocol),
        "args": {"env": protocol["env_id"], "gamma": protocol["return_definition"]["gamma"]},
    }
    evaluate.validate_checkpoint_protocol(checkpoint, protocol)
    changed = copy.deepcopy(protocol)
    changed["reward_scale"][0] *= 2
    with pytest.raises(ValueError, match="protocol/hash"):
        evaluate.validate_checkpoint_protocol(checkpoint, changed)


@pytest.mark.parametrize("field,value", [("env", "other-environment"), ("gamma", 0.5)])
def test_checkpoint_rejects_inconsistent_training_metadata(field, value):
    protocol, _ = load_protocol("configs/protocols/course_minecart_v0.json")
    checkpoint = {
        "protocol": protocol,
        "protocol_sha256": protocol_hash(protocol),
        "args": {"env": protocol["env_id"], "gamma": protocol["return_definition"]["gamma"]},
    }
    checkpoint["args"][field] = value
    with pytest.raises(ValueError, match=r"environment|gamma"):
        evaluate.validate_checkpoint_protocol(checkpoint, protocol)

import hashlib
import json

import pytest

from scripts import package_english_demo


def test_english_export_preserves_policy_and_numerical_contract(tmp_path):
    base = tmp_path / "base"
    (base / "src").mkdir(parents=True)
    (base / "src/__init__.py").write_text("")
    specs = {}
    for name, dimension in [("lunar", 4), ("mine", 3)]:
        policy = (name + "-immutable-weight-bytes").encode()
        (base / f"{name}.pt").write_bytes(policy)
        specs[name] = {
            "weights_file": f"{name}.pt",
            "weights_sha256": hashlib.sha256(policy).hexdigest(),
            "gamma": 0.99,
            "seed": 17,
            "default_weights": [1 / dimension] * dimension,
            "reward_scale": list(range(1, dimension + 1)),
            "model_kind": "categorical_ppo",
        }
    (base / "config.json").write_text(json.dumps({"environments": specs}))
    target = tmp_path / "english"
    package_english_demo.build(base, target)
    exported = json.loads((target / "config.json").read_text())
    assert exported["interface_language"] == "en"
    for name, old in specs.items():
        assert all(exported["environments"][name][key] == value for key, value in old.items())
        assert (target / old["weights_file"]).read_bytes() == (base / old["weights_file"]).read_bytes()
    with pytest.raises(ValueError, match="already exists"):
        package_english_demo.build(base, target)

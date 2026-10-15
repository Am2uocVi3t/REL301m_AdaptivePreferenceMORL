#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from importlib import metadata
from pathlib import Path
from typing import Any

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.envs.wrapper import make_mo_env
from src.evaluation.calibration import (
    calibration_plan_hash,
    calibration_source_type,
    load_calibration_plan,
    reference_points_hash,
)
from src.evaluation.protocol import protocol_hash
from src.utils.provenance import collect_provenance, write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract a predeclared deterministic environment reference front")
    parser.add_argument("--plan", default="configs/pilots/calibration_v2.json")
    parser.add_argument("--env-id", required=True)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--verify-existing", action="store_true")
    return parser.parse_args()


def file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as source_file:
        for block in iter(lambda: source_file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return value


def sorted_front(points: Any, reward_dim: int) -> np.ndarray:
    values = np.asarray(points, dtype=np.float64)
    if values.ndim != 2 or values.shape[0] == 0 or values.shape[1] != reward_dim:
        raise ValueError(f"Reference-front generator must return [N, {reward_dim}] points")
    if not np.all(np.isfinite(values)):
        raise ValueError("Reference-front generator returned non-finite values")
    order = np.lexsort(values.T[::-1])
    return values[order]


def main() -> None:
    args = parse_args()
    plan = load_calibration_plan(args.plan)
    matches = [environment for environment in plan["environments"] if environment["env_id"] == args.env_id]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one plan environment for {args.env_id}")
    environment = matches[0]
    if calibration_source_type(environment) != "environment_reference_front":
        raise ValueError(f"Environment {args.env_id} does not declare an environment reference front")

    source = environment["calibration_source"]
    output_path = Path(source["artifact"])
    if args.overwrite and args.verify_existing:
        raise ValueError("--overwrite and --verify-existing are mutually exclusive")
    if output_path.exists() and not (args.overwrite or args.verify_existing):
        raise FileExistsError(f"Refusing to overwrite reference-front artifact: {output_path}")
    if args.verify_existing and not output_path.is_file():
        raise FileNotFoundError(f"Reference-front artifact does not exist: {output_path}")

    protocol_path = Path(environment["protocol"])
    protocol = load_json(protocol_path)
    reward_dim = int(protocol["reward_dim"])
    return_definition = protocol.get("return_definition", {})
    gamma = float(source["gamma"])
    if return_definition.get("type") != "discounted" or not np.isclose(
        float(return_definition.get("gamma", -1.0)), gamma
    ):
        raise ValueError("Reference-front gamma must match the protocol return definition")
    reward_scale = np.asarray(protocol.get("reward_scale"), dtype=np.float64)
    if not args.verify_existing and (reward_scale.shape != (reward_dim,) or not np.allclose(reward_scale, 1.0)):
        raise ValueError("Reference-front extraction must precede protocol reward-scale freezing")

    package = source["package"]
    installed_version = metadata.version(str(package["name"]))
    if installed_version != package["version"]:
        raise ValueError("Installed reference-front package version does not match the plan")

    fronts: list[np.ndarray] = []
    config_name: str | None = None
    config_hash: str | None = None
    for seed in source["determinism_seeds"]:
        env = make_mo_env(args.env_id, seed=int(seed), reward_scale=np.ones(reward_dim, dtype=np.float32))
        try:
            generator = getattr(env.unwrapped, str(source["generator"]), None)
            if not callable(generator):
                raise ValueError(f"Environment {args.env_id} does not expose {source['generator']}")
            config_path = Path(getattr(env.unwrapped, "config", ""))
            if not config_path.is_file():
                raise ValueError("Reference-front environment does not expose a readable config file")
            current_config_hash = file_sha256(config_path)
            if current_config_hash != source["environment_config_sha256"]:
                raise ValueError("Environment config hash does not match the predeclared plan")
            if config_hash is not None and current_config_hash != config_hash:
                raise ValueError("Environment config changed across determinism seeds")
            config_name = config_path.name
            config_hash = current_config_hash
            fronts.append(sorted_front(generator(gamma, symmetric=bool(source["symmetric"])), reward_dim))
        finally:
            env.close()

    if any(not np.array_equal(fronts[0], front) for front in fronts[1:]):
        raise ValueError("Reference-front generator is not deterministic across the declared seeds")
    points = fronts[0]
    if len(np.unique(points, axis=0)) != len(points):
        raise ValueError("Reference-front generator returned duplicate points")

    artifact = {
        "$schema": "../schemas/reference-front-artifact.schema.json",
        "schema_version": 1,
        "kind": "environment_reference_front",
        "env_id": args.env_id,
        "reward_dim": reward_dim,
        "return_definition": {"type": "discounted", "gamma": gamma},
        "plan": args.plan,
        "plan_sha256": calibration_plan_hash(plan),
        "protocol": str(protocol_path),
        "protocol_sha256": protocol_hash(protocol),
        "generator": {
            "name": source["generator"],
            "gamma": gamma,
            "symmetric": bool(source["symmetric"]),
            "package": package,
            "environment_config_name": config_name,
            "environment_config_sha256": config_hash,
            "determinism_seeds": source["determinism_seeds"],
            "deterministic_across_seeds": True,
        },
        "points": points.tolist(),
        "points_sha256": reference_points_hash(points),
        "provenance": collect_provenance(vars(args)),
    }
    if args.verify_existing:
        existing = load_json(output_path)
        if existing.get("plan_sha256") != artifact["plan_sha256"]:
            raise ValueError("Existing reference-front plan hash does not match")
        if existing.get("env_id") != artifact["env_id"] or existing.get("reward_dim") != artifact["reward_dim"]:
            raise ValueError("Existing reference-front environment contract does not match")
        if existing.get("return_definition") != artifact["return_definition"]:
            raise ValueError("Existing reference-front return definition does not match")
        if existing.get("generator") != artifact["generator"]:
            raise ValueError("Existing reference-front generator provenance does not match")
        if existing.get("points_sha256") != artifact["points_sha256"] or existing.get("points") != artifact["points"]:
            raise ValueError("Existing reference-front points do not reproduce exactly")
        print(f"Verified {len(points)} deterministic reference-front points in {output_path.resolve()}")
        return
    write_json(output_path, artifact)
    print(f"Wrote {len(points)} deterministic reference-front points to {output_path.resolve()}")


if __name__ == "__main__":
    main()

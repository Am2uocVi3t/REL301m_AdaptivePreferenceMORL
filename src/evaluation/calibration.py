from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np


def load_calibration_plan(path: str | Path) -> dict[str, Any]:
    plan = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_calibration_plan(plan)
    return plan


def calibration_plan_hash(plan: dict[str, Any]) -> str:
    encoded = json.dumps(plan, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def reference_points_hash(points: np.ndarray) -> str:
    values = np.asarray(points, dtype=np.float64)
    encoded = json.dumps(values.tolist(), separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def calibration_source_type(environment: dict[str, Any]) -> str:
    source = environment.get("calibration_source")
    if source is None:
        return "validation_pilot"
    if not isinstance(source, dict) or not isinstance(source.get("type"), str):
        raise ValueError("calibration_source must be an object with a type")
    return str(source["type"])


def validate_calibration_plan(plan: dict[str, Any]) -> None:
    schema_version = plan.get("schema_version")
    if schema_version not in {1, 2}:
        raise ValueError("Calibration plan schema_version must be 1 or 2")
    if plan.get("status") != "predeclared":
        raise ValueError("Calibration plan must have status='predeclared'")
    if plan.get("source_split") != "validation":
        raise ValueError("Calibration may use only the validation split")
    if plan.get("method") != "uniform-pcqn":
        raise ValueError("Calibration must use uniform-pcqn to avoid allocation-induced sampling bias")

    seeds = plan.get("seeds")
    if not isinstance(seeds, list) or len(seeds) < 2 or not all(isinstance(seed, int) for seed in seeds):
        raise ValueError("Calibration plan must define at least two integer seeds")
    if len(set(seeds)) != len(seeds):
        raise ValueError("Calibration seeds must be unique")

    training = _require_mapping(plan, "training")
    for field in ("total_timesteps", "learning_starts", "train_freq", "batch_size", "buffer_capacity"):
        if int(training.get(field, 0)) <= 0:
            raise ValueError(f"training.{field} must be positive")
    if int(training["learning_starts"]) >= int(training["total_timesteps"]):
        raise ValueError("training.learning_starts must be below total_timesteps")
    if schema_version == 2 and training.get("preference_sampling") != "uniform_fixed_protocol_pool":
        raise ValueError("Calibration v2 pilots must sample the uniform fixed protocol pool")

    evaluation = _require_mapping(plan, "evaluation")
    if int(evaluation.get("episodes_per_preference", 0)) <= 0:
        raise ValueError("evaluation.episodes_per_preference must be positive")
    if evaluation.get("shift") != "nominal":
        raise ValueError("Calibration must use the nominal environment")
    if not isinstance(evaluation.get("seed_base"), int):
        raise ValueError("evaluation.seed_base must be an integer")

    rule = _require_mapping(plan, "calibration_rule")
    if rule.get("return_field") != "episode_returns":
        raise ValueError("Calibration must use discounted episode_returns")
    scale_quantile = float(rule.get("scale_abs_quantile", 0.0))
    if not 0.5 < scale_quantile < 1.0:
        raise ValueError("calibration_rule.scale_abs_quantile must be in (0.5, 1.0)")
    span_quantiles = rule.get("reference_span_quantiles")
    if (
        not isinstance(span_quantiles, list)
        or len(span_quantiles) != 2
        or not 0.0 <= float(span_quantiles[0]) < float(span_quantiles[1]) <= 1.0
    ):
        raise ValueError("calibration_rule.reference_span_quantiles must be two increasing quantiles")
    for field in ("magnitude_floor", "reference_margin_fraction", "reference_minimum_margin"):
        if float(rule.get(field, 0.0)) <= 0.0:
            raise ValueError(f"calibration_rule.{field} must be positive")

    environments = plan.get("environments")
    if not isinstance(environments, list) or len(environments) < 1:
        raise ValueError("Calibration plan must define at least one environment")
    ids: list[str] = []
    for environment in environments:
        if not isinstance(environment, dict) or not environment.get("env_id") or not environment.get("protocol"):
            raise ValueError("Each calibration environment needs env_id and protocol")
        source = environment.get("calibration_source")
        if schema_version == 2 and not isinstance(source, dict):
            raise ValueError("Every calibration v2 environment needs calibration_source")
        source_type = calibration_source_type(environment)
        if source_type == "validation_pilot":
            if source is not None and source.get("preference_sampling") != "uniform_fixed_protocol_pool":
                raise ValueError("Validation pilots must sample the uniform fixed protocol pool")
        elif source_type == "environment_reference_front":
            if not isinstance(source, dict):
                raise ValueError("Environment reference-front source must be an object")
            required = (
                "artifact",
                "generator",
                "gamma",
                "symmetric",
                "package",
                "environment_config_sha256",
                "determinism_seeds",
            )
            if any(field not in source for field in required):
                raise ValueError("Environment reference-front source is incomplete")
            if source["generator"] != "pareto_front":
                raise ValueError("Only the audited pareto_front generator is supported")
            if not 0.0 < float(source["gamma"]) <= 1.0:
                raise ValueError("Reference-front gamma must be in (0, 1]")
            if not isinstance(source["symmetric"], bool):
                raise ValueError("Reference-front symmetric must be boolean")
            package = source["package"]
            if not isinstance(package, dict) or not package.get("name") or not package.get("version"):
                raise ValueError("Reference-front package name and version are required")
            config_hash = source["environment_config_sha256"]
            if not isinstance(config_hash, str) or len(config_hash) != 64:
                raise ValueError("Reference-front environment config needs a SHA-256 hash")
            determinism_seeds = source["determinism_seeds"]
            if (
                not isinstance(determinism_seeds, list)
                or len(determinism_seeds) < 2
                or not all(isinstance(seed, int) for seed in determinism_seeds)
                or len(set(determinism_seeds)) != len(determinism_seeds)
            ):
                raise ValueError("Reference-front determinism seeds must be unique integers")
        else:
            raise ValueError(f"Unsupported calibration source type: {source_type}")
        ids.append(str(environment["env_id"]))
    if len(set(ids)) != len(ids):
        raise ValueError("Calibration environment IDs must be unique")


def validate_calibration_artifact(
    artifact: dict[str, Any],
    *,
    expected_env_id: str,
    expected_protocol_sha256: str,
    expected_seed: int,
    return_field: str,
    expected_checkpoint: str | None = None,
    expected_episodes_per_preference: int | None = None,
) -> np.ndarray:
    if artifact.get("split") != "validation":
        raise ValueError("Calibration artifacts must come from the validation split, never test")
    if artifact.get("shift") != "nominal":
        raise ValueError("Calibration artifacts must use the nominal environment")

    protocol = artifact.get("protocol")
    if not isinstance(protocol, dict) or protocol.get("env_id") != expected_env_id:
        raise ValueError(f"Calibration artifact does not match environment {expected_env_id}")
    reward_dim = int(protocol.get("reward_dim", 0))
    reward_scale = np.asarray(protocol.get("reward_scale"), dtype=np.float64)
    if reward_scale.shape != (reward_dim,) or not np.allclose(reward_scale, 1.0):
        raise ValueError("Calibration artifacts must be collected with identity reward_scale")

    provenance = artifact.get("provenance")
    config = provenance.get("config") if isinstance(provenance, dict) else None
    if not isinstance(config, dict):
        raise ValueError("Calibration artifact is missing provenance.config")
    if config.get("protocol_sha256") != expected_protocol_sha256:
        raise ValueError("Calibration artifact protocol hash does not match the predeclared plan")
    if int(config.get("seed", -1)) != expected_seed:
        raise ValueError("Calibration artifact evaluation seed does not match the pilot manifest")
    if expected_checkpoint is not None and config.get("model_path") != expected_checkpoint:
        raise ValueError("Calibration artifact checkpoint does not match the pilot manifest")
    if (
        expected_episodes_per_preference is not None
        and int(config.get("episodes_per_preference", -1)) != expected_episodes_per_preference
    ):
        raise ValueError("Calibration artifact episode budget does not match the pilot plan")

    values = np.asarray(artifact.get(return_field), dtype=np.float64)
    if values.ndim != 3 or values.shape[2] != reward_dim or values.size == 0:
        raise ValueError(f"Calibration artifact {return_field} must have shape [preferences, episodes, {reward_dim}]")
    if not np.all(np.isfinite(values)):
        raise ValueError("Calibration returns must be finite")
    if expected_episodes_per_preference is not None and values.shape[1] != expected_episodes_per_preference:
        raise ValueError("Calibration return tensor does not match the pilot episode budget")
    return values.reshape(-1, reward_dim)


def validate_reference_front_artifact(
    artifact: dict[str, Any],
    *,
    expected_env_id: str,
    expected_reward_dim: int,
    expected_gamma: float,
    expected_plan_sha256: str,
    expected_protocol_sha256: str,
    expected_source: dict[str, Any],
) -> np.ndarray:
    if artifact.get("schema_version") != 1 or artifact.get("kind") != "environment_reference_front":
        raise ValueError("Artifact is not a versioned environment reference front")
    if artifact.get("env_id") != expected_env_id or int(artifact.get("reward_dim", 0)) != expected_reward_dim:
        raise ValueError("Reference-front environment or reward dimension does not match")
    return_definition = artifact.get("return_definition")
    if (
        not isinstance(return_definition, dict)
        or return_definition.get("type") != "discounted"
        or not np.isclose(float(return_definition.get("gamma", -1.0)), expected_gamma)
    ):
        raise ValueError("Reference-front return definition does not match the protocol")
    if artifact.get("plan_sha256") != expected_plan_sha256:
        raise ValueError("Reference-front plan hash does not match")
    if artifact.get("protocol_sha256") != expected_protocol_sha256:
        raise ValueError("Reference-front protocol hash does not match")

    generator = artifact.get("generator")
    if not isinstance(generator, dict):
        raise ValueError("Reference-front generator provenance is missing")
    if generator.get("name") != expected_source.get("generator"):
        raise ValueError("Reference-front generator does not match")
    if generator.get("symmetric") is not expected_source.get("symmetric"):
        raise ValueError("Reference-front symmetric argument does not match")
    if generator.get("package") != expected_source.get("package"):
        raise ValueError("Reference-front package provenance does not match")
    if generator.get("environment_config_sha256") != expected_source.get("environment_config_sha256"):
        raise ValueError("Reference-front environment config hash does not match")
    if generator.get("determinism_seeds") != expected_source.get("determinism_seeds"):
        raise ValueError("Reference-front determinism seeds do not match")
    if generator.get("deterministic_across_seeds") is not True:
        raise ValueError("Reference front was not deterministic across declared seeds")

    points = np.asarray(artifact.get("points"), dtype=np.float64)
    if points.ndim != 2 or points.shape[0] == 0 or points.shape[1] != expected_reward_dim:
        raise ValueError(f"Reference-front points must have shape [N, {expected_reward_dim}]")
    if not np.all(np.isfinite(points)):
        raise ValueError("Reference-front points must be finite")
    if len(np.unique(points, axis=0)) != len(points):
        raise ValueError("Reference-front points must be unique")
    order = np.lexsort(points.T[::-1])
    if not np.array_equal(order, np.arange(len(points))):
        raise ValueError("Reference-front points must be lexicographically sorted")
    if artifact.get("points_sha256") != reference_points_hash(points):
        raise ValueError("Reference-front points hash does not match")
    return points


def propose_calibration(
    returns: np.ndarray,
    rule: dict[str, Any],
    *,
    allow_degenerate: bool = False,
) -> dict[str, Any]:
    values = np.asarray(returns, dtype=np.float64)
    if values.ndim != 2 or values.shape[0] == 0 or not np.all(np.isfinite(values)):
        raise ValueError("Calibration returns must be a finite non-empty [episodes, objectives] matrix")

    scale_quantile = float(rule["scale_abs_quantile"])
    magnitude_floor = float(rule["magnitude_floor"])
    magnitudes = np.quantile(np.abs(values), scale_quantile, axis=0)
    degenerate_indices = np.flatnonzero(magnitudes <= magnitude_floor).tolist()
    if degenerate_indices and not allow_degenerate:
        indices = degenerate_indices
        raise ValueError(f"Objectives {indices} lack enough magnitude for stable scaling")

    safe_magnitudes = magnitudes.copy()
    safe_magnitudes[degenerate_indices] = 1.0
    reward_scale = 1.0 / safe_magnitudes
    scaled = values * reward_scale
    lower_quantile, upper_quantile = (float(value) for value in rule["reference_span_quantiles"])
    robust_lower = np.quantile(scaled, lower_quantile, axis=0)
    robust_upper = np.quantile(scaled, upper_quantile, axis=0)
    robust_span = robust_upper - robust_lower
    reference_margin = np.maximum(
        robust_span * float(rule["reference_margin_fraction"]),
        float(rule["reference_minimum_margin"]),
    )
    scaled_minimum = scaled.min(axis=0)
    reference_point = scaled_minimum - reference_margin
    dominated_by_every_point = bool(np.all(scaled > reference_point))
    if not dominated_by_every_point:
        raise RuntimeError("Constructed reference point is not strictly dominated by every pilot return")

    return {
        "sample_count": len(values),
        "degenerate_objectives": degenerate_indices,
        "original_return_min": values.min(axis=0).tolist(),
        "original_return_max": values.max(axis=0).tolist(),
        "absolute_return_quantile": magnitudes.tolist(),
        "proposed_reward_scale": reward_scale.tolist(),
        "scaled_return_min": scaled_minimum.tolist(),
        "scaled_return_max": scaled.max(axis=0).tolist(),
        "robust_scaled_span": robust_span.tolist(),
        "reference_margin": reference_margin.tolist(),
        "proposed_reference_point": reference_point.tolist(),
        "reference_strictly_dominated_by_all_pilot_returns": dominated_by_every_point,
    }


def _require_mapping(document: dict[str, Any], field: str) -> dict[str, Any]:
    value = document.get(field)
    if not isinstance(value, dict):
        raise ValueError(f"Calibration plan {field} must be an object")
    return value

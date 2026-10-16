from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import numpy as np
import torch

from src.envs.wrapper import make_mo_env
from src.evaluation.protocol import load_protocol, protocol_hash, resolve_reward_scale
from src.models.q_network import VectorQNetwork


class MinecartDiagnosisError(RuntimeError):
    """Raised when the behavior-diagnosis contract or evidence is invalid."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_diagnosis_plan(root: Path, plan_path: Path) -> tuple[dict[str, Any], str]:
    plan = _load_json(plan_path)
    if plan.get("schema_version") != 1 or plan.get("status") != "predeclared_not_executed":
        raise MinecartDiagnosisError("Unsupported or mutable diagnosis plan")
    if plan.get("execution_authorized") is not False:
        raise MinecartDiagnosisError("The diagnosis plan must not embed execution authorization")

    firewall = _mapping(plan.get("data_firewall"), "data firewall")
    if (
        firewall.get("allowed_sources") != ["validation"]
        or firewall.get("evaluation_split") != "validation"
        or firewall.get("forbidden_split") != "test"
        or firewall.get("shift") != "nominal"
        or firewall.get("final_test_access_permitted") is not False
        or firewall.get("training_permitted") is not False
    ):
        raise MinecartDiagnosisError("Diagnosis data firewall is not validation-only")

    sources = _mapping(plan.get("sources"), "sources")
    for name in ("qualification", "source_audit"):
        reference = _mapping(sources.get(name), f"{name} source")
        source_path = _resolve_relative(root, reference.get("path"), f"{name} source")
        if sha256_file(source_path) != reference.get("sha256"):
            raise MinecartDiagnosisError(f"{name} source hash mismatch")

    environment = _mapping(plan.get("environment"), "environment")
    if environment.get("env_id") != "minecart-v0" or environment.get("shift") != "nominal":
        raise MinecartDiagnosisError("Diagnosis environment must be nominal minecart-v0")
    protocol_path = _resolve_relative(root, environment.get("protocol"), "protocol")
    protocol = _load_json(protocol_path)
    if protocol_hash(protocol) != environment.get("protocol_canonical_sha256"):
        raise MinecartDiagnosisError("Diagnosis protocol hash mismatch")

    evaluation = _mapping(plan.get("evaluation"), "evaluation")
    checkpoints = evaluation.get("checkpoints")
    if not isinstance(checkpoints, list) or not checkpoints:
        raise MinecartDiagnosisError("Diagnosis checkpoints are missing")
    expected_episodes = int(evaluation.get("preference_count", 0)) * int(evaluation.get("episodes_per_preference", 0))
    if expected_episodes <= 0 or expected_episodes != evaluation.get("episode_count_per_checkpoint"):
        raise MinecartDiagnosisError("Diagnosis episode count is inconsistent")

    audit = _load_json(_resolve_relative(root, sources["source_audit"]["path"], "source audit"))
    audited = {
        (int(job["training_seed"]), int(candidate["step"])): candidate
        for job in audit.get("jobs", [])
        for candidate in job.get("checkpoint_candidates", [])
    }
    seen: set[tuple[int, int]] = set()
    for checkpoint in checkpoints:
        record = _mapping(checkpoint, "checkpoint")
        key = (int(record.get("training_seed", -1)), int(record.get("step", -1)))
        if key in seen:
            raise MinecartDiagnosisError("Diagnosis checkpoint keys must be unique")
        seen.add(key)
        source_record = audited.get(key)
        if source_record is None:
            raise MinecartDiagnosisError(f"Checkpoint {key} is absent from the source audit")
        if record.get("path") != source_record.get("path") or record.get("sha256") != source_record.get("sha256"):
            raise MinecartDiagnosisError(f"Checkpoint {key} does not match the source audit")
        checkpoint_path = _resolve_relative(root, record.get("path"), f"checkpoint {key}")
        if sha256_file(checkpoint_path) != record.get("sha256"):
            raise MinecartDiagnosisError(f"Checkpoint {key} hash mismatch")

    _resolve_relative(root, plan.get("output"), "output", must_exist=False)
    return plan, sha256_file(plan_path)


def summarize_episode(
    *,
    actions: Sequence[int],
    departed_flags: Sequence[bool],
    cargo_before: Sequence[float],
    cargo_after: Sequence[float],
    rewards: np.ndarray,
    terminated: bool,
    truncated: bool,
    action_count: int,
    mine_action: int,
    ore_objective_indices: Sequence[int],
) -> dict[str, Any]:
    lengths = {len(actions), len(departed_flags), len(cargo_before), len(cargo_after), len(rewards)}
    if len(lengths) != 1 or not actions:
        raise MinecartDiagnosisError("Episode trace lengths are inconsistent or empty")
    action_values = np.asarray(actions, dtype=np.int64)
    if np.any(action_values < 0) or np.any(action_values >= action_count):
        raise MinecartDiagnosisError("Episode trace contains an invalid action")
    reward_values = np.asarray(rewards, dtype=np.float32)
    if reward_values.ndim != 2 or not np.all(np.isfinite(reward_values)):
        raise MinecartDiagnosisError("Episode rewards are malformed or non-finite")
    ore_indices = np.asarray(ore_objective_indices, dtype=np.int64)
    if np.any(ore_indices < 0) or np.any(ore_indices >= reward_values.shape[1]):
        raise MinecartDiagnosisError("Ore objective index is invalid")

    cargo_before_values = np.asarray(cargo_before, dtype=np.float32)
    cargo_after_values = np.asarray(cargo_after, dtype=np.float32)
    successful_mining = bool(np.any(cargo_after_values > cargo_before_values + 1e-8))
    ore_returns = reward_values[:, ore_indices].sum(axis=0)
    delivered = bool(np.any(ore_returns > 0.0))
    action_counts = np.bincount(action_values, minlength=action_count).astype(int)
    return {
        "action_counts": action_counts.tolist(),
        "departed": bool(any(departed_flags)),
        "used_mine_action": bool(action_counts[mine_action] > 0),
        "successful_mining": successful_mining,
        "ore_delivery": delivered,
        "cargo_but_no_delivery": successful_mining and not delivered,
        "terminated_at_base": bool(terminated),
        "truncated": bool(truncated),
        "positive_ore_objectives": (ore_returns > 0.0).tolist(),
        "ore_returns": ore_returns.tolist(),
        "length": len(actions),
    }


def aggregate_episode_summaries(
    episodes: Sequence[Mapping[str, Any]], *, action_count: int, ore_objective_count: int
) -> dict[str, Any]:
    if not episodes:
        raise MinecartDiagnosisError("Checkpoint diagnosis contains no episodes")
    action_counts = np.zeros(action_count, dtype=np.int64)
    positive_ore = np.zeros(ore_objective_count, dtype=np.int64)
    totals = {
        "episodes_departed": 0,
        "episodes_with_mine_action": 0,
        "episodes_with_successful_mining": 0,
        "episodes_with_ore_delivery": 0,
        "episodes_with_cargo_but_no_delivery": 0,
        "episodes_terminated_at_base": 0,
        "episodes_truncated": 0,
        "environment_steps": 0,
    }
    for episode in episodes:
        counts = np.asarray(episode["action_counts"], dtype=np.int64)
        positives = np.asarray(episode["positive_ore_objectives"], dtype=bool)
        if counts.shape != (action_count,) or positives.shape != (ore_objective_count,):
            raise MinecartDiagnosisError("Episode summary shape mismatch")
        action_counts += counts
        positive_ore += positives
        totals["episodes_departed"] += int(bool(episode["departed"]))
        totals["episodes_with_mine_action"] += int(bool(episode["used_mine_action"]))
        totals["episodes_with_successful_mining"] += int(bool(episode["successful_mining"]))
        totals["episodes_with_ore_delivery"] += int(bool(episode["ore_delivery"]))
        totals["episodes_with_cargo_but_no_delivery"] += int(bool(episode["cargo_but_no_delivery"]))
        totals["episodes_terminated_at_base"] += int(bool(episode["terminated_at_base"]))
        totals["episodes_truncated"] += int(bool(episode["truncated"]))
        totals["environment_steps"] += int(episode["length"])
    return {
        "episodes": len(episodes),
        "action_counts": action_counts.tolist(),
        **totals,
        "positive_ore_episodes_per_objective": positive_ore.tolist(),
    }


def evaluate_checkpoint_behavior(
    root: Path,
    plan: Mapping[str, Any],
    checkpoint_record: Mapping[str, Any],
    *,
    device: str,
) -> dict[str, Any]:
    environment = _mapping(plan.get("environment"), "environment")
    evaluation = _mapping(plan.get("evaluation"), "evaluation")
    protocol_path = _resolve_relative(root, environment.get("protocol"), "protocol")
    protocol, preferences = load_protocol(protocol_path, "validation")
    if len(preferences) != int(evaluation["preference_count"]):
        raise MinecartDiagnosisError("Validation preference count mismatch")

    checkpoint_path = _resolve_relative(root, checkpoint_record.get("path"), "checkpoint")
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=True)
    gamma = float(protocol["return_definition"]["gamma"])
    if not np.isclose(float(checkpoint.get("args", {}).get("gamma", gamma)), gamma):
        raise MinecartDiagnosisError("Checkpoint gamma does not match the protocol")

    env = make_mo_env(
        str(environment["env_id"]),
        seed=int(evaluation["seed_base"]),
        reward_scale=resolve_reward_scale(protocol),
    )
    try:
        observation_shape = env.observation_space.shape
        action_count = int(environment["action_count"])
        actual_action_count = getattr(env.action_space, "n", None)
        if observation_shape is None or len(observation_shape) != 1 or actual_action_count != action_count:
            raise MinecartDiagnosisError("Minecart observation or action contract mismatch")
        architecture = checkpoint.get("architecture", {})
        network = VectorQNetwork(
            state_dim=int(observation_shape[0]),
            action_dim=action_count,
            reward_dim=int(protocol["reward_dim"]),
            hidden_dims=architecture.get("hidden_dims", (256, 256)),
            num_heads=int(architecture.get("num_heads", 3)),
        )
        network.load_state_dict(checkpoint["model_state_dict"])
        network.to(device).eval()
        base_env: Any = env.unwrapped
        mine_action = int(environment["mine_action"])
        ore_indices = [int(value) for value in environment["ore_objective_indices"]]
        episodes_per_preference = int(evaluation["episodes_per_preference"])
        seed_base = int(evaluation["seed_base"])
        episode_summaries = []
        with torch.no_grad():
            for preference_index, preference in enumerate(preferences):
                preference_tensor = torch.as_tensor(preference, dtype=torch.float32, device=device).unsqueeze(0)
                for episode_index in range(episodes_per_preference):
                    episode_seed = seed_base + preference_index * episodes_per_preference + episode_index
                    observation, _ = env.reset(seed=episode_seed)
                    terminated = truncated = False
                    actions: list[int] = []
                    departed_flags: list[bool] = []
                    cargo_before: list[float] = []
                    cargo_after: list[float] = []
                    rewards: list[np.ndarray] = []
                    while not (terminated or truncated):
                        before = float(np.sum(base_env.cart.content))
                        state_tensor = torch.as_tensor(observation, dtype=torch.float32, device=device).unsqueeze(0)
                        action, _ = network.predict_action(state_tensor, preference_tensor, head_idx=None)
                        observation, reward, terminated, truncated, _ = env.step(action)
                        actions.append(action)
                        departed_flags.append(bool(base_env.cart.departed))
                        cargo_before.append(before)
                        cargo_after.append(float(np.sum(base_env.cart.content)))
                        rewards.append(np.asarray(reward, dtype=np.float32))
                    episode_summaries.append(
                        summarize_episode(
                            actions=actions,
                            departed_flags=departed_flags,
                            cargo_before=cargo_before,
                            cargo_after=cargo_after,
                            rewards=np.asarray(rewards, dtype=np.float32),
                            terminated=terminated,
                            truncated=truncated,
                            action_count=action_count,
                            mine_action=mine_action,
                            ore_objective_indices=ore_indices,
                        )
                    )
    finally:
        env.close()

    summary = aggregate_episode_summaries(
        episode_summaries,
        action_count=action_count,
        ore_objective_count=len(ore_indices),
    )
    if summary["episodes"] != int(evaluation["episode_count_per_checkpoint"]):
        raise MinecartDiagnosisError("Checkpoint episode count mismatch")
    return {
        "training_seed": int(checkpoint_record["training_seed"]),
        "step": int(checkpoint_record["step"]),
        "role": checkpoint_record["role"],
        "checkpoint": {"path": checkpoint_record["path"], "sha256": checkpoint_record["sha256"]},
        **summary,
    }


def build_mechanism_assessment(checkpoints: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    positive = [record for record in checkpoints if int(record["episodes_with_ore_delivery"]) > 0]
    lost_after_positive = False
    by_seed: dict[int, list[Mapping[str, Any]]] = {}
    for record in checkpoints:
        by_seed.setdefault(int(record["training_seed"]), []).append(record)
    for records in by_seed.values():
        ordered = sorted(records, key=lambda item: int(item["step"]))
        seen_positive = False
        for record in ordered:
            has_delivery = int(record["episodes_with_ore_delivery"]) > 0
            lost_after_positive = lost_after_positive or (seen_positive and not has_delivery)
            seen_positive = seen_positive or has_delivery

    persistent_cargo_without_delivery = any(
        int(record["episodes_with_cargo_but_no_delivery"]) > 0 for record in checkpoints
    )
    if positive and lost_after_positive:
        leading_mechanism = "prioritized_replay"
        rationale = (
            "Successful ore trajectories appear and later disappear within a seed, supporting "
            "rare-transition retention as the leading v2 target."
        )
    elif persistent_cargo_without_delivery:
        leading_mechanism = "n_step_returns"
        rationale = (
            "Policies acquire cargo without delivering it, supporting delayed return credit as the leading v2 target."
        )
    else:
        leading_mechanism = "unresolved_stop_before_v2"
        rationale = "The trace does not satisfy the predeclared evidence rule for prioritized replay or n-step returns."
    return {
        "positive_checkpoint_count": len(positive),
        "delivery_lost_after_positive_within_seed": lost_after_positive,
        "cargo_without_delivery_observed": persistent_cargo_without_delivery,
        "leading_v2_mechanism": leading_mechanism,
        "rationale": rationale,
    }


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise MinecartDiagnosisError(f"Cannot read JSON {path}: {error}") from error
    if not isinstance(value, dict):
        raise MinecartDiagnosisError(f"JSON root must be an object: {path}")
    return value


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise MinecartDiagnosisError(f"{label} must be an object")
    return value


def _resolve_relative(root: Path, value: Any, label: str, *, must_exist: bool = True) -> Path:
    if not isinstance(value, str) or not value or Path(value).is_absolute():
        raise MinecartDiagnosisError(f"{label} path must be non-empty and relative")
    path = (root / value).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as error:
        raise MinecartDiagnosisError(f"{label} path escapes the repository") from error
    if must_exist and not path.is_file():
        raise MinecartDiagnosisError(f"{label} file is missing: {path}")
    return path

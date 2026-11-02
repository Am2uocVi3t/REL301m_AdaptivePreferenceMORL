"""Utility-preserving categorical PPO with a PopArt vector critic.

Paper-motivated components: arxiv.org/abs/2407.16807, Eq10/19/21.
Project departures are frozen in ONPOLICY_IMPLEMENTATION_V1.md.
"""

from __future__ import annotations

import math
from typing import Any

import torch
from torch import nn
from torch.distributions import Categorical


class MultiBody(nn.Module):
    def __init__(self, state_dim: int, reward_dim: int, output_dim: int, width: int):
        super().__init__()
        self.bodies = nn.ModuleList([nn.Linear(state_dim, width) for _ in range(reward_dim)])
        self.hidden = nn.Linear(width, width)
        self.head = nn.Linear(width, output_dim)
        for layer in [*self.bodies, self.hidden, self.head]:
            nn.init.orthogonal_(layer.weight, math.sqrt(2))
            nn.init.zeros_(layer.bias)

    def forward(self, state: torch.Tensor, preference: torch.Tensor) -> torch.Tensor:
        bodies = torch.stack([torch.relu(body(state)) for body in self.bodies], dim=-2)
        merged = (bodies * preference.unsqueeze(-1)).sum(-2)
        return self.head(torch.relu(self.hidden(merged)))


class ActorCritic(nn.Module):
    mean: torch.Tensor
    second: torch.Tensor
    std: torch.Tensor

    def __init__(self, state_dim: int = 7, action_dim: int = 6, reward_dim: int = 3, width: int = 256):
        super().__init__()
        self.actor = MultiBody(state_dim, reward_dim, action_dim, width)
        self.critic = MultiBody(state_dim, reward_dim, reward_dim, width)
        nn.init.orthogonal_(self.actor.head.weight, 0.01)
        nn.init.orthogonal_(self.critic.head.weight, 1.0)
        self.register_buffer("mean", torch.zeros(reward_dim))
        self.register_buffer("second", torch.ones(reward_dim))
        self.register_buffer("std", torch.ones(reward_dim))

    def distribution(self, state: torch.Tensor, preference: torch.Tensor) -> Categorical:
        return Categorical(logits=self.actor(state, preference))

    def value(self, state: torch.Tensor, preference: torch.Tensor) -> torch.Tensor:
        return self.critic(state, preference) * self.std + self.mean

    @torch.no_grad()
    def update_popart(self, targets: torch.Tensor, rate: float, floor: float) -> None:
        old_mean, old_std = self.mean.clone(), self.std.clone()
        self.mean.lerp_(targets.mean(0), rate)
        self.second.lerp_(targets.square().mean(0), rate)
        self.std.copy_((self.second - self.mean.square()).clamp_min(floor**2).sqrt())
        self.critic.head.weight.mul_((old_std / self.std).unsqueeze(1))
        self.critic.head.bias.copy_((old_std * self.critic.head.bias + old_mean - self.mean) / self.std)


def td1_returns(
    rewards: torch.Tensor,
    next_values: torch.Tensor,
    terminated: torch.Tensor,
    truncated: torch.Tensor,
    gamma: float,
) -> torch.Tensor:
    """[time,stream,objective]; next_values use PRE-reset states/preferences."""
    result = torch.empty_like(rewards)
    carry = next_values[-1]
    for t in reversed(range(len(rewards))):
        boundary = (terminated[t] | truncated[t]).unsqueeze(-1)
        continuation = torch.where(boundary, next_values[t], carry)
        continuation = torch.where(terminated[t].unsqueeze(-1), 0.0, continuation)
        carry = rewards[t] + gamma * continuation
        result[t] = carry
    return result


def scalar_advantage(returns: torch.Tensor, values: torch.Tensor, preferences: torch.Tensor) -> torch.Tensor:
    return ((returns - values) * preferences).sum(-1)


def clipped_policy_loss(new_logp: torch.Tensor, old_logp: torch.Tensor, advantage: torch.Tensor, clip: float):
    ratio = (new_logp - old_logp).exp()
    return -torch.minimum(ratio * advantage, ratio.clamp(1 - clip, 1 + clip) * advantage).mean()


class PPO:
    def __init__(self, model: ActorCritic, plan: dict[str, Any]):
        self.model, self.plan = model, plan
        self.actor_optimizer = torch.optim.Adam(model.actor.parameters(), lr=plan["actor_lr"], eps=plan["adam_eps"])
        self.critic_optimizer = torch.optim.Adam(model.critic.parameters(), lr=plan["critic_lr"], eps=plan["adam_eps"])
        self.multiplier = float(plan["entropy_initial_multiplier"])
        self.actor_updates = self.critic_updates = 0

    def update(self, batch: dict[str, torch.Tensor], step: int) -> dict[str, float]:
        p, model = self.plan, self.model
        targets = td1_returns(
            batch["rewards"], batch["next_values"], batch["terminated"], batch["truncated"], p["gamma"]
        )
        flat = {key: value.flatten(0, 1) for key, value in batch.items()}
        targets = targets.flatten(0, 1)
        advantage = scalar_advantage(targets, flat["values"], flat["preferences"])
        advantage = (advantage - advantage.mean()) / advantage.std(unbiased=False).clamp_min(1e-8)
        model.update_popart(targets, p["popart_rate"], p["popart_std_floor"])
        normalized_targets = (targets - model.mean) / model.std
        target_entropy = math.log(6) + min(step / p["training_interactions"], 1) * (p["entropy_end"] - math.log(6))
        diagnostics = []
        for _ in range(p["epochs"]):
            order = torch.randperm(len(targets), device=targets.device)
            for index in order.tensor_split(p["minibatches"]):
                s, w = flat["states"][index], flat["preferences"][index]
                for _ in range(p["critic_steps_per_actor"]):
                    loss_c = (model.critic(s, w) - normalized_targets[index]).square().mean()
                    self.critic_optimizer.zero_grad(set_to_none=True)
                    loss_c.backward()
                    nn.utils.clip_grad_norm_(model.critic.parameters(), p["max_grad_norm"], error_if_nonfinite=True)
                    self.critic_optimizer.step()
                    self.critic_updates += 1
                distribution = model.distribution(s, w)
                logp = distribution.log_prob(flat["actions"][index])
                loss_pi = clipped_policy_loss(logp, flat["logp"][index], advantage[index], p["clip"])
                entropy = distribution.entropy().mean()
                error = target_entropy - float(entropy.detach())
                coefficient = self.multiplier + p["entropy_damping"] * error
                loss = loss_pi - coefficient * entropy
                self.actor_optimizer.zero_grad(set_to_none=True)
                loss.backward()
                nn.utils.clip_grad_norm_(model.actor.parameters(), p["max_grad_norm"], error_if_nonfinite=True)
                self.actor_optimizer.step()
                self.multiplier += p["entropy_multiplier_lr"] * error
                self.actor_updates += 1
                diagnostics.append(torch.stack([loss_pi.detach(), loss_c.detach(), entropy.detach()]))
        means = torch.stack(diagnostics).mean(0).cpu().tolist()
        if not all(math.isfinite(x) for x in [*means, self.multiplier]):
            raise FloatingPointError("Nonfinite PPO diagnostics")
        return dict(zip(["policy_loss", "value_loss", "entropy"], means, strict=True)) | {
            "entropy_target": target_entropy,
            "entropy_multiplier": self.multiplier,
        }

    def state_dict(self) -> dict[str, Any]:
        return {
            "model": self.model.state_dict(),
            "actor_optimizer": self.actor_optimizer.state_dict(),
            "critic_optimizer": self.critic_optimizer.state_dict(),
            "multiplier": self.multiplier,
            "actor_updates": self.actor_updates,
            "critic_updates": self.critic_updates,
        }

    def load_state_dict(self, state: dict[str, Any]) -> None:
        self.model.load_state_dict(state["model"])
        self.actor_optimizer.load_state_dict(state["actor_optimizer"])
        self.critic_optimizer.load_state_dict(state["critic_optimizer"])
        self.multiplier = state["multiplier"]
        self.actor_updates, self.critic_updates = state["actor_updates"], state["critic_updates"]

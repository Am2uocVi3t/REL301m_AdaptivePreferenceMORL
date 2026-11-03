"""Lunar-specific vector GAE/PPO; frozen Minecart implementation is unchanged."""

from __future__ import annotations

import math

import torch
from torch import nn

from src.models.onpolicy import PPO, clipped_policy_loss, scalar_advantage


def gae_advantages(rewards, values, next_values, terminated, truncated, gamma, lam):
    result = torch.empty_like(rewards)
    carry = torch.zeros_like(rewards[-1])
    for t in reversed(range(len(rewards))):
        delta = rewards[t] + gamma * (~terminated[t]).unsqueeze(-1) * next_values[t] - values[t]
        carry = delta + gamma * lam * (~(terminated[t] | truncated[t])).unsqueeze(-1) * carry
        result[t] = carry
    return result


class LunarPPO(PPO):
    def update(self, batch: dict[str, torch.Tensor], step: int) -> dict[str, float]:
        p, model = self.plan, self.model
        advantages = gae_advantages(
            batch["rewards"],
            batch["values"],
            batch["next_values"],
            batch["terminated"],
            batch["truncated"],
            p["gamma"],
            p["gae_lambda"],
        )
        targets = advantages + batch["values"]
        flat = {key: value.flatten(0, 1) for key, value in batch.items()}
        targets = targets.flatten(0, 1)
        advantage = scalar_advantage(targets, flat["values"], flat["preferences"])
        advantage = (advantage - advantage.mean()) / advantage.std(unbiased=False).clamp_min(1e-8)
        model.update_popart(targets, p["popart_rate"], p["popart_std_floor"])
        normalized_targets = (targets - model.mean) / model.std
        target_entropy = math.log(4) + min(step / p["training_interactions"], 1) * (p["entropy_end"] - math.log(4))
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

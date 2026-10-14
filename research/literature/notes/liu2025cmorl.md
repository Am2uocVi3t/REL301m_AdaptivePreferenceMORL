---
paper_id: liu2025cmorl
evidence_level: full_text
---

# Efficient Discovery of Pareto Front for Multi-Objective Reinforcement Learning

Primary source: https://proceedings.iclr.cc/paper_files/paper/2025/hash/adb77ecc8ba1c2d3135c86a46b8f2496-Abstract-Conference.html

## Access report

Official ICLR 2025 full text checked on 2026-10-15.

## Relevance and mechanism

C-MORL uses initial Pareto discovery followed by constrained frontier extension; crowding distance identifies sparse regions for further search.

## Evidence and relationship to claims

Pareto-front experiments make it direct prior art for coverage-driven attention under `coverage-recency-allocation`, `conditioning-gap-allocation`, and `combined-allocation`. The repository uses one conditioned model plus recency.

## Limitations and falsifiers

The multi-policy constrained formulation has different compute assumptions. An equivalent local coverage sampler would narrow the difference.

Evidence pointer: two-stage method and experiments.

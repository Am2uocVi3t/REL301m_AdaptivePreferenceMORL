---
paper_id: yang2019envelope
evidence_level: full_text
---

# A Generalized Algorithm for Multi-Objective Reinforcement Learning and Policy Adaptation

Primary source: https://arxiv.org/abs/1908.08342

## Access report

Author-posted full text corresponding to NeurIPS 2019 checked on 2026-10-15.

## Relevance and mechanism

Envelope Q-learning changes the Bellman operator and loss so one preference-conditioned value model can select among value vectors and adapt to unseen linear preferences.

## Evidence and relationship to claims

Discrete MORL experiments assess Pareto approximation and policy adaptation, not curriculum allocation. The work is prior art for the conditioned foundation of `combined-allocation`; the repository asks which preference should receive bounded training resources.

## Limitations and falsifiers

The envelope update differs from PCQN. Evidence that its preference sampling already implements an equivalent adaptive allocation rule would reduce the distinction.

Evidence pointer: Sections 3–5 and supplementary algorithms.

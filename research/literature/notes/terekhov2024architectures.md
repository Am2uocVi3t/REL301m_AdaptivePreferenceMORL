---
paper_id: terekhov2024architectures
evidence_level: full_text
---

# In Search for Architectures and Loss Functions in Multi-Objective Reinforcement Learning

Primary source: https://arxiv.org/abs/2407.16807

## Access report

Full legal primary PDF read in the 1 November 2026 retrieval/extraction pass,
including Sections 6.2/6.3 and Appendices B/D. Ignored D-drive PDF SHA256:
dd5efd35c9238db46f921a2ffcd53bff14d164ae9772bec5833b08e8e0bfa533.
Author implementation c568cb6d689d7eaa50a2dec38197de8847f18adc checked.
This is an ARLET 2024 workshop manuscript, not a journal acceptance claim.

## Why this work is relevant

It studies architecture, policy losses, normalization and exploration entropy
for preference-conditioned MORL, including stochastic Minecart. It informs
backbone qualification before interpreting allocation results.

## Mechanism and assumptions

MOPPO extends clipped policy optimization using vector critics and preference
scalarization. Shared/multibody representations, PopArt and entropy control
are empirical design choices. Sampled-policy evaluation differs from the
deterministic argmax demo; these results do not establish greedy-demo behavior.

## Evidence and experimental protocol

Stochastic Minecart uses 4M interactions, five seeds and gamma .99. Table 2
(printed p16, introduced under Appendix C) gives hidden width 256, clip .2, eight trajectories/batch, four PPO
epochs, eight minibatches and PopArt rate .001. Appendix D reports about five
hours per Minecart run on V100. This is not a runtime prediction for our laptop.
Envelope uses a best-HV checkpoint due late collapse, whereas PPO/PCN use final
checkpoints. Source defaults also differ from paper settings (Minecart cap 192
versus long variant 1000); do not import its numerical ranking into our protocol.

## Relationship to project claims

Backbone architecture changes preference-region learnability and constrains
interpretation of all our allocation hypotheses. The paper does not test our
four allocation signals under matched controls, and does not establish an
adaptive-allocation benefit for this project.

## Limitations and possible falsifiers

Sampled-policy results need not survive deterministic action selection.
Checkpoint choice and metric can change method rankings. The old Python 3.10,
Torch 2.1.1/TorchRL .3 implementation is not a qualified drop-in for our pinned
Python 3.11/Torch 2.14 Windows runtime. A matched implementation is required
before claiming an advantage here.

## Quotable facts

Paraphrase pointers: Sections 6.2/6.3 (Minecart and baseline comparison),
Appendix C Table 2 (hyperparameters), Appendix D (compute), and author
`env/minecart.yaml` versus `env/minecart_long.yaml` (episode lengths).


## Targeted P2 follow-up — 2026-11-02

Revisited Sections5.2/6.2/6.3, AppendixA.4 and Table2 after the completed negative
P2 factorial. Author repository: https://github.com/CLAIRE-Labo/tunable-morl-public.
Pinned public train_moe.yaml was fetched again and matches the saved source
canonically. Defaults are not the paper configuration: entropy minimum .1
versus paper .4; damping .05 versus .01; cached PopArt model default .01 versus
paper .001. Minecart default horizon192 has a separate long1000 configuration.
Source/default mapping and hashes live in
research/evidence/onpolicy_primary_source_map_20261102.json. A proposed finite
PPO specialist/conditioned pilot is an adaptation under our unchanged protocol;
none of these sources proves it will resolve the current greedy-control failure.

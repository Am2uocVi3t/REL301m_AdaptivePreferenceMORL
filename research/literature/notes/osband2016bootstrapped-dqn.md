---
paper_id: osband2016bootstrapped-dqn
evidence_level: full_text
---

# Deep Exploration via Bootstrapped DQN

Primary source: https://arxiv.org/abs/1602.04621

## Access report

Final NeurIPS primary main PDF (nine pages) and official supplement (printed
pages 10--18) read in full by the read-only retrieval shard on 2026-11-02.
Legal PDFs remain ignored on D: under `artifacts/research-review-primary-sources/`.
Main SHA256 db2cfc03428dcc294839ca2497d9fb42df7a13c7564fd070d93f113bfcf37847;
supplement SHA256 385ca707763c1dcebcd5aa27e64df16510dd18120605a78bd8909f96cada4944.

## Why this work is relevant

Our learner uses shared features, bootstrap masks and an episode-fixed sampled
head during training. This source motivates a controlled policy-extraction
diagnosis before attributing poor greedy performance to absent exploration.

## Mechanism and assumptions

Main Section 3 / supplement Algorithm 1: sample a head uniformly at the start
of an episode and retain it; each head has its own DDQN target. Main Section 2
notes shared features reduce compute at the expense of head diversity.
Supplement D.1 states Atari evaluation uses ensemble voting. Our mean-Q
extraction is an adaptation and does not follow that voting recipe.

## Evidence and experimental protocol

Supplement D.1 describes Atari training: epsilon anneals from 1 to .01 over
the first 1M steps; total budget 50M agent steps / 200M frames. Main Section 6.4
offers exploitative majority/plurality voting. Supplement C.1 distinguishes
episode-fixed randomized exploration from ensembling at each training step.
These are not Minecart budgets or demonstrated MORL settings.

## Relationship to project claims

Head sampling and ensemble disagreement are established mechanisms, constraining
the project's uncertainty/combined-allocation novelty. The source does not
establish benefits of our three-head vector critic or preference allocation.

## Limitations and possible falsifiers

A train/evaluation difference is not automatically a bug. Main Section 6.2
reports reward encounters without proper learning and unstable learning in
some games. Reward in behavior data does not prove a competent extracted
policy. Our voting tie-break and MORL setup require their own evidence.

## Quotable facts

Paraphrase pointers: main Sections 2, 3, 6.2, 6.4; supplement Algorithm 1
(printed p12), C.1 (p13), D.1 (p15). No long direct quotations are used.

---
paper_id: portelas2020alp-gmm
evidence_level: full_text
---

# Teacher Algorithms for Curriculum Learning of Deep RL in Continuously Parameterized Environments

Primary source: https://proceedings.mlr.press/v100/portelas20a.html

## Access report

Open PMLR full text checked on 2026-10-15.

## Relevance and mechanism

ALP-GMM estimates absolute learning progress from episodic-return change near a previous continuous task, partitions task space with Gaussian mixtures, and uses a bandit to favor high-progress regions while exploring.

## Evidence and relationship to claims

Comparisons across continuously parameterized environments establish learning-progress curriculum as known. `learning-progress-allocation` is an incremental transfer and head-to-head signal test.

## Limitations and falsifiers

Nearest-neighbor return changes can be noisy and conflate forgetting with learning. Weak predictive validity or no causal allocation benefit would reject the hypothesis.

Evidence pointer: Sections 3–5 and ALP-GMM algorithm.

---
paper_id: chen2026morl-fb
evidence_level: full_text
---

# A Reward-Free Viewpoint on Multi-Objective Reinforcement Learning

Primary source: https://openreview.net/forum?id=IwiwmY3Mzz

## Access report

The ICLR 2026 paper was checked in full on 2026-10-15 using the author-posted arXiv version (arXiv:2604.24532) after OpenReview returned HTTP 403 to automated PDF retrieval. The temporary 37-page PDF and extracted text were kept outside Git.

## Why this work is relevant

MORL-FB is a close 2026 antecedent for preference-conditioned exploration and generalization. It changes the learned representation and latent exploration distribution using sampled preferences, so the project cannot describe preference-guided exploration itself as new. It does not, however, rank preference regions from their observed weakness, uncertainty, recency, coverage, or learning progress.

## Mechanism and assumptions

The paper treats linear-scalarization MORL as a restricted reward-free RL problem. A Forward-Backward representation factors the command-conditioned action value into a forward representation `F(s,a,z)` and a latent command `z`. At test time, a preference-weighted reward induces `z`; a policy conditioned on `z` selects actions.

Vanilla reward-free exploration samples latent commands independently of the MORL reward structure and performs poorly in the authors' experiments. MORL-FB therefore samples a preference uniformly from the simplex, maps it to a preference-guided latent command using replay mini-batches, and uses that command for rollouts. Training combines the Forward-Backward measure loss, an auxiliary vector-reward TD/Q loss, an orthonormality regularizer, and an actor objective.

The preference distribution is fixed rather than updated from regional outcomes. The adaptation happens in latent-command construction and representation learning, not in a curriculum scheduler over preference candidates.

## Evidence and experimental protocol

The primary experiments cover six MO-Gymnasium MuJoCo tasks with two to five objectives, plus discrete-control appendices. Baselines include PD-MORL, Q-Pensieve, CAPQL, Envelope Q-Learning, PCN, PG-MORL, SFOLS, MORL/D, GPI-LS, GPI-PD, and vanilla Forward-Backward RL. Continuous-control methods receive three million environment steps and are summarized over five random seeds.

The paper reports utility, hypervolume, episodic dominance, and cross-task aggregate statistics. A reduced-training-preference experiment trains only on simplex corners plus the uniform center and evaluates across the full preference set. Ablations remove preference-guided exploration or the auxiliary Q loss. A separate experiment transfers a Hopper2d representation to objectives added in Hopper3d/Hopper4d without retraining.

The reported evidence supports the value of preference-guided latent exploration within this architecture. It does not isolate an adaptive preference allocation distribution, compare rollout-only versus update-only allocation, or use held-out regional learning progress to schedule training.

## Relationship to project claims

- `combined-allocation`: MORL-FB establishes a strong modern conditioned baseline with preference-guided exploration. The project distinction is outcome-dependent allocation among preference regions under matched curriculum-evaluation budgets.
- MORL-FB does not instantiate any of the project's four scheduler scores. Algorithm 1 samples the preference uniformly and does not revise that distribution from returns.
- Its reduced-preference experiment is useful precedent for a held-out preference split, while its cross-objective transfer is different from the repository's dynamics-shift claim.

## Limitations and possible falsifiers

The method assumes linear scalarization and inherits Forward-Backward representation and exploration limitations, especially in sparse-reward or complex environments. Baseline extensions and hyperparameter optimization complicate reproduction and exact fairness. The project-level reading would be falsified if the released implementation adapts the preference sampling distribution from regional outcomes despite the fixed sampling described in Algorithm 1.

## Evidence pointers

- Sections 1 and 3: reward-free interpretation, three enhancements, and MORL-FB formulation.
- Algorithm 1 and Appendix B, Algorithm 2: uniform preference sampling, preference-guided latent construction, replay, and losses.
- Section 4: environments, baselines, three-million-step budget, five seeds, metrics, and reduced-preference generalization.
- Sections 4.1–4.2: component ablations and zero-shot cross-objective transfer.
- Section 6: limitations and future work.

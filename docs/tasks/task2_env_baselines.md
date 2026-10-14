# Task 2: Environments, shifts, and baselines

**Status:** adapters implemented; dependency and behavioral smoke runs pending.

## Core environments

- `mo-lunar-lander-v3`, four objectives.
- `minecart-v0`, three objectives under the default two-mine configuration.

Reward scales are loaded from versioned protocol JSON files and applied to training and evaluation. Current values are identity placeholders and must be frozen from pilot/training evidence before final experiments.

## Dynamics shifts

LunarLander physics parameters are passed into the environment constructor. Strict attribute overrides are available only when an environment exposes and retains the requested field. Silent no-op mutation is prohibited.

The verified heavy-gravity setting is `-11.5`; Gymnasium 1.4 requires gravity to remain strictly between `-12` and `0`, so the original proposal value `-15` is not executable.

Non-nominal Minecart shifts are currently **planned**. They must not be reported until an intervention changes transition dynamics and a behavioral smoke test detects the effect.

## Baselines

The MORL-Baselines 1.3 adapters use:

- `morl_baselines.multi_policy.envelope.envelope.Envelope`;
- `morl_baselines.multi_policy.gpi_pd.gpi_pd.GPILS`.

Run them through `scripts/train_baseline.py`. A frozen hypervolume reference point is required. The adapter matches the training interaction budget; final comparisons must additionally account for updates, evaluations, tuning, wall-clock, and memory.

## Verification still required

```bash
python scripts/train.py --help
python scripts/train_baseline.py --help
python -m pytest tests/test_envs.py -q
```

Then run reset/step and 10,000-step smoke experiments in the pinned environment before marking this task validated.

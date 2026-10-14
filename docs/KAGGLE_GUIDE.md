# Reproducible Kaggle Experiment Guide

Kaggle images, Python versions, accelerators, and quotas change. Record the actual image, Python, GPU, and installed package versions in every run instead of treating this guide as platform evidence.

## Setup

```bash
git clone https://github.com/Am2uocVi3t/REL301m_AdaptivePreferenceMORL.git
cd REL301m_AdaptivePreferenceMORL
apt-get update -y
apt-get install -y libcdd-dev swig
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pytest -q
python -m pip freeze > resolved-environment.txt
```

If Box2D, `pycddlib`, or another pinned package cannot be built in the current image, stop and record the install error. Do not silently change versions during final experiments. Python 3.11 is the recommended experiment interpreter.

WandB is optional. Set `WANDB_API_KEY` as a Kaggle secret and pass `--wandb-project REL301m-MORL` only when remote logging is desired. Local TensorBoard artifacts are always written under the run directory when TensorBoard is installed.

## Smoke run

```bash
python scripts/train.py \
  --env mo-lunar-lander-v3 \
  --protocol configs/protocols/course_mo_lunar_lander_v3.json \
  --algo adaptive-pcqn \
  --allocation-target rollout_and_update \
  --total-timesteps 10000 \
  --learning-starts 1000 \
  --eval-freq 5000 \
  --save-freq 5000 \
  --output-dir /kaggle/working/artifacts
```

Confirm that the output contains `run_manifest.json`, checkpoints, budget counters, and logs before scheduling a full run.

## Full course runs

Run paired seeds with identical protocol and budget arguments. At minimum schedule:

- `adaptive-pcqn`;
- `random-curriculum-pcqn` as the compute-matched score control;
- `uniform-pcqn`;
- required signal and allocation-target ablations.

Do not use the test split during training. Validation preferences are fixed by the protocol and reused at every checkpoint.

## Final evaluation

After selecting the checkpoint and freezing the protocol reference point:

```bash
python scripts/evaluate.py \
  --model-path /kaggle/working/artifacts/<run>/final.pt \
  --protocol configs/protocols/course_mo_lunar_lander_v3.json \
  --split test \
  --episodes-per-preference 30 \
  --shift nominal \
  --output /kaggle/working/results/<run>_test_nominal.json
```

Download the raw evaluation JSON, checkpoints, run manifest, resolved environment, logs, and notebook output. A WandB chart or notebook screenshot is not a substitute for raw per-episode results.

## Resume status

Training resume is not implemented. There is deliberately no `--load-checkpoint` flag. Split long experiments into independent complete seeded runs until resume support includes optimizer, replay, RNG, sampler, counters, and protocol state.

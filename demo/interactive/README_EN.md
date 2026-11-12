# MORL Preference Lab — English inference demo

This local application runs frozen PPO policies on actual MO-Gymnasium physics.
Both panels share the same checkpoint and initial environment seed. Preference
sliders change the policy input, never the weights. This is an inference
demonstration, not a comparison of algorithms or a final-test benchmark.

## Start

Use Python 3.11 in an isolated environment and install `requirements.txt`.
Box2D may require SWIG and matching C/C++ build tools. From the package directory:

```bash
python launch.py --port 8765
```

Open `http://127.0.0.1:8765`. Stop the server with Ctrl+C. Keep it local; use one
controlling browser tab. No API key, training, model download or paid service is
used during inference. A source clone does not include trained checkpoint files.

## Demonstration walkthrough

1. Start in LunarLander, paused. Select **Single step** to inspect one transition.
2. Move a slider. Other weights rescale so their total stays 100%. A pending
   preference changes nothing until **Run comparison** resets both panels.
3. Select **Run comparison**. Reference stays at the declared default; your
   panel uses the selected preference. Pause/resume and speed controls affect
   presentation; every executed physics step is retained by the backend.
4. **Change preferences during the episode** applies at the next inference
   step and keeps episode history. The warning explains why this is no longer
   a matched-initial-state comparison. Reset for a fresh comparison.
5. Switch to Minecart. Compare the balanced profile with an ore-heavy profile.
   Corner weights can fail; do not hide failures or promise universal control.
6. Choose **Native renderer** to inspect the original physics view. Styling
   changes no actions, rewards or collisions. Download trace JSON for inspection.

## Interpreting the display

Returns are raw cumulative reward components in different units; they are not
success percentages. Costs are negative rewards, so assigning more weight to a
cost objective places greater importance on avoiding that cost. Utility uses
the fixed reward scales and discount factor recorded in `config.json`.

Minecart shows confirmation seed 20264311, selected by the predeclared lowest
seed rule. Lunar shows specialist pilot 20265311. Separate two-seed Lunar
confirmation is reported in the course report, not substituted into this demo.
Three Minecart training replications and two Lunar confirmations do not prove
arbitrary-preference competence, dynamics robustness or adaptive superiority.

If a request fails, the application halts instead of automatically retrying a
physics step. Reset, or reload if another tab changed the session generation.
The report and its appendix provide implementation, evidence and limitations.

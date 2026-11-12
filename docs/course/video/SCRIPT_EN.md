# REL301m — narration script

Target: about two minutes at a calm pace. Read the body naturally; headings are
editing cues, not spoken lines. Pause or adjust the script to fit your own pace.

## Introduction

Hello. We are presenting our REL301m project on preference-conditioned
multi-objective reinforcement learning. Instead of optimizing one reward, the
agent balances several objectives according to a preference vector.

## LunarLander

Here is our live inference application. Both panels use the same trained model
and the same initial environment seed. The left panel keeps the reference
preference. On the right, we can choose our own trade-off.

We begin with LunarLander. Its objectives include landing outcome, shaping,
and the costs of the main and side engines. Single step lets us inspect one
action and its reward components. Run comparison resets both environments
and starts the policies from matched initial states.

Moving a slider changes the preference input. It does not train the model or
modify its weights. Normally the change remains pending until we reset.
The native renderer shows the original environment graphics, with no extra
physics step caused by switching the display.

## Minecart

In Minecart, the objectives are delivered ore of two types and fuel cost.
We can compare the balanced reference with an ore-heavy preference. The
application still uses one frozen actor for both panels.

Live preference changes can also take effect during an episode. This keeps
the previous trajectory, so the panels may now have different histories.
For a fresh comparison, we reset to the same initial seed. The exported JSON
trace records observations, actions, preference inputs and vector rewards.

## Evidence and conclusion

Our report preserves the unsuccessful value-learning studies as well as the
later PPO results. Three Minecart confirmation training seeds passed the
specified task gates. Two separate Lunar confirmation seeds passed the
trained-profile landing gate. The Lunar actor shown here is the earlier
specialist pilot, not one of those two confirmation models.

These are bounded results. They do not prove reliable behavior at every
preference, robustness to new dynamics, or an advantage from adaptive allocation.
The demo is inference only, and the original final-test gate remains locked.

Thank you. The repository contains the implementation and recorded evidence;
the English report explains the methods, results, limitations and reproduction
steps in detail.

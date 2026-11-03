# Frozen PPO preference diagnosis — 3 November 2026

Portable final actors, five new environment cases20266511–20266515 per profile.
No training, candidate changes, checkpoint selection or original final-test access.
55 episodes /18,394 diagnostic steps; all55 traces replayed exactly for another
18,394 diagnostic replay steps. Source: research/evidence/ppo_demo_preference_diagnosis_v1.json;
audit: research/qualification/ppo_demo_preference_diagnosis_v1.json. Executor-only.

| Environment | Profile | Native task success | Mean frozen utility | Mean steps |
|---|---|---|---|---|
| lunar | default | 4/5 | 0.072615 | 329.6 |
| lunar | uniform | 4/5 | -0.009436 | 300.8 |
| lunar | corner0 | 4/5 | 0.114786 | 351.4 |
| lunar | corner1 | 1/5 | 0.632767 | 157.2 |
| lunar | corner2 | 3/5 | -0.568958 | 286.8 |
| lunar | corner3 | 4/5 | -0.274635 | 207.0 |
| mine | default | 5/5 | 0.467452 | 17.0 |
| mine | uniform | 5/5 | 0.125936 | 19.0 |
| mine | corner0 | 0/5 | 0.000000 | 1000.0 |
| mine | corner1 | 0/5 | 0.000000 | 1000.0 |
| mine | corner2 | 0/5 | -0.239371 | 10.0 |

Lunar corners0/1/2/3 select landing/shaping/main-fuel/side-fuel respectively;
Minecart corners0/1/2 select ore1/ore2/fuel. Native task success means pad-x
landing for Lunar and ore delivery for Minecart, not optimal weighted utility.

Lunar default produced native+100 in all5 but only4 inside the pad: the stricter
criterion matters. Shaping-only often fails the landing criterion despite
positive shaping utility. Pure-ore Minecart profiles hit the1000-step cap with
zero ore. Their zero weighted utility hides substantial negative fuel returns
because fuel has zero weight. Fuel-only returned no ore but mean raw fuel-.3
in10 steps; no delivery alone cannot establish failure of that fuel preference.
No uniqueness/optimality or single-cause diagnosis follows from these cases.

These observations qualify the earlier10/10 bounded-case result, rather than
contradicting its recorded cases. They rule out a universal-preference-success
claim. Training candidate and prospective two-seed confirmation remain fixed;
no tuning follows this diagnostic. Per-seed confirmation outcomes remain pending.

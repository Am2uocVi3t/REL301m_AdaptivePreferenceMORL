---
experiment_id: pilot-protocol-freeze
plan: configs/pilots/calibration_v2.json
status: complete
claim_ids: []
---

# Pilot-only reward-scale and hypervolume-reference calibration

## Falsifiable question

Can a predeclared uniform-policy pilot provide finite, stable per-objective magnitude estimates and a hypervolume reference point strictly dominated by every observed scaled pilot return for both course environments?

## Methods and data firewall

- Uniform-PCQN only; adaptive and random curricula are excluded from calibration.
- Identity reward scales during pilot collection.
- Immutable validation preferences and nominal dynamics only.
- Final-test artifacts are rejected by the calibrator.
- Smoke runs validate integration but are permanently ineligible for freezing values.

## Frozen budgets and seeds

- Environments: `mo-lunar-lander-v3`, `minecart-v0`.
- Training seeds: `20261021`, `20261022`, `20261023`.
- Training interactions: 100,000 per environment and seed; 600,000 total.
- Gradient schedule: learning starts at 5,000, update every 4 interactions, batch size 64.
- Calibration evaluation: 5 episodes for each of 32 validation preferences, or 160 episodes per job and 960 total.
- Curriculum diagnostics and intermediate validation are disabled for this scale-only pilot.

## Calibration rule

Use discounted `episode_returns`. The proposed reward scale is the inverse 95th percentile absolute return per objective. In scaled coordinates, the proposed hypervolume reference point is the coordinatewise observed minimum minus `max(0.05 × robust_span, 0.01)`, where `robust_span` is the 5th-to-95th percentile range.

## Artifact and provenance contract

The ignored execution directory contains the pilot manifest, six checkpoints, and six validation-evaluation JSON files with raw and discounted returns. The calibration proposal records hashes for the plan, manifest, protocols, and every source evaluation artifact. It does not mutate protocol files.

## Decision rule

Proceed to a reviewable freeze proposal only if all six jobs complete, all hashes and seeds match, all returns are finite, objective magnitudes exceed the floor, no test/shifted artifact is present, and each proposed reference point is strictly dominated by every scaled pilot return. Otherwise revise the pilot plan without consulting final-test data.

## Executed v1 outcome — 2026-10-15

The six jobs completed under Python 3.11.17 with the predeclared 600,000 training interactions and 960 validation episodes. Every checkpoint records 100,000 training interactions, 23,751 gradient updates, zero curriculum-evaluation interactions, and zero in-training validation interactions. The execution used only the validation split under nominal dynamics.

The ignored raw manifest is `artifacts/pilot-calibration-v1/pilot_manifest.json` (SHA-256 `17e7ab4ea734130ef42aeef163662133ae09b542a997a1825c775ff8e17d4bdb`). Source evaluation hashes are:

- Minecart seeds `20261021`, `20261022`, and `20261023`: `344a58ef088b7ddcf982577177a9074df958eb0204e8c47fb797493319dc261a`, `e1ada7ec903e8d83c0c7aa00f7777c79d238f3edae328f5d40760ab18da9a270`, and `22bdf1f05d4ce255ae6b2d942a0fa829900dc919f6523611ad0a38a669438592`.
- MO-Lunar-Lander seeds `20261021`, `20261022`, and `20261023`: `9b146e2f16c14549d2257b470a64feac2811df7b7803cc1ba5cdcd1a21c9e444`, `2d5b246325932e5cfd5ed193bc21aba4478462960526f663018f4b132d20b915`, and `5f9216d5d01a0da7cd952f7d4f07cb2e89cc7253a98bc87c5c6772f8ebe41521`.

MO-Lunar-Lander produced 480 finite samples with non-degenerate magnitudes in all four objectives. Its provisional scale proposal was `[0.0190260017, 0.0110089049, 0.0162116762, 0.0251301322]`, but it is not frozen because the complete two-environment gate failed.

Minecart produced 480 finite samples, but all 480 returns were exactly zero in ore objectives 0 and 1. The calibrator therefore failed as designed with `Objectives [0, 1] lack enough magnitude for stable scaling`; it wrote no proposal and mutated no protocol.

Post-run control auditing found that `uniform-pcqn` sampled fresh continuous Dirichlet preferences instead of sampling uniformly from the protocol-seeded finite candidate pool shared with adaptive methods. Regression tests now enforce fixed-pool uniform rollout sampling. A separate 100,000-interaction fixed-pool diagnostic retained nonzero ore returns in its training archive (`max=[0.9046933, 0.5208790, -0.4167641]`) but still produced zero ore reward in all 160 final validation episodes. Its ignored evaluation artifact has SHA-256 `a13411678f0d8f2d3fa4421b8cb0870abcb28523eee856a20dca18253836acee`.

Therefore v1 is a documented failed calibration, not freeze evidence. A revised source/budget rule for sparse Minecart rewards must be predeclared and independently executed before either protocol is frozen. No final-test data was accessed.

## Executed v2 outcome — 2026-10-15

ADR-003 replaced the learner-dependent one-source rule with a source-aware rule declared before execution: use authoritative deterministic environment geometry when available and otherwise use an independent validation-only fixed-pool pilot. Minecart's `pareto_front(gamma=0.99, symmetric=true)` produced the same 20 sorted points across three declared seeds under `mo-gymnasium==1.3.2` and the pinned environment-config hash. MO-Lunar-Lander has no equivalent interface, so three new seeds (`20261103`–`20261105`) supplied 300,000 training interactions and 480 validation episodes.

The v2 proposal passed all provenance, budget, finite-value, non-degeneracy, and strict-domination gates. It froze:

- MO-Lunar-Lander reward scale `[0.0179126034, 0.0109185159, 0.0163337195, 0.0324797828]` and reference `[-1.1573719430, -2.3275130420, -1.1397362012, -1.6736955656]`.
- Minecart reward scale `[0.9659120784, 0.9659120784, 0.8247459754]` and reference `[-0.0438900907, -0.0438900907, -1.0215943973]`.

The versioned evidence is `research/calibration/course_calibration_v2_freeze.json`; the proposal and Minecart front remain separate immutable inputs. Post-freeze 20-step training plus validation-evaluation smoke runs computed finite exact hypervolume for both protocols (LunarLander `0.2836022`, Minecart `0.0`). These smoke values prove plumbing only and are not comparative results. No final-test data was accessed.

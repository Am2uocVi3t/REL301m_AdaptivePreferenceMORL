# Verified Lunar PPO course delivery — 3 November 2026

The new release is `outputs/REL301m_Course_Project_20261103_LunarPPO`
and its ZIP. The earlier 3 November release is preserved unchanged.
The repository launcher prefers the new release, using the next free port
if the requested port is occupied. Current verified instance: localhost8766.

Lunar uses the audited final4M actor from the sole predeclared pilot seed20265311,
with default preference [.7,.1,.1,.1]. Minecart retains the final4M actor from
the lowest confirmation seed20264311. Both infer with argmax. Slider input
does not update parameters and does not guarantee competence at every weight.
Stale PCQN training provenance was replaced with the actual PPO study identity.

Verification used the ZIP extracted on D:, imported the package's own runtime,
and ran 40 real physics episodes:10 cases x2 profiles in each environment.
Every action and probability vector matched the direct CPU source actor;
raw and discounted/scaled return sums matched transition records. All40 task
cases succeeded; native rendering passed for both environments. These reuse
development cases, add diagnostic cost, and are not independent research
replication or final-test episodes. The exact step count and raw returns are
in `research/qualification/lunar_ppo_course_demo_20261103.json`.

Actual Edge headless checks passed desktop/mobile layout, both model identities,
matched reset, single-step, pending/live preference, native renderer without
extra physics steps and both PDF links. No JavaScript errors or mobile
horizontal overflow. The same checks passed via the repository launcher
on8766 while the old8765 instance remained untouched.

The group-template report has14 pages. The new Vietnamese guide has1 page;
both were text-checked and updated pages visually inspected. Old guides are
explicitly archived under `docs/historical-release` in the new package.
Manifest file hashes and every ZIP member were checked after extraction.
Fresh dependency installation was not repeated; the existing pinned Windows
Python3.11 CPU runtime was used. No training or original final-test access.

Code quality: Ruff format/check, mypy139 files,231 tests passed/4 skipped,
Bandit, compileall and Git whitespace checks passed. Main receipt:
`research/qualification/course_lunar_delivery_20261103.json`.

This completes the requested model/report packaging and execution check.
Lunar remains a single-seed specialist result; Minecart has3 training seeds.
Independent semantic review and lecturer rubric/deadline remain unconfirmed.
The original adaptive-allocation comparison and phase4 scientific locks are
unchanged. No new training/confirmation is automatically dispatched.

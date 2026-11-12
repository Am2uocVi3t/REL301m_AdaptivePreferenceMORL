# Repository preparation — 12 November 2026

This records the earlier repository-preparation stage. The user subsequently
confirmed and received the English demo and English PDF with editable source.
For current instructions use the [English delivery guide](course/ENGLISH_DELIVERY_20261112.md)
and [English documentation coverage](ENGLISH_DOCUMENTATION.md); pending-format
statements below describe the earlier stage only.

## Scope and survey

Prepare the repository link for the lecturer. Report format (slides or PDF),
content/timing and demo video remain backlog. Existing manuscript and
presentation assets are retained; no new report, PDF, deck or video is produced.

The initial checkout was `main` at `5197b7f`. Before editing, the standard-library
research harness passed `doctor`; `status` and `roadmap list` showed Phase 4
active with the original adaptive-allocation comparison unestablished. Reviewed
the bootstrap/memory, README, status, roadmap, architecture, dependency pins,
canonical asset paths, PPO result summaries and representative source/test paths.
Work continues on `codex/submission-repository-polish`.

The code has two learning paths: preference-conditioned vector Double DQN with
replay/curriculum, and categorical PPO with a PopArt vector critic (Lunar adds
GAE). Fixed protocols and environment wrappers feed training; validation saves
vector returns and provenance. A local Python HTTP server and Canvas frontend
load exported checkpoints for inference. The harness maintains research state.
There is no frontend compilation requirement for the demo.

The previous README mixed chronological recovery notes and obsolete demo
descriptions with current instructions. Root Windows launchers require ignored
runtime/package paths, so they cannot be presented as a fresh-clone quickstart.
Python 3.11 is the target; the inspected WSL environments only supplied 3.12.
The standalone Windows demo provides 3.11.18 and an inference stack. See
[reproduction boundaries](REPRODUCIBILITY.md) for exact distinctions.

## Classification and cleanup decision

| Category | Examples | Decision |
|---|---|---|
| Required source and specifications | `src/`, `scripts/`, `tests/`, `configs/`, dependency files | Retain; no algorithm/protocol changes |
| Reproducibility evidence | `research/evidence/`, qualification, calibration, claims, sessions | Retain, including failed studies and large JSON return tensors |
| Supporting material | `paper/`, existing course figures, proposal PDF, historical logs | Retain; provenance, manuscript dependencies or history have a known role |
| Existing user edits | Memory, `AGENTS.md`, handoff, presentation scripts/figures, untracked presentation sources and skills | Preserve; do not stage them with this cleanup |
| Local generated/runtime data | `artifacts/`, `outputs/`, checkpoints, caches, logs, environments | Already ignored; no physical deletion |
| Presentation ZIP | `docs/course/presentation/REL301m_Slide_Package.zip` | Add exact ignore rule; preserve local file |
| Potential secrets/personal settings | `.env.*`, private key files, local credentials | Add ignore rules; no real values placed in docs |
| Tool/build residue | `node_modules/`, `.cache/`, `.uv-cache/`, temporary/backups, LaTeX intermediates | Add ignore rules |

**No file or directory is deleted or moved.** Replacing the README removes stale
front-page prose; its previous version remains in Git history, while detailed
research/recovery documents remain available. Do not prune `.agents/` or archived
research simply because they are not part of the inference path: existing
workflows and source-bound records refer to them.

The initial tracked inventory contained no checkpoint, ZIP, `.env`, private-key
filename, bytecode or LaTeX-log candidates in the checked filename patterns.
A text scan for common GitHub/API tokens and private-key headers found no
candidates in tracked UTF-8 files up to 3 MB. This is a bounded pattern scan,
not a comprehensive secret-history audit. Do not print credential values during
follow-up checks. Public author names come from existing course material;
machine-specific runtime paths are confined to operational documentation.

## Changes

- Replace the root README with a Vietnamese project overview, evidence-bounded
  result table, architecture image, installation/check/run/demo guidance,
  directory map, team information, limitations and explicit backlog.
- Add a deterministic source-flow SVG; it depicts implemented components,
  not fabricated learning outcomes or a screenshot of unexecuted behavior.
- Add runtime/reproduction guidance distinguishing clone, local artifact store
  and historical packages.
- Link the hand-in overview from the documentation/course hubs and clarify
  that existing presentation/report sources do not confirm a final format.
- Extend ignore rules without hiding editable slide sources or the existing PPTX.
- Format two previously unedited packaging/rendering scripts with Ruff; AST
  comparison against HEAD confirms the programs are identical. This repairs
  preexisting long lines left by the earlier directory reorganization.

Suggested GitHub repository description:

> REL301m course project: preference-conditioned MORL on Minecart and LunarLander, with PCQN/PPO, audited experiment evidence, tests, and an interactive inference demo.

## Validation and remaining work

Validation receipts are recorded below when commands finish. No new training,
final-test access, paid review, report export or demo-video recording is authorized
by this preparation. Fresh Linux dependency reconstruction and public pretrained
artifact distribution must not be claimed as verified without executing them.

Verification used the existing Windows Python 3.11.18 interpreter with QA tools
and their dependencies installed in an isolated external target directory,
`C:/REL301m_Demo/.runtime/submission-qa`, selected through `PYTHONPATH`. Existing
demo site-packages were not replaced. QA logs are under that runtime's `tmp/`
directory. This does not certify a clean full research dependency installation.

| Check | Result |
|---|---|
| Harness `doctor`, `status`, `roadmap list` | Passed; Phase 4/scientific gates unchanged |
| `python -m pytest -q -ra` | 233 passed, 4 skipped; 3 Unix-only ARIS modules and 1 absent historical-checkpoint integration |
| `python -m mypy src scripts` | Passed, 145 source files; cache placed on local Windows disk |
| `python -m bandit -q -r src scripts -ll` | Exit 0; comments produced non-finding parser warnings |
| `python -m compileall -q src scripts tests` | Exit 0 |
| Ruff on all 185 tracked Python files in `src`, `scripts`, `tests`, `monitor` | Format and lint passed |
| Actual local PPO demo over HTTP | Both checkpoint hashes, homepage/config, reset, tick and native frames passed; 8 total presentation steps, zero training/final-test; server stopped |
| Changed-document relative links | 38 checked, no missing targets |
| Architecture SVG | XML parsed successfully |
| New ignore rules | No already-tracked file matches; local presentation ZIP stays on disk |
| Existing user edits | Hash comparison against the pre-edit snapshot found no changes |

Whole-worktree Ruff initially reported 77 errors: 75 in the user's untracked
presentation scripts and 2 preexisting long lines in tracked scripts. Only the
2 tracked errors were fixed. Whole-worktree formatting/whitespace checks still
include preexisting user work, which is outside this commit; do not describe
those broad checks as passing. The submission's tracked-source checks are
recorded separately. No user script or slide edit is included in the commit.

The GitHub account has WRITE permission but not ADMIN/MAINTAIN. Updating the
repository description returned HTTP 404 from the settings endpoint; the
suggested description above is ready for the owner to apply. This does not
prevent pushing a documentation branch or opening a review PR.

Session state/log were refreshed with `research_harness.py session close`.
The canonical handoff already had user edits, so a newly generated handoff is
saved under ignored `artifacts/repository-preparation/HANDOFF_20261112.md`
instead of overwriting their file. Claims, experiment registry and scientific
phase are unchanged.

## GitHub handoff

Prepared branch: [codex/submission-repository-polish](https://github.com/Am2uocVi3t/REL301m_AdaptivePreferenceMORL/tree/codex/submission-repository-polish).
Review PR: [#9](https://github.com/Am2uocVi3t/REL301m_AdaptivePreferenceMORL/pull/9).
GitHub reports `MERGEABLE` but `BLOCKED` / `REVIEW_REQUIRED` on the protected
default branch. An authorized reviewer must approve and merge before the root
repository URL shows this README. No protection bypass or self-approval was used.
The owner must also apply the proposed repository description in settings.

Backlog: confirm report format (slide or PDF), content and timing; video demo
only on request; confirm if the lecturer also requires a pretrained demo package.

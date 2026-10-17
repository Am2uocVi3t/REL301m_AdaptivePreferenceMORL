# Agent Bootstrap

This file is the canonical entry point for any coding or research agent working in this repository.

## Session start

Before changing files:

1. Run `python scripts/research_harness.py doctor`, `python scripts/research_harness.py status`, and `python scripts/research_harness.py roadmap list`.
2. Read `.agents/memory/MEMORY.md`.
3. Read `docs/research/PROJECT_STATUS.md` and `docs/research/ROADMAP.md` for the latest verified state, phase gate, and open blockers.
4. Read `README.md` for supported commands and repository layout.
5. If changing the research question, protocol, metrics, or claims, also read:
   - `docs/proposal/REL301m_Research_Project_Proposal_MORL_V2.md`;
   - `docs/ARCHITECTURE.md`;
   - the relevant JSON file in `configs/protocols/`.

Do not treat the original submitted PDF as the current executable specification. It is an immutable historical record.

For a new chat, use the complete code block in `docs/research/HANDOFF_PROMPT.md`. Re-check its generated Git snapshot against the live worktree before relying on it.

## ARIS project integration

Before invoking installed ARIS workflows, read `docs/research/ARIS_INTEGRATION.md`
and `configs/aris/project.json`. ARIS skills are copied from pinned upstream with
Claude-review overlays; they do not override this file or frozen protocols.
Resolve helpers from the pinned upstream path in the project config. Run
`scripts/aris_preflight.py` with a fresh quota snapshot before dispatch.
The user's 2026-10-17 authorization permits the versioned Minecart F1 scope and
protocol amendment, implementation, local training, nominal-validation audit,
Git commit/push and a new review PR. It does not waive the scientific firewall:
checkpoint locking and final-test access remain conditional on the frozen F1
all-seeds retention gate plus source audit. Paid review requires a separately
defined bounded batch within the existing cost limits, and unattended/scheduled
dispatch remains disabled until its documented lifecycle and confinement gates
are verified. Never restart completed research to populate ARIS state.

## Sources of truth (precedence)

Use this precedence when sources disagree:

1. Executed tests and versioned result artifacts.
2. Code and protocol/config files.
3. Machine-readable registries under `research/`, especially `research/roadmap.json`, plus `docs/research/PROJECT_STATUS.md` and `docs/ARCHITECTURE.md`.
4. Editable proposal v2.
5. Other Markdown documents.
6. Original submitted proposal PDF.

## Scientific guardrails

- Never describe a planned or smoke-tested result as experimentally supported.
- For literature tasks, search primary sources and register the evidence without waiting for the user to enumerate papers.
- Never infer a completed reading from metadata or an abstract. If full text remains inaccessible after checking legal alternatives, mark the paper `screened` and `full_text_required`, report the access blocker, and ask the user for an uploaded PDF or authorized link.
- Do not bypass paywalls, CAPTCHAs, authentication, or redistribution restrictions; never commit paper PDFs.
- Never tune normalization, reference points, checkpoints, or hyperparameters on the final test split.
- Keep training, update, curriculum-evaluation, and final-evaluation budgets separate.
- Compare adaptive allocation with uniform and compute-matched random controls using paired seeds.
- Treat preference generalization and environment/dynamics generalization as separate claims.
- Preserve raw and discounted vector returns plus provenance for every reported result.
- The committed protocol currently leaves hypervolume reference points unset until pilot-only calibration.

## Engineering guardrails

- Target Python 3.11; use the pinned dependencies in `requirements.txt`.
- Create a dedicated branch for major changes and preserve unrelated user modifications.
- Keep generated checkpoints, logs, caches, and experiment outputs out of Git.
- After code/config changes, run:

```bash
ruff format --check .
ruff check .
mypy src scripts
pytest -q
bandit -q -r src scripts -ll
python -m compileall -q src scripts tests
git diff --check
```

- Update `docs/research/PROJECT_STATUS.md` only with evidence from the current working tree.
- Keep `research/claims.json`, the experiment registry, session log, and generated handoff synchronized through `scripts/research_harness.py`.
- Treat roadmap completion as an evidence claim: exactly one phase is active, completed phases name existing evidence, and transitions obey `research/roadmap.json`.
- Close substantial sessions with an evidence-bounded summary and regenerate the handoff prompt.

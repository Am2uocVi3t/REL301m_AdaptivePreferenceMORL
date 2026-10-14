# Agent Bootstrap

This file is the canonical entry point for any coding or research agent working in this repository.

## Session start

Before changing files:

1. Run `python scripts/research_harness.py doctor` and `python scripts/research_harness.py status`.
2. Read `.agents/memory/MEMORY.md`.
3. Read `docs/research/PROJECT_STATUS.md` for the latest verified state and open blockers.
4. Read `README.md` for supported commands and repository layout.
5. If changing the research question, protocol, metrics, or claims, also read:
   - `docs/proposal/REL301m_Research_Project_Proposal_MORL_V2.md`;
   - `docs/ARCHITECTURE.md`;
   - the relevant JSON file in `configs/protocols/`.

Do not treat the original submitted PDF as the current executable specification. It is an immutable historical record.

For a new chat, use the complete code block in `docs/research/HANDOFF_PROMPT.md`. Re-check its generated Git snapshot against the live worktree before relying on it.

## Sources of truth

Use this precedence when sources disagree:

1. Executed tests and versioned result artifacts.
2. Code and protocol/config files.
3. Machine-readable registries under `research/`, `docs/research/PROJECT_STATUS.md`, and `docs/ARCHITECTURE.md`.
4. Editable proposal v2.
5. Other Markdown documents.
6. Original submitted proposal PDF.

## Scientific guardrails

- Never describe a planned or smoke-tested result as experimentally supported.
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
- Keep `research/claims.yaml`, the experiment registry, session log, and generated handoff synchronized through `scripts/research_harness.py`.
- Close substantial sessions with an evidence-bounded summary and regenerate the handoff prompt.

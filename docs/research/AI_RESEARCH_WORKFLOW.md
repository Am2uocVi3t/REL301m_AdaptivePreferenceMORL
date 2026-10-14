# AI-Assisted Research Workflow

This repository treats an AI chat as a temporary collaborator and Git as the durable research record. The harness keeps research state explicit across chats while preserving the distinction between implemented code, verified behavior, and experimental evidence.

## Start every chat

From the repository root:

```bash
python scripts/research_harness.py doctor
python scripts/research_harness.py status
git status --short --branch
```

Then read `AGENTS.md` and the documents it routes to. For a fresh chat, copy the entire code block in `docs/research/HANDOFF_PROMPT.md` and append the new request. The generated Git snapshot is a warning against stale context, not a replacement for the live `git status` check.

## Research loop

```text
question or claim
  -> primary-source literature search
  -> structured paper notes and antecedent mapping
  -> falsifiable experiment card
  -> frozen protocol and budget
  -> implementation plus invariant tests
  -> pilot-only calibration
  -> paired experiment execution
  -> raw artifacts and provenance
  -> claim-status update
  -> session close and regenerated handoff
```

### 1. Frame a falsifiable claim

Create or refine an entry in `research/claims.json`. Keep these states distinct:

- `hypothesis`: a research proposition with no implementation implication;
- `implemented`: the mechanism exists in the executable path;
- `validated`: targeted tests or diagnostics support the stated mechanism;
- `experimentally_supported`: a frozen protocol and versioned empirical artifact support the claim;
- `rejected`: evidence contradicts the claim or it is intentionally abandoned.

The current CLI changes existing claim status and evidence:

```bash
python scripts/research_harness.py claim list
python scripts/research_harness.py claim set-status CLAIM_ID validated \
  --evidence tests/test_algorithm.py
```

Do not promote a claim to `experimentally_supported` merely because code compiles, a smoke test passes, or a curve looks promising. That state requires at least one existing, versioned artifact reference such as `--evidence artifact:research/artifacts/study-manifest.json`.

### 2. Search and read literature

Use `research/literature/search-queries.json` as a seed, not proof of a systematic search. Record exact queries, sources, dates, inclusion/exclusion criteria, citation chasing, and limitations in `research/literature/SEARCH_LOG.md`. Prefer proceedings, OpenReview, PMLR, publisher/arXiv records, official benchmark pages, and official code.

Register each included work before interpreting novelty:

```bash
python scripts/research_harness.py paper add \
  --id author2026shortname \
  --title "Exact paper title" \
  --year 2026 \
  --author "First Author" \
  --author "Second Author" \
  --url "https://primary-source.example/paper" \
  --source-type peer-reviewed \
  --venue "Venue 2026" \
  --tag adaptive-allocation
```

This writes metadata, a BibTeX entry, and a structured note template. Complete the note before setting `read`:

```bash
python scripts/research_harness.py paper set-status author2026shortname read
```

Do not commit downloaded PDFs. A paper title match is not a novelty analysis: compare the mechanism, sampling signal, training path, evaluation setting, and falsifiable consequence.

### 3. Pre-register an experiment

Freeze the protocol before expensive or final runs. Register which claims it can distinguish:

```bash
python scripts/research_harness.py experiment add \
  --id course-gap-only-seeds \
  --title "Gap-only paired-seed course experiment" \
  --protocol configs/protocols/course_mo_lunar_lander_v3.json \
  --claim conditioning-gap-allocation
```

Use `research/experiments/templates/experiment-card.md` when the registry's compact record is insufficient. Record controls, allocation target, seeds, all four budgets, metrics, statistical tests, decision rule, and artifact contract before execution.

Status changes must describe reality:

```bash
python scripts/research_harness.py experiment set-status course-gap-only-seeds running
python scripts/research_harness.py experiment set-status course-gap-only-seeds complete \
  --artifact results/immutable-manifest.json
```

The final-test split remains locked until checkpoint, hyperparameters, normalization, and reference points are selected from training/pilot/validation evidence.

### 4. Implement and verify

Follow `AGENTS.md` and `docs/ARCHITECTURE.md`. Tests should cover scientific invariants and integration paths, while experiment artifacts support empirical claims. Neither substitutes for the other. After changing code or structured research state, run the doctor and repository validation suite.

### 5. Report progress

Use fact, inference, and recommendation explicitly:

- Fact: direct code, test, artifact, or primary-source evidence.
- Inference: a reasoned interpretation that could still be wrong.
- Recommendation: the next decision or experiment.

Update `docs/research/PROJECT_STATUS.md` only from current evidence. Keep `research/state.yaml` concise and operational; do not duplicate a full narrative there.

## End every substantial chat

Close the session with an evidence-bounded summary and concrete next actions:

```bash
python scripts/research_harness.py session close \
  --summary "Implemented X; tests Y passed; no empirical performance claim was made." \
  --next "Review the frozen pilot manifest." \
  --next "Run paired seeds after approval." \
  --blocker "Reference point is not frozen." \
  --write-handoff
```

Then run:

```bash
python scripts/research_harness.py doctor
git diff --check
```

Commit the synchronized code, registries, documentation, and handoff together. The session log is append-only; correct a bad entry with a later entry instead of rewriting history.

## What the harness does not do

It does not schedule autonomous agents, download or redistribute papers, infer evidence from prose, launch expensive experiments without review, or guarantee publication novelty. It makes the evidence chain inspectable so a human or a later chat can continue without relying on conversational memory.

# Read-only research alignment and novelty audit

This is a reusable English review procedure, not a current result or permission
to run new research. Start with [AGENTS.md](../../AGENTS.md) and
[the current status](../research/PROJECT_STATUS.md). The earlier Vietnamese
audit prompt is retained as an original working document.

## Review questions

1. Do the current claims and documents accurately describe executable code,
   fixed protocols and completed experiments?
2. What prior work already covers the proposed mechanisms, and what narrowly
   defensible novelty remains unresolved?
3. What missing implementation or evidence blocks each intended claim?

Work read-only unless the user separately authorizes changes or a saved report.
Do not start training, access a locked test split, modify a protocol, purchase
review services or change a scientific gate as part of this audit.

## Evidence and scope

Use the source precedence in the root bootstrap: executed tests/versioned
results, code/protocols, registries/current status, editable proposal, other
Markdown, then the immutable original proposal PDF. The original PDF records
historical intent; it is not the current executable specification.

Inspect relevant source paths and callers, dependencies, protocols, tests and
raw-result artifacts. Do not infer implementation from filenames or a completed
experiment from a checklist. Respect missing checkpoints and distinguish
source/numeric checks from independent semantic acceptance.

## Traceability

Create a requirement/claim matrix with document location, source/config/test
evidence (`path:line`), actual semantics, severity and a minimal proposed action.
Use explicit statuses:

- `ALIGNED_AND_IMPLEMENTED`
- `ALIGNED_BUT_PARTIAL`
- `DOCUMENTED_ONLY`
- `IMPLEMENTED_BUT_UNDOCUMENTED`
- `SEMANTIC_MISMATCH`
- `CONTRADICTS_PROPOSAL`
- `STALE_OR_BROKEN`
- `NO_EVIDENCE`

Separate planned, implemented, validated and experimentally supported work.
Check current links, CLI arguments, environment IDs, tensor contracts, units,
normalization, reference points, provenance and artifact availability.

## Scientific checks

- Separate preference conditioning, deployment-time preference changes,
  adaptive training allocation, human preference elicitation, task curricula
  and dynamics generalization.
- Verify per-head targets, shared-trunk/mask semantics and replay end flags.
- Trace whether each sampler changes rollout preferences, update preferences
  or both, and whether uniform/random controls share the intended budgets.
- Confirm that gap uses measured current returns and that disagreement is not
  described as calibrated epistemic uncertainty without calibration evidence.
- Inspect raw and discounted/scaled vectors, fixed preference manifests,
  deterministic metrics and pilot-only calibration. Never tune on final test.
- Check declared dynamics interventions by their actual construction and
  behavior, not post-initialization attribute assignment alone.
- Keep training seeds distinct from episode cases and sampled/argmax modes.
  Check uncertainty, exact-test resolution and any multiplicity/effect-size
  claims against the actual sample size.
- Preserve failed qualification and missing artifacts. A larger budget or a
  different backbone is not automatically a controlled treatment comparison.

## Novelty and literature

For an explicitly requested novelty review, search current primary sources by
mechanism, research problem, sampling signal, protocol and evaluation setting.
A missing exact phrase is not novelty evidence. Identify peer-reviewed work,
preprints, software and venue policies separately, with direct source links.

Use verdicts `not novel`, `incremental`, `potentially novel` or
`novelty unresolved`, with confidence and a falsifier. Do not claim full-text
reading from metadata/abstracts. Inaccessible full text stays screened with an
explicit access blocker; follow the repository's legal-access rules.

Do not imply that cited alternatives were implemented baselines. Publication
or venue recommendations need current verified policies and deadlines, and no
acceptance guarantee. A research review does not authorize a submission.

## English output

Provide an executive verdict, traceability matrix, actionable document/code
findings, a prior-work comparison and a prioritized evidence roadmap. State the
five strongest blockers, exact verification commands and any unexecuted checks.
Link each important claim to its supporting source or retained artifact.
Separate engineering readiness, scientific support and external academic
acceptance. Recommend only changes justified by the observed evidence.

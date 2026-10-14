# Cross-Chat Research Handoff

Copy the complete prompt below into a new chat.

```text
You are continuing the REL301m Adaptive Preference MORL research project.

Before acting:
1. Read `AGENTS.md`, `.agents/memory/MEMORY.md`, and `docs/research/PROJECT_STATUS.md`.
2. Run `python scripts/research_harness.py doctor` and `python scripts/research_harness.py status`.
3. Run `git status --short --branch`; do not overwrite unrelated changes.
4. Read the relevant protocol/config/code directly before making scientific claims.

Snapshot generated: 2026-10-14T19:38:50+00:00
Expected working branch at generation: feature/ai-research-harness
Expected commit at generation: 96c9f4d
Working tree dirty at generation: yes
Current phase: course pilot preparation
Publication state: no multi-seed empirical claim established

Research question:
Under matched interaction, update, evaluation, and tuning budgets, which signal—conditioning gap, masked-ensemble disagreement, local coverage and recency, or observed learning progress—best predicts and improves future performance in weak preference regions?

Source precedence:
1. Executed tests and versioned raw-result artifacts.
2. Code and protocol/config files.
3. Machine-readable registries under `research/`, `docs/research/PROJECT_STATUS.md`, and `docs/ARCHITECTURE.md`.
4. Editable proposal v2.
5. Other Markdown documents.
6. Original submitted proposal PDF (historical only).

Active claims:
- conditioning-gap-allocation [implemented]: Empirical conditioning gap identifies weak preference regions
- disagreement-allocation [implemented]: Masked-ensemble disagreement identifies useful allocation regions
- coverage-recency-allocation [implemented]: Local coverage and recency improve preference allocation
- learning-progress-allocation [hypothesis]: Observed learning progress is a better allocation target than difficulty or uncertainty
- combined-allocation [hypothesis]: Combining gap, disagreement, coverage/recency, and progress improves sample efficiency
- environment-shift-robustness [hypothesis]: Adaptive preference allocation affects robustness under dynamics shift

Literature queue:
- No papers registered yet. Add primary sources before making novelty claims.

Full-text requests for the user:
- None currently registered.

Active experiments:
- pilot-protocol-freeze [planned]: Pilot-only reward-scale and hypervolume-reference calibration
- course-paired-matrix [blocked]: Paired-seed controls and allocation-signal ablations

Open blockers:
- Freeze reward scaling and dominated hypervolume reference points from pilot-only evidence.
- Validate GPI-LS under Python 3.11 with native cddlib headers.
- Behaviorally validate that every enabled dynamics shift changes the intended transitions.
- Run paired controls, signal ablations, and compatible close baselines after freezing the protocol.

Latest closed-session summary:
Added an explicit automation contract and full-text access policy: literature agents search legal primary sources autonomously, abstract-only papers stay screened, read requires verified full text plus a completed note, and inaccessible papers are surfaced to the user in the handoff. Full suite: 35 passed.

Next actions:
1. Review and merge PR #5 after the full-text policy update.
2. Formalize the course-to-publication phase gates in a versioned roadmap.
3. Populate the literature registry with the nearest primary-source antecedents and map them to claim IDs.

Non-negotiable scientific guardrails:
- Do not label a claim `experimentally_supported` without a versioned raw-result artifact.
- Do not use final-test data for tuning, normalization, reference points, or checkpoint selection.
- Separate preference generalization from environment/dynamics generalization.
- Match interaction, update, diagnostic-evaluation, final-evaluation, and tuning budgets.
- Literature: use primary sources; log queries; register metadata/BibTeX; complete notes; never commit PDFs.
- Search legal full-text alternatives autonomously. If access still fails, keep the paper `screened`, record
  `full_text_required`, state what was tried, and ask the user for an uploaded PDF or authorized link.
- Never make a strong novelty or mechanism claim from metadata or an abstract alone.
- End substantial sessions with `python scripts/research_harness.py session close ... --write-handoff`.

User request for this new session:
[PASTE THE NEW REQUEST HERE]
```

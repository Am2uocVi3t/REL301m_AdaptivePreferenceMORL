# Progress report evidence index — 17 October 2026

Paths below are relative to the research repository root. No large raw artifact or paper PDF is copied into the report folder.

| Report statement | Evidence |
| --- | --- |
| Research question and limited novelty | `docs/proposal/REL301m_Research_Project_Proposal_MORL_V2.md`, `research/claims.json`, `docs/research/LITERATURE_MAP.md` |
| 22 full-text readings | `research/literature/index.json` and corresponding structured notes |
| Masked-head Double-DQN, replay, allocation modes | `docs/ARCHITECTURE.md`, `src/`, scientific invariant tests |
| Last recorded 103-test implementation gate | `research/qualification/minecart_pcqn_backbone_v2_implementation.json`; the report does not imply every test was rerun during training |
| Frozen pilot calibration | `research/calibration/course_calibration_v2_freeze.json` |
| 30 primary jobs, 300 checkpoints, blocked lock | `research/evidence/course_primary_execution_audit_v1.json`, `research/evidence/course_primary_validation_v1.json`, `research/evidence/course_primary_checkpoint_lock_v1.json` |
| 14,400 Minecart episodes, 13,308 time limits, 345,417 probed actions | `research/evidence/minecart_validation_diagnosis_v1.json` |
| V1 selected 0/160, 0/160, 28/160 per ore objective | `research/qualification/minecart_pcqn_backbone_v1.json` |
| Seven checkpoints / 1,120 behavior episodes | `research/evidence/minecart_pcqn_backbone_v1_behavior_diagnosis.json` |
| V2 single-factor PER and unchanged Huber | `configs/remediations/minecart_pcqn_backbone_v2.json`, pre-execution amendment and implementation qualification |
| V2 three complete runs and 30-checkpoint source pass | `artifacts/minecart-pcqn-remediation-v2/execution_status.json`, `research/evidence/minecart_pcqn_backbone_v2_source_audit.json` |
| V2 selected 0/160 both ores, all three seeds failed; 4,800 episodes / 4,710,905 eval steps | `research/qualification/minecart_pcqn_backbone_v2.json` and linked raw validation evidence |
| Native-sprite nominal-validation replay demo (presentation only) | `visual-policy-demo.md`, `scripts/render_policy_demo.py`, `demo/visual/index.html`, `research/qualification/visual_policy_demo_v1.json`; full hashed traces retained under `outputs/visual-demo/`, no training or final-test access |
| Completed one-batch Claude review and limits | `research/qualification/aris_single_batch_result_v1.json`, `research/reviews/aris_batch_20261017.md` |
| Current 168-test tooling gate; separate from original 103-test backbone gate | `research/qualification/aris_single_batch_offline_v1.json` |

## Execution provenance

- Training commit: `25328e8e0a8448e1f929251afc3a55c7b8a56978`.
- Frozen v2 plan SHA256: `c28b0de87731d79af71ee5ee1c5fbbd4eab0e027b72ae3df7908fa170b1873ec`.
- V2 source audit SHA256 recorded by qualification: `223f53a88e1936548c18510a5323e5f86feac7f5b45cf59fc765a0865a34b809`.
- Completed v2 counters are 1,000,000 training interactions and 995,001 updates per seed; the separately preserved first interrupted attempt of seed20264011 is extra expenditure.
- Qualification evidence role: `backbone_qualification_only_not_course_comparison`; final-test and matrix unlock flags are false.

## Visual and bibliography provenance

- `Figures/morl-pipeline.tex`: conceptual rendering of implemented contracts in `docs/ARCHITECTURE.md`; not a measured improvement claim.
- `Figures/research-timeline.tex`: the completed-work ledger and qualification artifacts above; arrows indicate research progression, not successful phase promotion.
- `Figures/qualification-results.tex`: ore-positive counts from the v1/v2 `seed_decisions`; both ore objectives have the same counts. Different seed batches prohibit paired causal interpretation.
- References use the canonical `research/literature/library.bib`; the related-work synthesis is grounded in the existing full-text notes. It does not imply local reproduction of those papers.
- FPT cover/logo/watermark assets are reused from the supplied template, not research-result images.

## Claim boundaries

The failed gate applies to the specified qualification, not all possible PER algorithms or all MORL settings.
Completed training, passed source checks, and nonzero hypervolume do not establish non-degenerate ore behavior or adaptive-allocation benefit.
The preliminary report does not satisfy the final course-analysis/phase-transition gate and does not authorize additional training.

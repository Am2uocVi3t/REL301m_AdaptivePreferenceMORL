# Tracker — preference transfer recovery

| Stage | State | Evidence / next gate |
|---|---|---|
| Frozen-model diagnosis | Complete | `research/evidence/policy_extraction_diagnosis_v1.json`; 3.720 episodes, zero training |
| P1 inference factorial | Complete; all gates fail | `research/evidence/preference_transfer_p1_v1.json`; 960 episodes /443,192 steps |
| P2 learning factorial | Complete, all task gates fail | `configs/experiments/preference_recovery_p2_v1.json`; 12/12 complete; research/evidence/preference_recovery_p2_v1.json; no passing arm |
| P3 independent confirmation | Conditional design | Select one method first; freeze full confirmation matrix |
| P4 adaptive comparison | Conditional design | Competent backbone + separately reviewed matched-budget protocol |

P2 đã hoàn tất:0/240 task deliveries; P3/P4 không được kích hoạt. Đề xuất on-policy mới có protocol riêng và execution disabled. Original matrix/F1/final-test
locks giữ nguyên. Không đổi planned thành evidence, không restart study cũ.

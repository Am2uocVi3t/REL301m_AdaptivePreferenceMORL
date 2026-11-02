# Tracker — preference transfer recovery

| Stage | State | Evidence / next gate |
|---|---|---|
| Frozen-model diagnosis | Complete | `research/evidence/policy_extraction_diagnosis_v1.json`; 3.720 episodes, zero training |
| P1 inference factorial | Complete; all gates fail | `research/evidence/preference_transfer_p1_v1.json`; 960 episodes /443,192 steps |
| P2 learning factorial | Running, qualified | `configs/experiments/preference_recovery_p2_v1.json`; initial95b5282; IO recovery3a159fe now9 complete/3 active, source-bound retry qualified; inspect live status |
| P3 independent confirmation | Conditional design | Select one method first; freeze full confirmation matrix |
| P4 adaptive comparison | Conditional design | Competent backbone + separately reviewed matched-budget protocol |

P2 đã được user cho phép và khởi chạy; chưa có kết quả task cuối của P2. Original matrix/F1/final-test
locks giữ nguyên. Không đổi planned thành evidence, không restart study cũ.

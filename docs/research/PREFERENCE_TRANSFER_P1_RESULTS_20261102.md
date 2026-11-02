# P1 — kết quả inference factorial, 02/11/2026

Hoàn tất 12 fixed-final checkpoint ×2 preference ×10 case ×4 policy:
**960 episode / 443.192 diagnostic steps, 0 training/update/final-test**.
Trace numeric/source audit qua; đây là audit của executor, không phải review
ngữ nghĩa độc lập. Evidence: `research/evidence/preference_transfer_p1_v1.json`.
Engineering qualification 20 episode /9.801 bước được tính riêng.

Các ô dưới đây là số task success trên 10 case, theo ba training seed cố định;
Minecart là giao quặng, Lunar là native +100 và nằm trong pad-x. Không pooling
case qua các model, không thay checkpoint hay chọn seed tốt nhất.

| Môi trường / n / preference | Mean greedy | Mean eps .05 | GPI greedy | GPI eps .05 |
|---|---|---|---|---|
| Minecart n1, `[.45,.45,.1]` | 0,0,0 | 0,0,0 | 0,0,0 | 0,1,0 |
| Minecart n1, `[.8,.1,.1]` | 0,0,0 | 0,0,0 | 0,0,0 | 5,2,0 |
| Minecart n20, `[.45,.45,.1]` | 0,0,0 | 8,0,0 | 0,0,0 | 1,0,1 |
| Minecart n20, `[.8,.1,.1]` | 0,0,0 | 3,1,0 | 0,0,0 | 8,0,7 |
| Lunar n1, landing-heavy | 4,0,5 | 3,0,6 | 7,2,0 | 6,3,1 |
| Lunar n20, landing-heavy | 0,0,1 | 0,0,0 | 4,4,6 | 6,6,5 |

GPI trên Lunar n20 có tín hiệu hữu ích: cả ba seed cải thiện pad success và
utility landing-heavy, paired utility mean tăng `.0315, .0333, .0621` với
greedy và `.0362, .0410, .0571` với epsilon so với mean greedy. Tuy nhiên,
không đạt gate 8/10 mọi seed; uniform preference cũng không có cải thiện ổn
định. Lunar n1 có một seed bị giảm mạnh từ GPI. Không gọi đây là giải pháp
chung hoặc bảo đảm transfer.

Minecart không có policy nào đạt cả hai task profile ở mọi seed. Một số seed
được cứu một phần bởi epsilon/GPI; cũng có utility giảm. Ví dụ n20 GPI+epsilon
ở `[.8,.1,.1]` đạt 8,0,7 deliveries nhưng utility delta so với mean là
`+.1520, −.8784, −.2114`: task count đơn lẻ chưa thể thay utility.

## Quyết định đã định trước

Tất cả gate P1 đều false. Điều kiện chuẩn bị P2 Minecart đã thỏa: tiến hành
study mới n=1 2×2 relabel/loss, không tăng ngân sách P1 hay tune source bank.
Đây không bác bỏ định lý GPI: critic head-mean chưa có approximate-value bound
và chưa được chứng minh là Q của chính mean-greedy source policy.

Giữ đầy đủ vector, episode trace, paired utility differences trong evidence;
không đưa checkpoint P1 vào demo như một model đã qualified. Original matrix,
F1, checkpoint-lock và final-test tiếp tục bị khóa. P2 execution contract:
`docs/research/PREFERENCE_TRANSFER_EXECUTION_V1.md`.

# Phân bổ preference trong Multi-Objective Reinforcement Learning

**REL301m - Báo cáo nghiên cứu và gói trình diễn, ngày 01/11/2026**

Báo cáo này trình bày implementation, bằng chứng validation đã giữ được và
kết quả qualification thất bại. Đây chưa phải xác nhận hoàn thành toàn bộ
protocol môn học: baseline/ablation còn thiếu, final test chưa được phép chạy,
và checkpoint cũ chưa phục hồi. Không tuyên bố phương pháp adaptive tốt hơn controls.

## 1. Bài toán và mục tiêu

Một tác tử MORL nhận vector reward có nhiều mục tiêu xung đột. Preference là
vector trọng số không âm, tổng bằng 1, biểu diễn mức ưu tiên giữa các mục tiêu.
Thay vì huấn luyện một policy độc lập cho từng preference, mô hình ở đây nhận
cả state và preference để chọn action.

Nghiên cứu hỏi liệu phân bổ thời gian học cho những vùng preference khó,
không chắc chắn, ít được thăm hoặc đang thay đổi có hữu ích hơn lấy mẫu uniform
hay không. Phạm vi nghiên cứu là đánh giá các tín hiệu phân bổ; không coi
preference conditioning hoặc adaptive weight selection là đóng góp mới tự thân.

### Cơ sở nghiên cứu và vị trí đóng góp

Double-DQN tách bước chọn action và đánh giá target để hạn chế overestimation [1].
Abels và cộng sự đã nghiên cứu multi-objective Q-network có điều kiện theo trọng
số và Diverse Experience Replay [2]. Envelope Q-learning là một hướng khác để
học representation phục vụ các linear preference [3]. Vì vậy dự án không tuyên
bố preference conditioning là mới; câu hỏi ở đây tập trung vào tín hiệu phân bổ
ngân sách giữa các preference. Những kết quả trong các paper đó không phải bằng
chứng phương pháp hiện tại có hiệu quả.

MO-Gymnasium mô tả LunarLander với bốn mục tiêu gồm kết quả hạ cánh, shaping và
hai chi phí động cơ [4]. Minecart có hai mục tiêu ore giao về base và một mục tiêu
fuel; ore reward là sparse [5]. Đây là lý do zero ore cần được xem riêng thay vì
chỉ đọc một metric tổng hợp.

## 2. Phương pháp đã triển khai

PCQN dự đoán vector Q bằng shared trunk và ba output head. Action được chọn
bằng scalarization theo preference. Khi cập nhật, mỗi head dùng Double-DQN:
online network chọn action tiếp theo và target network đánh giá vector Q của
action đó. True termination tắt bootstrap; time-limit truncation chỉ kết thúc rollout.

Replay lưu state, action, vector reward, next state, các cờ kết thúc, behavior
preference và bootstrap mask. Ba allocation mode phân biệt thay đổi phân phối
preference ở rollout, ở update hoặc cả hai.

Curriculum gồm empirical conditioning gap so với Pareto archive, disagreement
giữa các head, local coverage/recency và độ thay đổi tuyệt đối của utility giữa
hai lần đo. Tín hiệu được chuẩn hóa, trộn bằng softmax và có uniform floor.
Độ thay đổi tuyệt đối bao gồm cả tăng và giảm utility, nên không tự đồng nghĩa
với cải thiện hay learnability. Ensemble disagreement cũng chưa được calibration.

Các công thức và giới hạn chính thức nằm trong proposal v2 và
`docs/ARCHITECTURE.md`. Literature map gồm 22 structured full-text notes; việc
có notes không đồng nghĩa đã tái lập thực nghiệm của các công trình đó.

## 3. Thiết kế và dữ liệu còn giữ được

Khối primary đã thực hiện ba arm: Uniform-PCQN, compute-matched random-score
PCQN và full Adaptive-PCQN. Mỗi arm có năm paired training seed trên
`mo-lunar-lander-v3` và `minecart-v0`: tổng cộng 30 job, mỗi job 500.000
training interactions, lưu 10 checkpoint từ 50.000 đến 500.000 bước.

Mỗi checkpoint được nominal-validation trên 32 preference cố định và ba episode
mỗi preference. Aggregate versioned giữ vector return và episode length cho
300 checkpoint, tổng 28.800 episode và 18.304.760 evaluation environment steps.
Những bước này là chi phí đánh giá riêng, không gộp vào ngân sách training.
Các episode lặp qua checkpoint không phải training replicate độc lập; đơn vị
thực nghiệm là training seed.

18.304.760 bước chỉ là phần retained evaluation của 300 saved checkpoint,
không phải tổng chi phí đánh giá của study. Historical final counters ghi riêng
36.758.477 validation steps và 19.531.144 curriculum-evaluation steps trong
training. Các arm khớp training interactions, gradient-update budget và lịch
diagnostics; số environment steps thực tế khi đánh giá và wall-clock có thể khác
do episode length khác nhau. Tên matched-random không có nghĩa các chi phí đó
bằng nhau tuyệt đối.

Return chính dùng gamma 0,99 và reward scale cố định từ source-aware pilot
calibration v2. Trường `raw_episode_returns` ở đây là undiscounted **scaled**
return, không phải native environment units. Reference point và scaling không
được chọn từ final test. Dữ liệu ở đây hoàn toàn thuộc validation.

Sau sự cố mất laptop, đã tìm lại snapshot GitHub `e223362` ngày 18/10.
Người thực hiện nhớ có sửa code và chạy trên laptop đến 22/10, nhưng phần sau
18/10 chưa tìm được bản sao. Vì vậy bản báo cáo không suy đoán kết quả của
những lượt chạy hoặc phiên bản code chưa khôi phục.

## 4. Kiểm tra lại và kết quả mô tả

Lượt re-audit ngày 01/11 dùng protocol, frozen manifest và historical source-audit
để kiểm metadata, preference matrix, counters, shapes, finite values và tái tính
expected utility/hypervolume của cả 300 record. Kiểm tra này đã pass mà không
chạy thêm môi trường. Cả 300 file checkpoint được tham chiếu vẫn thiếu, nên
không coi đây là tái kiểm chứng file model hoặc tái lập rollout.

Bảng sau dùng **cố định checkpoint 500.000 bước**, mean ± sample standard
deviation trên năm training seed. Không dùng checkpoint lựa chọn sau khi xem
test, và không gọi các checkpoint này là đã khóa. Đây là diagnostics mô tả,
không phải kết luận comparative study đã đạt qualification.

| Môi trường | Arm | Protocol-scaled HV | Expected utility |
|---|---|---:|---:|
| LunarLander | Uniform | 4,0609 ± 0,3293 | −0,0758 ± 0,0311 |
| LunarLander | Matched-random | 4,6750 ± 0,4427 | −0,0227 ± 0,0684 |
| LunarLander | Full adaptive | 4,1764 ± 0,3228 | −0,0458 ± 0,0423 |
| Minecart | Uniform | 0,000253 ± 0,000565 | −0,6912 ± 0,1455 |
| Minecart | Matched-random | 0,000561 ± 0,000768 | −0,5857 ± 0,1577 |
| Minecart | Full adaptive | 0,000732 ± 0,000671 | −0,6302 ± 0,0443 |

Minecart không có ore return dương ở cả hai mục tiêu ore trên toàn bộ 14.400
episode validation của primary block. Hypervolume khác không không chứng minh
agent đã học được nhiệm vụ khai thác/giao ore. Study bị đánh dấu
`failed_degenerate`; checkpoint locking và phần matrix-v1 chưa chạy vẫn bị chặn.
Không dùng chênh lệch số học trong bảng để kết luận superiority hoặc equivalence.

Các remediation v1, PER-only v2 và F1 được giữ nguyên là các nghiên cứu qualification
riêng. Hồ sơ F1 ghi sáu paired job và 60 checkpoint: cả ba A1R1 seed đều không
biểu hiện positive ore, nên retention screen thất bại. Không trộn các seed hoặc
ngân sách đó vào bảng primary và không diễn giải thành chứng minh mọi replay
method đều thất bại. Raw F1 tensors và model files chưa được phục hồi như dữ
liệu primary nhúng trong aggregate; phần này dựa trên qualification/audit đã lưu.

![LunarLander: toàn bộ saved checkpoint, mean và sample SD trên năm training seed; validation-only, không phải confidence interval.](outputs/course-report/figures/lunar_validation.png)

![Minecart: cùng cách tổng hợp trên toàn bộ saved checkpoint. Chênh lệch metric không vượt qua được ore-degeneracy qualification.](outputs/course-report/figures/minecart_validation.png)

## 5. Trạng thái implementation và demo trên máy phục hồi

Python 3.11 đã được dựng riêng trên Windows. Cả hai môi trường đã reset/step
được và hoàn tất engineering witness gồm 200 training interactions, 43 gradient
updates, checkpoint an toàn và validation mới cho mỗi môi trường. Những lượt
chạy ngắn này chỉ xác nhận luồng tích hợp, không phải kết quả hội tụ hoặc so sánh.

Gói demo dùng hai model Uniform-PCQN **mới huấn luyện để thay thế model bị mất**,
mỗi môi trường một seed và đúng 100.000 training interactions.
Execution status ghi SHA256 của plan
`configs/demos/recovery_presentation_v1.json`. Mỗi job
có 23.751 gradient updates; không dùng curriculum/validation trong training,
không chọn best checkpoint, không thêm seed hoặc tăng ngân sách theo kết quả.
Chỉ final checkpoint được đóng gói. Không trộn các job này vào 30 job primary.

Provenance của run manifest được ghi lúc khởi tạo, còn checkpoint provenance
được ghi lúc lưu model. Dirty-state flags giữa hai mốc có thể khác nhau; chúng
được giữ nguyên trong gói, không coi là các snapshot đồng nhất hoặc chứng minh
một training tree sạch. Config hash của manifest chứa protocol object, còn
checkpoint config chứa protocol path; hai hash có phạm vi khác nhau.

Demo chạy inference thật với cùng checkpoint/seed ở hai panel; slider thay đổi
preference input, không thay trọng số network. Có pause/step, native renderer và
trace export với state/action/reward. Kết quả model thay thế không chứng minh
hội tụ, hạ cánh thành công hoặc khả năng giao ore. Phần validation nghiên cứu cũ
và model dùng để trình diễn là hai nguồn khác nhau, được gắn nhãn tách biệt.

Runtime còn thiếu `pycddlib==2.1.6`; do đó chưa xác nhận GPI-LS trên máy hiện tại.
Torch hiện là CPU wheel dù phần cứng có RTX 3050. Cách chạy và giới hạn Windows
được ghi trong `docs/WINDOWS_RECOVERY.md`.

## 6. Kết luận và phần việc còn lại

Kết quả đã giữ được cho thấy framework và contracts khoa học có implementation
cụ thể, đồng thời phát hiện failure của backbone trên Minecart trước khi cho
phép kết luận về adaptive allocation. Nghiên cứu hiện chưa trả lời đầy đủ tín
hiệu nào dự báo cải thiện tốt nhất, chưa có final-test comparison, và chưa hoàn
tất baseline/ablation theo proposal. Kết quả âm này có giá trị như failure analysis;
không nên thay bằng số liệu tự dựng hoặc tiếp tục tuning chỉ để có kết quả dương.

Gói báo cáo và demo phục vụ trình bày kết quả hiện có. Rubric và hạn nộp chính
thức vẫn cần xác nhận với giảng viên. Nếu cần mở rộng thực nghiệm, phải thống nhất
phạm vi của study mới thay vì sửa kết luận hoặc ngân sách sau khi xem kết quả. Các sửa lỗi phục hồi không tự mở lại
matrix-v1, F1/F2 hay final test. Chưa tự nhận toàn bộ yêu cầu môn học đã hoàn thành.

## 7. Nguồn bằng chứng và lệnh tái kiểm tra

- `research/evidence/course_primary_validation_v1.json`: vector returns nhúng của primary block.
- `research/evidence/course_primary_execution_audit_v1.json`: source metadata, counters và checkpoint identities.
- `configs/experiments/course_paired_matrix_v1.json` và hai protocol course: thiết kế và scaling cố định.
- `research/qualification/course_matrix_post_validation_gate_v1.json`: quyết định chặn study.
- `research/qualification/minecart_pcqn_replay_f1.json`: quyết định failed F1.
- `scripts/reaudit_recovered_validation.py`: tái tính metrics, không truy cập final test.

```powershell
. scripts/use_d_runtime.ps1
.venv/Scripts/python.exe scripts/reaudit_recovered_validation.py
.venv/Scripts/python.exe -m pytest -q
```

Chi tiết audit code trước sửa lỗi nằm ở `alignment-audit-20261101.md`; các
finding trong đó phải đọc cùng recovery update vì một số lỗi đã được sửa sau audit.

## 8. Tài liệu tham khảo chính

[1] H. van Hasselt, A. Guez, D. Silver. Deep Reinforcement Learning with Double
Q-learning. AAAI, 2016. https://arxiv.org/abs/1509.06461

[2] A. Abels, D. Roijers, T. Lenaerts, A. Nowé, D. Steckelmacher. Dynamic Weights
in Multi-Objective Deep Reinforcement Learning. ICML / PMLR 97:11-20, 2019.
https://proceedings.mlr.press/v97/abels19a.html

[3] R. Yang, X. Sun, K. Narasimhan. A Generalized Algorithm for Multi-Objective
Reinforcement Learning and Policy Adaptation. NeurIPS, 2019.
https://arxiv.org/abs/1908.08342

[4] Farama Foundation. MO-Gymnasium: MO-Lunar-Lander documentation.
https://mo-gymnasium.farama.org/environments/mo-lunar-lander/

[5] Farama Foundation. MO-Gymnasium: Minecart documentation.
https://mo-gymnasium.farama.org/environments/minecart/

Thông tin bibliographic và mô tả môi trường được đối chiếu với nguồn chính ngày
01/11/2026; API thực tế được kiểm trên package versions đã pin. Toàn bộ kết luận
thực nghiệm của báo cáo dựa trên artifact của dự án, không suy từ kết quả paper khác.

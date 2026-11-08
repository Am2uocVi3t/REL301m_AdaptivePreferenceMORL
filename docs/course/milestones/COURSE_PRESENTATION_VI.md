# Gợi ý báo cáo REL301m — dùng cùng PDF và demo

Đây là hướng dẫn trình bày kết quả thực có, không phải xác nhận đạt rubric của thầy.
PDF chính dùng mẫu LaTeX của nhóm ở `paper/REL301m`.

## Mạch trình bày khoảng 7 phút

1. **Bài toán (1 phút).** Có nhiều mục tiêu xung đột. Preference là vector
   trọng số không âm, tổng bằng 1. Một policy nhận cả state và preference;
   thay đổi ưu tiên của người dùng không cần huấn luyện lại mạng.
2. **Phương pháp (1 phút).** Vector Q-network có ba head dùng chung trunk;
   mỗi head có Double-DQN target. Replay giữ vector reward và behavior
   preference. Bốn tín hiệu phân bổ là gap, disagreement, coverage/recency và
   absolute progress. Uniform và matched-random là hai controls.
3. **Thiết kế (1 phút).** Primary block đã chạy 30 job: hai môi trường,
   ba arm, năm paired seed, 500.000 bước/job. Phân biệt training interactions,
   gradient updates, curriculum và validation. Không gộp các chi phí đó thành
   một số “training steps”. Các seed mới của Envelope là feasibility riêng.
4. **Kết quả và giới hạn (1–2 phút).** Chỉ vào bảng và đường cong trong PDF.
   Bảng dùng checkpoint cuối cố định; vùng tô là sample SD của năm training
   seed. Minecart primary có zero ore trên toàn bộ 14.400 episode validation.
   Vì vậy chưa chứng minh adaptive tốt hơn controls. Trình bày bảng Envelope
   đúng từng seed sau khi cohort hoàn tất; không dùng nó làm comparison matched.
5. **Demo (1–2 phút).** Mở app; reset cùng seed và checkpoint, giữ hai panel
   cùng preference, step để thấy kết quả khớp. Đổi slider rồi chạy so sánh.
   Có thể bật live mode để thấy preference đổi giữa trajectory; giải thích
   lúc này có lịch sử trước đó. Bật native renderer và xuất trace nếu cần.
6. **Kết luận (30 giây).** Nhóm đã triển khai và kiểm tra framework, giữ được
   dữ liệu validation và phát hiện thất bại của backbone. Đóng góp hiện tại
   là controlled implementation/failure analysis, không phải SOTA. Full
   ablations và final-test comparison của proposal gốc vẫn chưa hoàn thành.

## Những câu cần trả lời rõ

**Kéo slider có train lại không?** Không. Slider đổi preference input; weights
của checkpoint được giữ nguyên. App thực hiện inference và bước môi trường thật.

**Demo có phải model của bảng primary không?** Không. Hai model Uniform-PCQN
được train mới, mỗi model 100.000 bước, để thay weights bị mất trên laptop.
Nguồn checkpoint và plan được ghi trong package. Các checkpoint Envelope mới
được giữ riêng, không âm thầm thay model của app theo kết quả validation.

**Có phải đã giải được Minecart không?** Hãy đọc số episode ore dương theo
từng seed và checkpoint trong báo cáo. Nonzero hypervolume hoặc cart chuyển
động không đủ chứng minh giao ore. Không hứa demo sẽ hạ cánh hoặc giao ore.

**Tại sao có ore bằng 0 nhưng HV khác 0?** HV là thể tích đối với reference
point cố định trên tất cả mục tiêu. Cải thiện fuel so với reference vẫn có
thể cho HV dương, dù ore bằng 0. Phải kiểm tra từng objective.

**Kết quả âm có ý nghĩa gì?** Nó cho thấy chưa đủ điều kiện diễn giải lợi ích
phân bổ của learner trong setting đã thử. Chưa định vị được một nguyên nhân
duy nhất và không chứng minh mọi MORL method thất bại trên Minecart.

**Tính mới là gì?** Preference conditioning và adaptive allocation đã có
nghiên cứu trước. Nhóm nghiên cứu hẹp hơn: đo và so sánh các tín hiệu phân bổ
trong một framework có controls. Không tự nhận thuật toán đầu tiên hoặc SOTA.

**Tại sao không cứ train tiếp đến khi tốt?** Đó sẽ là thay đổi ngân sách sau
khi xem kết quả. Cohort mới có ba seed và ngân sách cố định, đủ để có một
kết quả mô tả trung thực; outcome âm vẫn được báo cáo và không được xóa.

**Đã dùng test set chưa?** Chưa. Những bảng hiện tại là validation. Final
test và các scientific gates cũ vẫn khóa. Không nói kết quả validation là
kết quả tổng quát hóa trên final test.

**Mất laptop có làm mất hết không?** Không. Git source đã push đến 18/10 và
aggregate nhúng của 300 checkpoint đánh giá còn giữ được. File weights cũ và
code/experiments chỉ nằm local sau 18/10 chưa phục hồi, nên chưa thể tái chạy
chính các checkpoint lịch sử. Numerical re-audit không thay cho rollout replay.

## Nguồn nghiên cứu chính

- [Dynamic Weights, ICML 2019](https://proceedings.mlr.press/v97/abels19a.html).
- [Envelope Q-learning](https://arxiv.org/abs/1908.08342).
- [Ví dụ Minecart của MORL-Baselines 1.3.0](https://github.com/LucasAlegre/morl-baselines/blob/v1.3.0/examples/envelope_minecart.py).
- Protocol, số liệu và các giới hạn tái lập nằm trong appendix của PDF.

Chỉ gửi/bảo vệ những tài liệu nhóm đã đọc và hiểu. Hạn nộp và rubric chính
thức vẫn cần xác nhận với thầy; gói local này chưa được tự động nộp ở đâu.

Cập nhật kết quả đã audit: hai seed Lunar prospective20266311/12 đều hoàn tất4M,
đáp đúng bãi10/10 ở cả sampled và argmax tại preference train. Thay mọi ô pending
trong bản kịch bản lịch sử dưới đây bằng kết quả này; pilot vẫn tách riêng.
Uniform secondary10/10 và9/10; không bảo đảm mọi preference. Xem
LUNAR_CONFIRMATION_RESULTS_20261103.md. Không có training đang chạy.

# Kịch bản trình bày REL301m — bản làm việc 3/11/2026

Chỉ dùng kết quả đã audit. Phần hai seed Lunar mới là kế hoạch đang thực hiện,
không được điền kết quả trước khi hoàn tất. Gói demo đã phát hành giữ nguyên.

## 1. Bài toán — khoảng 40 giây

Một tác vụ có nhiều mục tiêu xung đột. Lunar vừa cần đáp xuống, vừa cần tiết
kiệm nhiên liệu; Minecart cần lấy hai loại quặng và giảm chi phí di chuyển.
Preference là trọng số người dùng đặt cho các mục tiêu. Mục tiêu proposal là
nghiên cứu phân bổ việc học giữa các preference. Muốn kết luận về phân bổ,
trước hết policy phải thực hiện được nhiệm vụ.

## 2. Chúng em đã triển khai gì — khoảng 45 giây

Pipeline lưu vector reward, model nhận state cùng preference, có các cách phân
bổ rollout/update và các control. Phân biệt việc đổi input preference khi demo
với phân bổ dữ liệu khi train. Giữ raw và discounted/scaled return riêng;
không cộng rewards khác đơn vị rồi gọi là thước đo chiến thắng.

## 3. Kết quả âm và chẩn đoán — khoảng 60 giây

Các thí nghiệm value-based ban đầu không vượt được task gate Minecart.
Các bước sửa credit assignment/replay cũng không đủ. Đây là kết quả cần giữ,
không bỏ các seed thất bại. Có trajectory train gặp quặng nhưng policy greedy
vẫn không giao được quặng; chưa có bằng chứng về một nguyên nhân duy nhất.
PPO là backbone đã biết được dùng cho bước kiểm tra khả năng học tác vụ,
không trình bày nó là thuật toán adaptive allocation mới.

## 4. Kết quả tích cực đã có — khoảng 60 giây

Minecart: ba seed fresh,4 triệu bước mỗi seed; tất cả vượt task gate hai profile
ở cả sampled và argmax trên các ca phát triển đã định trước.
Lunar: một pilot4 triệu bước, trained preference [.7,.1,.1,.1], đạt10/10 hạ
cánh native+100 bên trong bãi ở cả hai mode tại checkpoint cuối. Nói rõ đơn vị
lặp là seed huấn luyện, không phải episode. Hai seed Lunar prospective đang
được xác nhận riêng; giữ phần này pending cho đến khi audit kết quả.

## 5. Kiểm tra preference khó hơn — khoảng 60 giây

Chẩn đoán actor argmax cố định trên5 seed môi trường mới,55 episode:
Lunar mặc định4/5, đồng đều4/5, shaping-only1/5 đáp đúng bãi.
Minecart mặc định5/5 và đồng đều5/5 giao quặng; các corner riêng từng ore0/5.
Fuel-only0/5 giao quặng không tự nó chứng minh sai preference: mục tiêu đó
không thưởng quặng. Cần đọc utility và chi phí nhiên liệu cùng task success.
Không bảo đảm mọi preference. Các kết quả này không được dùng để chỉnh
candidate giữa hai lượt confirmation. Xem bảng và trace trong báo cáo chẩn đoán.

## 6. Demo — khoảng 90 giây

Mở đúng gói LunarPPO bằng START_COURSE_DEMO.bat và địa chỉ terminal in ra.
Chạy Lunar mặc định, dùng Một bước/Renderer gốc. Đổi sang Minecart, chạy
mặc định rồi đồng đều, reset giữa các so sánh. Hai panel dùng cùng model và
seed đầu. Nếu đổi preference live, giải thích lịch sử khác nhau; không gọi đó
là so sánh hai episode độc lập. Tải trace JSON. Một lần trình diễn không thay
thế bảng đánh giá. Nếu gặp lỗi, dùng trace dự phòng đã audit, không giả video
là inference trực tiếp.

## 7. Giới hạn và bước xác nhận — khoảng 45 giây

Hai fresh seed Lunar,4M mỗi seed,giữ toàn bộ hyperparameter và final-only gate;
pilot không nằm trong nhóm xác nhận prospective. Không có adaptive advantage,
không có arbitrary-preference guarantee hay dynamics study. Final test gốc
vẫn khóa. Kết quả failure vẫn được báo cáo. Kết luận report môn cần phản ánh
phạm vi đã làm, không nói toàn bộ proposal đã hoàn thành.

## 8. Kết luận — khoảng 30 giây

Đóng góp thực tế: pipeline có thể kiểm tra lại, phân tích các thất bại và chỉ ra
backbone nào thực hiện được tác vụ trong phạm vi đã đo. Phần chưa làm được
là bằng chứng cho lợi ích adaptive allocation và khả năng đáp mọi trọng số.
Sau audit confirmation, thay riêng ô kết quả pending; không chọn seed đẹp nhất.

## Câu hỏi có thể gặp

- Vì sao đổi từ Q-learning sang PPO? Các task gate value-based chưa đạt; PPO
  là thí nghiệm feasibility riêng, không phải so sánh superiority công bằng.
- 10/10 có nghĩa chắc chắn thành công? Không; đó là10 ca đã định trước. Các ca
  môi trường mới của Lunar đã cho thấy4/5 ở default.
- Slider có chứng minh preference generalization? Không. Nó chứng minh model
  nhận input mới; bảng chẩn đoán mới đánh giá hành vi tại các trọng số cụ thể.
- Ba seed đủ chưa? Đây là ngân sách môn học nhỏ. Lunar có1 pilot+2 prospective,
  không đánh đồng thành3 confirmations; không khẳng định significance.
- Vì sao chưa dùng final test? Chưa đạt gate nghiên cứu gốc; không dùng nó để
  chọn hyperparameter hoặc checkpoint.

## Nội dung nhắn hỏi giảng viên — người dùng tự gửi

“Thầy/cô cho nhóm em xác nhận hạn nộp, thời lượng demo và định dạng báo cáo cuối
kỳ được không ạ? Proposal của nhóm nghiên cứu adaptive preference allocation.
Hiện nhóm có pipeline, kết quả âm và phân tích failure của backbone ban đầu,
cùng kết quả PPO feasibility ở Minecart và Lunar có nêu rõ giới hạn. Phần
so sánh adaptive allocation với controls trong proposal có bắt buộc phải hoàn
tất để đáp ứng môn học không, hay nhóm có thể báo cáo phạm vi đã kiểm chứng
và thảo luận phần chưa đạt ạ?”

Không có tin nhắn nào được gửi tự động. Chưa có xác nhận rubric/hạn nộp.

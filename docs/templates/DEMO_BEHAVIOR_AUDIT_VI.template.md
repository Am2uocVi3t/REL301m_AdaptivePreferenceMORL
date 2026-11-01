# Kiểm tra hành vi demo — 01/11/2026

Đã chạy 80 episode: 8 preference x 5 environment seed x 2 môi trường, trên
đúng hai model Uniform-PCQN trong gói hiện tại. Tổng cộng @@STEPS@@ bước chẩn
đoán, 0 training update và không dùng research final test. Đây là một model
mỗi môi trường; năm environment seed không phải năm lần train độc lập.
Không chọn lại checkpoint hoặc thay seed để lấy kết quả đẹp.

## LunarLander

@@LUNAR_TABLE@@

`+100` là định nghĩa kết thúc của engine. Cột trong pad chỉ kiểm tra vị trí x
nằm trong [helipad_x1, helipad_x2], không phải một qualification gate mới.
Hai lần +100 đều ở landing-heavy: seed 20000 đáp ngoài pad; seed 20003 nằm
trong pad x. Preference mặc định và balanced không có +100.

Pure-fuel có thể chấp nhận crash vì trọng số landing bằng 0; không nên dùng
riêng những anchor đó để kết luận mọi trade-off đều phải đáp an toàn.
Mixed/default policies vẫn chưa chứng minh điều khiển nhiệm vụ ổn định.

## Minecart

@@MINE_TABLE@@

Không episode nào thu được cargo hoặc giao ore. Policy phần lớn phanh hoặc
đứng im. Ore2-only có rời base, nhưng không tới vùng mine. Đổi action giữa
phanh và đứng im không thể hiện điều khiển trade-off ore thành công.

## Slider có thực sự tác động không?

Trên cùng 500 observation lấy mỗi 10 bước từ năm trajectory mặc định của
từng môi trường, thay preference làm thay action. Ví dụ balanced khác
default ở 39,6% probe Lunar; ore1-only khác default ở 100% probe Minecart,
chủ yếu phanh sang đứng im. Q-score/greedy action có đáp ứng input;
thành công nhiệm vụ là yêu cầu riêng và chưa đạt độ tin cậy.

Probe set này chỉ gồm state trên trajectory mặc định, không chứng minh
controllability trên toàn bộ state space. Pure objective anchors có thể
tạo ra trade-off cực đoan; không tự động tương đương lỗi slider hoặc lỗi
scalarization.

## Mức độ sẵn sàng

App chạy inference thật, model không đổi và raw trace đã được kiểm lại đủ
80 file bằng SHA256, tổng reward native và discounted/scaled return.
Nó dùng được để trình bày framework và failure analysis. Chưa nên gọi là
demo agent hoàn thành nhiệm vụ hoặc nghiên cứu đã chứng minh adaptive
allocation hiệu quả.

Cần cải thiện/qualify backbone dưới một study mới có ngân sách cố định
trước khi hoàn thiện các so sánh/ablation. Không mở lại hoặc kéo dài các
cohort đã kết thúc. Không đổi seed/preference mặc định của app để che
những thất bại đã quan sát.

@@BROWSER@@

Nguồn định nghĩa task:
[MO-Lunar-Lander](https://mo-gymnasium.farama.org/environments/mo-lunar-lander/)
và [Minecart](https://mo-gymnasium.farama.org/environments/minecart/),
đối chiếu thêm source pinned mo-gymnasium 1.3.2.

Raw vectors/episode summaries: `research/evidence/demo_behavior_audit_v1.json`.
Trace đầy đủ trên D: `artifacts/demo-behavior-audit-v1`.
Hình kết quả: `outputs/demo-behavior-audit-v1/behavior_summary.png`.
Native renderer và UI screenshots nằm trong thư mục artifact trên.

Kiểm tra UI chạy lặp lại bốn điều kiện trên có chi phí riêng, không gộp vào
58.828 bước của matrix 80 episode. Receipt ghi 7.813 bước của lượt UI thành
công và counter server cộng dồn 15.634 bước kể cả những lần thử harness trước.
Một lần chờ renderer trong harness cũ chưa đủ đã tạo screenshot sai thời điểm;
computed style xác nhận CSS của app đã ẩn canvas đúng. Đã sửa harness chờ
canvas ẩn, ảnh mới load xong và control trở lại sẵn sàng trước khi chụp.
Không sửa CSS/app/model hoặc tạo bản package khác cho vấn đề này.

# Kiểm tra hành vi demo — 01/11/2026

Đã chạy 80 episode: 8 preference x 5 environment seed x 2 môi trường, trên
đúng hai model Uniform-PCQN trong gói hiện tại. Tổng cộng 58,828 bước chẩn
đoán, 0 training update và không dùng research final test. Đây là một model
mỗi môi trường; năm environment seed không phải năm lần train độc lập.
Không chọn lại checkpoint hoặc thay seed để lấy kết quả đẹp.

## LunarLander

| Preference | w | +100 engine /5 | Trong pad x /5 | Crash /5 | Cap 1000 /5 |
|---|---|---:|---:|---:|---:|
| default | [0.255, 0.409, 0.164, 0.172] | 0 | 0 | 0 | 5 |
| balanced | [0.25, 0.25, 0.25, 0.25] | 0 | 0 | 1 | 4 |
| landing_only | [1.0, 0.0, 0.0, 0.0] | 0 | 0 | 5 | 0 |
| shaping_only | [0.0, 1.0, 0.0, 0.0] | 0 | 0 | 5 | 0 |
| main_fuel_only | [0.0, 0.0, 1.0, 0.0] | 0 | 0 | 5 | 0 |
| side_fuel_only | [0.0, 0.0, 0.0, 1.0] | 0 | 0 | 5 | 0 |
| landing_heavy | [0.7, 0.1, 0.1, 0.1] | 2 | 1 | 0 | 3 |
| fuel_heavy | [0.05, 0.05, 0.45, 0.45] | 0 | 0 | 5 | 0 |

`+100` là định nghĩa kết thúc của engine. Cột trong pad chỉ kiểm tra vị trí x
nằm trong [helipad_x1, helipad_x2], không phải một qualification gate mới.
Hai lần +100 đều ở landing-heavy: seed 20000 đáp ngoài pad; seed 20003 nằm
trong pad x. Preference mặc định và balanced không có +100.

Pure-fuel có thể chấp nhận crash vì trọng số landing bằng 0; không nên dùng
riêng những anchor đó để kết luận mọi trade-off đều phải đáp an toàn.
Mixed/default policies vẫn chưa chứng minh điều khiển nhiệm vụ ổn định.

## Minecart

| Preference | w | Rời base /5 | Tới mine /5 | Giao ore /5 |
|---|---|---:|---:|---:|
| default | [0.375, 0.359, 0.266] | 0 | 0 | 0 |
| balanced | [0.333, 0.333, 0.333] | 0 | 0 | 0 |
| ore1_only | [1.0, 0.0, 0.0] | 0 | 0 | 0 |
| ore2_only | [0.0, 1.0, 0.0] | 5 | 0 | 0 |
| fuel_only | [0.0, 0.0, 1.0] | 0 | 0 | 0 |
| ore1_heavy | [0.8, 0.1, 0.1] | 0 | 0 | 0 |
| ore2_heavy | [0.1, 0.8, 0.1] | 0 | 0 | 0 |
| ores_heavy | [0.45, 0.45, 0.1] | 0 | 0 | 0 |

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

Bốn trường hợp UI chạy hết episode bằng Edge (Lunar balanced/landing-heavy, Minecart ore1-only/ore2-only) khớp steps, weights và native returns của diagnostic trực tiếp. Native renderer và screenshots nằm tại artifacts/demo-behavior-audit-v1/browser.

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
Không sửa CSS/model cho vấn đề renderer này.

## Sửa lỗi HTTP độc lập với đánh giá policy

Khi chạy toàn bộ test trên Windows, request POST thiếu token có lúc bị ngắt
kết nối (WinError 10053) thay vì nhận response 403. Đã tái hiện hai lần trong
full suite và xác nhận server đóng kết nối khi body request còn chưa đọc.
Server hiện đọc bỏ body có Content-Length hợp lệ trong giới hạn 32 KiB,
dưới timeout socket sẵn có, trước khi trả 403. Không xử lý request bị từ chối
thành hành động môi trường. Test gửi 10 request bị từ chối và xác nhận không
có reset; toàn bộ 179 test đạt, 4 skip đã có lý do.

Cơ sở xử lý teardown: [RFC 9112, section 9.6](https://www.rfc-editor.org/rfc/rfc9112.html#section-9.6).
Bản `outputs/REL301m_Course_Project_20261101_httpfix.zip` mang sửa lỗi này.
Bản ZIP/PDF trước vẫn giữ nguyên. Model, config, physics và hàm chọn action
giống hệt bản đã đo 80 episode; sửa HTTP không cải thiện khả năng hạ cánh/ore.

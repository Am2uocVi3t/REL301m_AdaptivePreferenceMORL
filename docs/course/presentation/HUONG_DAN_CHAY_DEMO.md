# REL301m — Hướng dẫn demo PPO

Phiên bản LunarPPO, 03/11/2026. Inference trực tiếp, không phải video.

## Mở demo

Trên máy hiện tại: bấm START_COURSE_DEMO.bat ở repository, rồi mở địa chỉ mà terminal hiển thị. Cổng mặc định là http://127.0.0.1:8765. Giữ cửa sổ server mở. Nếu cổng bận, chạy scripts/start_course_demo.ps1 -Port 8768 trong PowerShell. Training monitor là cửa sổ riêng: START_TRAINING_MONITOR.bat.

Với ZIP: giải nén toàn bộ vào D:, đọc README_VI.md. Nếu chưa có dependencies, chạy INSTALL_D.ps1 một lần bằng PowerShell; cần internet cho lần cài đầu. Sau đó dùng START_DEMO.bat. Cần Windows x64 và Python 3.11. Không mở trực tiếp website/index.html. Không cần GPU hoặc API key để inference.

## Trình diễn khoảng ba phút

Chọn LunarLander. Mặc định hai panel dùng cùng checkpoint và cùng seed, với preference [.7,.1,.1,.1]. Bấm Chạy so sánh. Dùng Tạm dừng và Một bước để quan sát action và reward. Chuyển Renderer gốc để xem hình từ engine thật; đổi renderer không tạo bước physics.

Kéo slider bên phải, rồi bấm Chạy so sánh để reset cả hai về cùng seed và áp dụng preference mới. Chế độ đổi preference khi đang chạy giữ lịch sử cũ: đó không phải so sánh hai episode độc lập. Slider thay đầu vào mạng, không train lại model.

Chọn Minecart và lặp lại. Tải trace JSON để kiểm tra state, preference, action, reward và nguồn checkpoint. Hai panel cùng môi trường dùng chung một model; đây không phải so sánh hai thuật toán.

## Kết quả và giới hạn cần nói đúng

Minecart dùng PPO final 4 triệu bước, seed20264311 được chọn bằng quy tắc seed nhỏ nhất. Ba seed huấn luyện độc lập đều đạt 10/10 lượt hoàn thành nhiệm vụ ở hai profile và cả hai chế độ inference trên các ca phát triển đã định trước.

Lunar dùng PPO + GAE final 4 triệu bước, seed20265311. Đây là pilot một seed, train với [.7,.1,.1,.1]. Checkpoint cuối đạt 10/10 hạ cánh native +100 bên trong bãi ở cả sampled và argmax trên các ca phát triển. Demo dùng argmax. Chưa có xác nhận Lunar qua nhiều seed huấn luyện.

Preference đồng đều của Lunar cũng hạ cánh 10/10 ở các ca đó nhưng utility vẫn âm. Hạ cánh được khác với đáp ứng tốt mọi ưu tiên. Không bảo đảm mọi trọng số, mọi trạng thái hoặc mọi điều kiện dynamics; không khẳng định adaptive allocation tốt hơn controls. Các ca demo lặp lại tập phát triển, không phải final test hay xác nhận nghiên cứu độc lập.

## Báo cáo và vận hành

Báo cáo theo mẫu nhóm nằm ở docs/Bao_cao.pdf; hướng dẫn này ở docs/Huong_dan.pdf. Config và MANIFEST.json ghi checkpoint/hash của đúng phiên bản. Những hướng dẫn cũ được lưu trong docs/historical-release và chỉ mô tả các bản trước.

Inference không cập nhật tham số. Bộ đếm training updates bằng 0 trong app là số update trong phiên demo. Ctrl+C dừng server. Nếu lỗi, kiểm tra terminal; không tự động train hoặc đổi checkpoint. Báo cáo giữ các kết quả âm trước đây, các giới hạn nghiên cứu và phần proposal chưa hoàn tất. Cần xác nhận rubric/hạn nộp với giảng viên trước khi nộp.

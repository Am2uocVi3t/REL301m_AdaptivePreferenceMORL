# Hướng dẫn demo MORL

**REL301m - gói phục hồi ngày 01/11/2026**

## 1. Mở trên máy hiện tại

Ở thư mục repository trên ổ D, bấm đúp `START_COURSE_DEMO.bat`. Giữ cửa sổ
Python đang mở, sau đó vào **http://127.0.0.1:8765** bằng Edge hoặc Chrome.
Không mở trực tiếp file HTML và không chạy website trong cửa sổ xem ZIP.

Nếu cổng 8765 bận, dùng PowerShell tại repository:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start_course_demo.ps1 -Port 8766
```

Chỉ dùng loopback trên máy; không cần API key, không gọi dịch vụ trả phí, không
training khi mở app. Model và dependency nằm trên D. Ctrl+C dừng server.

## 2. Trình diễn trong khoảng ba phút

- Chọn LunarLander. Hai panel dùng cùng model và cùng reset seed.
- Bấm **Chạy so sánh** để reset và chạy hai preference.
- Kéo slider bên phải. Tổng trọng số luôn bằng 100%. Ở chế độ thường, bấm Chạy so sánh để áp dụng và reset cùng seed.
- Dùng **Tạm dừng** và **Một bước** để xem state, action và reward thay đổi.
- Bật chế độ đổi preference khi đang chạy nếu muốn: input đổi từ tick tiếp theo, lịch sử không reset. Đây không phải retraining.
- Chuyển **Renderer gốc** để đối chiếu sprites với engine thật.
- Chọn Minecart để minh họa hai mục tiêu ore và chi phí fuel. Zero ore là kết quả có thể xảy ra, không phải hình ảnh dựng sẵn.
- Tải trace JSON nếu cần kiểm tra state, preference, action, vector reward và provenance.

## 3. Những điều cần nói chính xác

Model trong app là Uniform-PCQN mới huấn luyện để thay thế checkpoint bị mất:
mỗi môi trường 100.000 training interactions, một seed cố định, chỉ dùng checkpoint
cuối. Đây là model trình diễn, không phải bản model cũ đã cứu lại được.

Thí nghiệm nghiên cứu trong báo cáo là 30 job lịch sử khác, với năm paired seed
trên hai môi trường. Không dùng model trình diễn để tạo bảng kết quả đó.

Hai panel so sánh preference của **cùng một model**, không phải so sánh hai
thuật toán. Slider có thể tạo hành vi giống nhau; không đảm bảo policy đã học
được mọi preference hoặc giải được nhiệm vụ. Không thay physics, reward hay cargo
để làm kết quả trông thành công.

Inference không cập nhật tham số; bộ đếm gradient updates trong app bằng 0 là
số update trong phiên inference, không phải số update khi model được huấn luyện.

## 4. Dùng ZIP trên máy Windows khác

Giải nén toàn bộ gói vào ổ **D:**, không để trong Downloads trên C. Đọc README_VI.md.
Chạy `INSTALL_D.ps1` một lần nếu máy chưa có môi trường của gói; internet cần
cho lần cài dependency đầu. Bootstrap, Python, cache và venv được đặt bên trong
gói trên D. Sau đó dùng `START_DEMO.bat`. Môi trường đã kiểm trên Windows x64,
Python 3.11 CPU; không tuyên bố hỗ trợ những hệ điều hành chưa kiểm.

Gói có wheel Box2D 2.3.8 và provenance/license, tránh build C++ trên máy trình bày.
Không cần cài MORL-baselines hoặc pycddlib để chạy app inference này.

## 5. Báo cáo và giới hạn

Liên kết báo cáo PDF và hướng dẫn nằm trong app. Báo cáo giữ kết quả âm Minecart,
không khẳng định adaptive allocation tốt hơn controls và không có final-test claim.
Original checkpoint files và code sửa trên laptop sau 18/10 chưa được phục hồi.
Đối chiếu rubric/hạn nộp với giảng viên trước khi nộp gói.

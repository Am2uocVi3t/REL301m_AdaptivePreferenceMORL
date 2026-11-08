# REL301m - báo cáo và demo phục hồi

Trên máy hiện tại: ở thư mục repository trên D, bấm `START_COURSE_DEMO.bat`.
Mở http://127.0.0.1:8765 bằng Edge/Chrome và giữ cửa sổ server đang chạy.

## Dùng ZIP trên Windows x64

1. Giải nén toàn bộ gói vào D:, không dùng cửa sổ xem ZIP.
2. Mở PowerShell trong thư mục giải nén, chạy:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File INSTALL_D.ps1
```

3. Lần đầu cần internet và khoảng 1-2 GB trống trên D để tải Python/dependency/cache.
   Installer dừng trước khi download nếu thư mục không ở D. Không yêu cầu quyền admin.
4. Bấm START_DEMO.bat, mở http://127.0.0.1:8765. Ctrl+C để dừng. Các lần inference
   sau không cần tải lại model. Không có training, API key hoặc dịch vụ trả phí.

Python 3.11.18 được bootstrap bằng uv 0.13.6 kèm license; wheel Box2D 2.3.8
được repack từ conda-forge, có nguồn và SHA256 trong NATIVE_BOX2D_PROVENANCE.json.
Không cần compiler, MORL-baselines hay pycddlib để dùng app inference này.
Không tuyên bố gói Windows đã được kiểm trên Linux/macOS.

## Thao tác và ý nghĩa

Hai panel dùng cùng checkpoint và reset seed; panel phải nhận preference từ slider.
Đổi slider rồi bấm Chạy so sánh để reset. Bật live mode nếu muốn áp dụng từ tick
tiếp theo mà giữ lịch sử. Dùng pause/step/native renderer và tải trace JSON để kiểm tra.
Tham số model không đổi khi kéo slider. Hai panel không so sánh hai thuật toán.

Model là hai Uniform-PCQN mới huấn luyện, mỗi môi trường 100.000 bước, một seed
cố định, chỉ checkpoint cuối. Chúng thay thế weights bị mất để chạy demo; không
phải model lịch sử đã khôi phục và không phải bằng chứng adaptive allocation thắng.
Không đảm bảo hạ cánh hoặc giao ore; zero ore được giữ nguyên.

Báo cáo nghiên cứu sử dụng 30 job lịch sử riêng biệt, với dữ liệu per-episode
được giữ trong research/evidence/course_primary_validation_v1.json. Không trộn
model demo vào bảng nghiên cứu. Các scientific gates cũ không được mở bởi gói này.

PDF báo cáo/hướng dẫn nằm trong docs và có liên kết trong app. Nguồn Markdown,
protocol, plan và execution metadata được kèm để đối chiếu. Checkpoint cũ và code
trên laptop sau 18/10 chưa tìm lại được; final test chưa được sử dụng.

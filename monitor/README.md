# Native training terminal

Bấm đúp **START_TRAINING_MONITOR.bat** ở thư mục gốc. Nó mở giao diện terminal
thật trong PowerShell, dùng Rich có sẵn trên runtime CPU ở D:. Không cần trình
duyệt, HTTP server hay cài thêm package vào môi trường GPU training.

- ↑/↓ hoặc J/K: chọn worker; danh sách tự cuộn theo dòng đang chọn.
- Tab: đổi giữa stderr và stdout của worker.
- Space: pause/resume việc cập nhật màn hình; training không bị ảnh hưởng.
- R: cập nhật ngay; Q hoặc Ctrl+C: đóng monitor, không dừng training.
- Mặc định tự cập nhật 5 giây. Khi terminal hẹp, ẩn bớt cột; tăng kích thước
  cửa sổ để xem cả updates và task deliveries.

```powershell
. scripts/use_d_runtime.ps1
. scripts/start_training_monitor.ps1
# Hoặc in một snapshot, không giữ giao diện tương tác:
.venv/Scripts/python.exe scripts/training_terminal.py --once
```

Terminal tự chuyển sang Minecart PPO specialist khi có manifest của pilot mới;
nếu chưa có thì theo dõi cohort P2 Minecart. Với PPO, hiển thị ngân sách4M,
entropy/target từ stdout và final deliveries sampled/argmax riêng ở profile được
train. Evaluation chi tiết cả hai profile được giữ trong artifact của checkpoint.
Running dựa trên process command thực tế
trong Windows; Complete nghĩa là ghi xong job, chưa phải đạt task gate. Tiến độ
live lấy từ stdout theo mốc 25k bước, có thể trễ. Final deliveries hiển thị hai
profile riêng. Tên file snapshot là metadata, chưa phải checksum validation.
Log giữ cả segment cũ; không suy từ traceback cũ ra worker hiện tại đã chết.

Để tránh lỗi I/O đã phát hiện, collector không mở các JSON đang được writer thay
thế: heartbeat, progress, execution_status, resume_latest. Nó đọc process metadata,
log append và dữ liệu chỉ publish một lần; evaluations/losses chỉ đọc khi có
completion marker. Trên máy này, FILE_SHARE_DELETE một mình vẫn chưa đủ tránh
lỗi os.replace. Monitor không tự sửa hoặc retry training.

Tất cả output kiểm chứng/log ở artifacts/training-monitor trên D:. Rich15.0.0
đã có sẵn; pin monitor-only ở requirements-terminal.txt. Bản web thử nghiệm cũ
còn trong Git và có launcher riêng start_training_web_monitor.ps1; launcher
mặc định ở trên là terminal và không khởi động web server.

# Training console

Mở **http://127.0.0.1:8770/** hoặc bấm đúp `START_TRAINING_MONITOR.bat` ở thư mục
gốc. Dashboard hiện theo dõi cohort **P2 Minecart preference recovery**. Server
đã chạy thì launcher dùng lại; không tạo bản sao trên cùng port.

Giao diện tự cập nhật mỗi 5 giây khi tab đang hiển thị. Chọn worker để xem log,
snapshot gần nhất và kết quả cuối; lọc Active / Needs attention / Complete /
Pending. `R` hoặc Refresh cập nhật ngay. Pause view chỉ ngừng cập nhật giao diện.
Đóng dashboard không dừng training. Sau khi khởi động lại Windows, mở launcher
lần nữa; không cài service, scheduled task hay tự động đăng nhập.

## Cách hiểu số liệu

- **Connected**: dashboard kết nối được server, không có nghĩa training đang chạy.
- **Running**: Windows đang có process với command và seed/arm tương ứng;
  không chỉ dựa vào cờ running lưu trên đĩa.
- **Draining**: đã có lỗi; coordinator ngừng dispatch mới, để worker còn lại chạy xong.
- **Blocked**: không còn worker/coordinator hoạt động và có job lỗi cần xử lý.
- **Complete**: job đã ghi kết quả cuối, không có nghĩa phương pháp đã đạt gate.
- **Recorded progress**: job live theo log stdout mỗi 25k bước, có thể trễ;
  job hoàn tất dùng đúng số tương tác trong completion record. Không dựng ETA
  hoặc nội suy số bước chưa ghi. `—` nghĩa chưa có dữ liệu, không phải số 0.
- **Snapshot file**: mốc tên file checkpoint nhìn thấy trên đĩa, chưa phải kết
  luận đã kiểm tra checksum/pointer khôi phục.
- **Final deliveries**: hai task profile tách riêng. Loss thấp hoặc training
  hoàn tất không tự chứng minh task success. Loss chỉ hiện sau khi worker ghi
  file kết quả, không tạo đường cong giả cho worker chưa có dữ liệu.
- Log giữ cả các segment cũ; traceback trong stderr có thể là lịch sử nếu
  worker đang chạy lại. Badge trạng thái process cho biết tình trạng hiện tại.

## Đọc dữ liệu mà không chặn writer

Witness trên máy này cho thấy **FILE_SHARE_DELETE vẫn chưa đủ** để bảo đảm
`os.replace` thành công dưới một reader đang mở. Dashboard vì vậy không mở
`heartbeat.json`, `progress.json`, `resume_latest.json` hay `execution_status.json`
của training. Nó dùng process enumeration của Windows, stdout/stderr append,
tên file snapshot và các artifact đã publish một lần. `evaluations.json` và
`losses.json` chỉ được đọc sau `complete.json`, khi writer đã ghi xong.
Đây là sửa cách monitor; lỗi I/O của training helper vẫn cần recovery riêng.

## Vận hành

```powershell
. scripts/use_d_runtime.ps1
. scripts/start_training_monitor.ps1              # mở trình duyệt
. scripts/start_training_monitor.ps1 -NoBrowser   # chỉ bảo đảm server đang chạy
```

Server localhost, API chỉ đọc; không có nút start/stop/retry training. Không
cài thêm package vào runtime train. Cache/log riêng ở `artifacts/training-monitor`
trên D:. Có thể dùng `-Port 8771` nếu port mặc định thuộc ứng dụng khác.
Các tab log cũng có thể chứa đường dẫn máy của bạn; server chỉ bind 127.0.0.1,
chặn Host/Origin ngoài localhost và không xuất lên Internet.

Kiểm chứng: `pytest -q tests/test_training_monitor.py`; browser thực tế qua
`node scripts/verify_training_monitor.cjs` với Playwright có sẵn trong Codex
runtime và Microsoft Edge. Screenshot/receipt ở
`artifacts/training-monitor/verification`. Cấu hình visual riêng tại `monitor/DESIGN.md`.

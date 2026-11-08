# REL301m - Website tương tác model đã train

Đây là app Python + website local thật, không phải video hoặc trang HTML giả lập
policy. Một checkpoint cố định cho mỗi môi trường, dùng chung ở hai bên. Kéo
preference rồi reset/chạy, hoặc bật live-mode để đổi đầu vào model ngay khi chạy.
Không có train lại, optimizer, API key, Claude hay chi phí dịch vụ.

## 1. Cài một lần

Giải nén toàn bộ ZIP. Dùng **Python 3.11**, không phải 3.14. Cần internet để tải
dependency lần đầu, sau đó inference chạy offline. Không cần GPU, Node hay npm.

Linux/macOS (trong thư mục giải nén):

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install swig==4.4.1
.venv/bin/python -m pip install -r requirements.txt
bash START_DEMO.sh
```

Windows, Command Prompt:

```bat
py -3.11 -m venv .venv
.venv\Scripts\python -m pip install swig==4.4.1
.venv\Scripts\python -m pip install -r requirements.txt
START_DEMO.bat
```

Mở **http://127.0.0.1:8765** trong Chrome/Edge/Firefox. Đây không phải double-click
website/index.html. Backend cần đang chạy; Ctrl+C để dừng. Cổng bận thì dùng
`bash START_DEMO.sh --port 8766` hoặc `START_DEMO.bat --port 8766`.

PyTorch có thể tải lớn. Nếu chỉ dùng CPU trên Linux/Windows, có thể cài trước:
`.venv/bin/python -m pip install torch==2.14.1 --index-url https://download.pytorch.org/whl/cpu`
(đổi đường dẫn Python theo Windows), rồi cài requirements. Không tải model mới.

Nếu Box2D phải build source, cần SWIG và C/C++ build tools của hệ điều hành.
Linux thường cần `build-essential python3.11-dev`; macOS cần Xcode Command Line
Tools; Windows có thể cần Microsoft C++ Build Tools. Không tự cài công cụ hệ thống
hay dùng quyền admin nếu chưa được phép. Không tuyên bố cài đặt đã pass trên OS
khác: bản này được kiểm tra runtime trên Linux/Python 3.11 CPU.

## 2. Thao tác demo

1. App khởi tạo LunarLander ở trạng thái tạm dừng. Hai bên dùng cùng checkpoint,
   seed và preference mặc định từ validation đã có; không dùng final-test.
2. Bấm **Chạy so sánh**. Hai environment reset về cùng seed rồi model chọn action
   theo state và w mỗi bước. Bên trái giữ w mặc định; bên phải dùng slider.
3. Kéo một slider: các trọng số còn lại tự chia lại để tổng bằng 100%. Trong chế
   độ thường, đây là **pending**, chưa ảnh hưởng episode hiện tại. Bấm Chạy so sánh
   để áp dụng và reset cả hai từ cùng seed. Không giả vờ áp dụng ngay.
4. Bật **Đổi preference khi đang chạy**: w mới vào network từ tick kế tiếp, bên
   phải không reset. Website ghi cảnh báo lịch sử khác nhau. Nếu tạm dừng, bấm
   Tiếp tục hoặc Một bước để áp dụng; kéo slider không tự tạo environment steps.
5. Tạm dừng/Tiếp tục, Một bước, tốc độ 1x/2x/4x và Toàn màn hình dùng cho trình chiếu.
   Tốc độ thực phụ thuộc CPU/trình duyệt; tốc độ cao có thể bỏ qua khung hình giữa,
   nhưng backend vẫn thực hiện đủ transitions. Episode tối đa 1.000 bước, không
   tự lặp lại khi kết thúc. Bấm Chạy so sánh để chạy lại.
6. Chọn Minecart để dùng checkpoint Minecart; không thay thuật toán bằng một model
   đẹp hơn. Chọn **Renderer gốc** để đối chiếu với Sprite nâng cấp.
7. Tải trace JSON nếu cần kiểm tra state, w, action, vector reward, switches và
   provenance. Trace chỉ là dữ liệu trình diễn, không qualification/benchmark.

## 3. Sprite đẹp hơn nhưng không đổi mô phỏng

Canvas vẽ từ tọa độ engine thật: thân/chân tàu, địa hình/điểm đáp; xe, vị trí mỏ,
orientation và cargo. Tàu kim loại, kính, động cơ, bề mặt khoáng và trạm là lớp vẽ
trang trí. Đường mờ là các vị trí đã đi qua, không phải kế hoạch đường đi. Không
tự chuyển xe đến mỏ, không sửa reward/collision, không thêm cargo giả. Native
renderer có sẵn để kiểm tra. Đổi skin không cập nhật model hoặc bước physics.

## 4. Giới hạn cần nói trước lớp

- Đây là preference conditioning: cùng model đã train nhận state + w. Không phải
  học online hay retraining sau mỗi lần kéo slider. Không phải A/B giữa hai thuật toán.
- Trọng số ràng buộc tổng 1; các mục tiêu phạt dùng reward âm, trọng số cao hơn là
  đặt nặng tránh phạt đó. Raw return được ghi theo từng mục tiêu, không cộng các
  đơn vị khác nhau để tuyên bố policy thắng. Network đã học với reward scale cố định.
- Đổi w không đảm bảo hành vi đẹp hoặc khác nhau ở mọi state. Minecart v2 đã thất
  bại qualification: có thể đứng yên/zero ore. Không có cam kết slider sẽ giúp khai
  thác thành công. LunarLander cũng có thể rơi hoặc tốn nhiên liệu.
- Mỗi môi trường đã được train riêng từ trước; trong một môi trường chỉ nạp một
  checkpoint để hai bên dùng chung. Không load checkpoint khác khi đổi slider.
- Seed trình diễn cố định để so cùng trạng thái đầu; hai policy đi khác đường thì
  state sẽ khác. Minecart dùng RNG cô lập từng panel vì package gốc dùng scipy
  global RNG khi khai thác. Không có đánh giá final-test hay unlock research gate.
- Local-only, một phiên giao diện điều khiển. Không public server, không mở nhiều
  tab cùng điều khiển. Origin/token, model SHA256 và tick ID được kiểm tra. Nếu
  timeout/lỗi: dừng, không tự retry bước; kiểm tra trạng thái rồi reset/tải lại.

## 5. Gói có gì

`website/`, `src/` (chỉ inference + environment wrapper), `checkpoints/` (chỉ trọng
số/architecture đã trích từ checkpoint cũ, không optimizer), `config.json` (hash và
provenance), requirements, launchers, hai PDF trong `docs/`, `MANIFEST.json`.
Không chứa training runner, dataset final-test, log riêng, credential, paper PDF
bên thứ ba hoặc video làm thay model. Không commit/push/submit tự động.

Team cần thử cài dependencies, slider, live-mode, fullscreen và Minecart trên chính
laptop mang đến lớp, xác nhận roster và phân vai. Xem VERIFICATION.json để biết
những gì đã kiểm tra thực tế và phần nào còn chưa kiểm tra.

Báo cáo PDF giữ snapshot nghiên cứu đã có; đoạn mô tả demo replay cũ trong báo cáo
không phải hướng dẫn website hiện tại. Hướng dẫn PDF và README này thay thế đoạn
đó về cách sử dụng demo. Không có clip MP4 thay thế model trong ZIP website.

Nguồn cài đặt: [SWIG trên PyPI](https://pypi.org/project/swig/4.4.1/) và
[PyTorch hướng dẫn chính thức](https://pytorch.org/get-started/locally/).

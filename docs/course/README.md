# 🎓 HỒ SƠ BÀO CÁO & BẢN GIAO MÔN HỌC REL301m

Tài liệu chính thức dành cho việc nộp bài, thuyết trình cuối kỳ và chạy demo môn học REL301m (Fall 2026).

> Phạm vi xác nhận ngày 12/11/2026: chuẩn bị **link repository để nộp**.
> Các nguồn report/thuyết trình dưới đây là tài sản đã có; định dạng report cuối
> kỳ (slide hay PDF) còn chờ xác nhận. Video demo chỉ thực hiện khi được yêu cầu.
> Bản clone chưa có checkpoint/gói `outputs/`; xem
> [hướng dẫn chạy và giới hạn demo](../../README.md#sử-dụng-demo).

---

## 📂 Cấu trúc Hồ sơ Môn học

1. **[Thuyết trình & Kịch bản nhóm (`presentation/`)](./presentation/README.md):**
   * **[Kịch bản Slide & Phân chia 3 người](./presentation/KICH_BAN_SLIDE_VA_PHAN_CHIA_3_NGUOI.md):** Dàn ý 10 slide trực quan + phân vai chi tiết cho Hưng (Dẫn nhập & Demo), Việt (Kiến trúc & Toán MORL), Nam (Thực nghiệm & Phân tích lỗi) kèm bộ câu hỏi vấn đáp với phản biện.
   * **[Kịch bản Thuyết trình Chi tiết (~6 phút)](./presentation/KICH_BAN_THUYET_TRINH_CUOI_KY_FINAL.md):** Kịch bản thoại từng phút từ mở đầu đến kết luận.
   * **[Cẩm nang Thuật ngữ A-Z](./presentation/DOC_CHO_TEAM_TONG_QUAN_VA_THUAT_NGU.md):** Giải thích cặn kẽ các khái niệm MORL, Pareto Front, PPO vs PCQN, GAE, Coverage, v.v.
   * **[Hướng dẫn Thao tác Live Demo](./presentation/HUONG_DAN_CHAY_DEMO.md):** Các bước kéo slider và giải thích trong 3 phút.
   * **[Thư mục hình ảnh slide (`presentation/figures/`)](./presentation/figures/):** Hình vẽ chuẩn bị sẵn để chèn trực tiếp vào slide Canva / PowerPoint.

2. **[Báo cáo Khoa học Chính thức (`paper/REL301m/`)](../../paper/REL301m/README.md):**
   * Mã nguồn LaTeX bài báo 16–19 trang theo định dạng chuẩn: `paper/REL301m/main.tex`.
   * Lệnh biên dịch PDF tự động: `./scripts/build_course_latex_report.ps1`.

3. **[Các Cột mốc & Báo cáo Tiến độ Lịch sử (`milestones/`)](./milestones/):**
   * `initial-progress-report.md`: Báo cáo tiến độ ban đầu.
   * `course-completion-v2.md`: Phạm vi hoàn thành nhiệm vụ và chuyển đổi PPO.
   * `recovery-course-plan.md`: Kế hoạch khắc phục và phục hồi thực nghiệm.
   * `monday-team-package.md`: Gói bàn giao thử nghiệm đầu kỳ.

---

## 🚀 Hướng dẫn Chạy Nhanh Cho Giảng Viên & Nhóm

* **Khởi chạy Web Demo Tương tác (Kéo slider thay đổi trọng số):**
  Nhấp đúp vào [`START_COURSE_DEMO.bat`](../../START_COURSE_DEMO.bat) ở thư mục gốc và mở trình duyệt tại `http://127.0.0.1:8765`.
* **Khởi chạy Terminal Monitor Native (Theo dõi GPU, loss, workers):**
  Nhấp đúp vào [`START_TRAINING_MONITOR.bat`](../../START_TRAINING_MONITOR.bat) ở thư mục gốc.

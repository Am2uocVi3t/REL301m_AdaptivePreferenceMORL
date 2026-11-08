# Kiểm kê khôi phục và kế hoạch hoàn thành REL301m

Ngày kiểm tra: 01/11/2026 (Asia/Bangkok). Ưu tiên hiện tại: hoàn thành môn học.

## Phạm vi người dùng xác nhận ngày 01/11/2026

- Người dùng xác nhận khoảng 18–22/10 có cả sửa code và chạy thí nghiệm trực tiếp trên laptop bị mất. Snapshot GitHub 18/10 chưa bao phủ chắc chắn phiên bản làm việc cuối; có thể thiếu cả code và dữ liệu chạy. Chưa biết các thay đổi đã commit hay chưa và có backup hay không. Ưu tiên tìm bản sao ổ đĩa/thư mục repo/cloud sync/clone khác trước khi dựng lại phần việc mất; không giả định có output trên Kaggle/Colab.

- Mục tiêu là đồ án đại học với báo cáo, demo và thông tin đầy đủ; chưa ưu tiên công bố bài báo.
- Hạn báo cáo cuối chưa biết vì chưa hỏi giảng viên. Chưa có rubric chính thức xác nhận số môi trường, seed hoặc ablation tối thiểu; không tự xem các mục đó đã được miễn.
- Bộ đầu ra dự kiến: báo cáo giải thích bài toán, phương pháp, thiết kế thí nghiệm, kết quả có bằng chứng và giới hạn; demo chạy được kèm hướng dẫn; README về cài đặt, lệnh chạy và nguồn dữ liệu/kết quả.
- Ưu tiên khôi phục code và demo, kiểm kê bằng chứng còn lại trước khi quyết định chạy bù. Kết quả âm được báo cáo trung thực; không đặt điều kiện phương pháp phải thắng mới hoàn thành đồ án.
- Việc xác nhận đầu ra ở đây chưa tự động gỡ yêu cầu tạm giữ manuscript/TeX/PDF được ghi trong nhánh cũ. Chưa sửa các tài liệu đó trong phiên này.

## Trạng thái Git đã kiểm tra trực tiếp

Cập nhật triển khai tiếp theo: nhánh hiện tại đã đổi tên thành `codex/course-recovery-20261101`. Python 3.11 PCQN chạy được trên Windows; đã sửa các lỗi pipeline trọng yếu và có hai smoke checkpoint mới, không coi chúng là model cũ. Quan trọng: aggregate JSON trong Git giữ đủ tensor raw/discounted của 300 primary checkpoint; đã tái kiểm số học 28.800 episode. Các ghi chú “chưa xác nhận tensor” bên dưới là trạng thái điều tra ban đầu. Toàn bộ 300 file checkpoint cũ vẫn thiếu; pycddlib/baseline runtime đầy đủ chưa sẵn sàng. Báo cáo phục hồi có tại `docs/research/COURSE_REPORT_RECOVERED_DRAFT.md`.

Cập nhật sau rà soát code ngày 01/11: đã tạo và checkout `codex/alignment-audit-20261101` từ snapshot `e223362`; không đổi `main`. Đã fetch thêm các PR head/merge refs, không thấy commit 19–23/10. Người dùng nhớ làm việc đến 22/10, nên phần sau 18/10 vẫn là khoảng cần khôi phục. Kết quả review code và giới hạn xác minh mới ở `alignment-audit-20261101.md`. Các mô tả “chưa checkout” bên dưới ghi trạng thái tại thời điểm kiểm kê ban đầu.

- Working tree ban đầu sạch; đang ở `main`, commit `286129220e7522bef19e8e1475a76f8662b3aa65`, ngày 15/10/2026 02:23:03 +07.
- `git ls-remote --heads origin` xác nhận nhánh GitHub mới nhất còn tồn tại: `codex/aris-full-workflow`, commit `e223362b9c9c3e8efdcaa961d16f9054e942818f`, ngày 18/10/2026 04:18:58 +07. Nội dung commit: `Record failed F1 replay screen and evidence-bounded reviews`.
- Nhánh đó đi trước `main` 26 commit, không có commit riêng của `main` trong phép so sánh hai đầu nhánh. Đây là phần đã push, không phải commit chỉ còn trên máy mất.
- Clone này được tạo ngày 01/11/2026 theo reflog. Không có stash; `git fsck --full --no-reflogs --unreachable` không báo object thất lạc. Reflog của clone mới không chứa reflog của máy cũ.
- Không tìm thấy commit trên các branch remote hiện tại mới hơn 18/10. Kiểm tra này không bao phủ bản clone khác, fork, PR ref đã xóa hoặc bản sao lưu ngoài repository.
- Chưa checkout, merge, reset, push hoặc sửa code/protocol. File này là ghi chép kiểm kê mới.

## Phần đã cứu được và phần chưa có

Nhánh `e223362` chứa code, protocol đã calibration/freeze, registry, audit JSON, qualification, nguồn báo cáo LaTeX, demo web và hồ sơ kết quả âm. Không nên bắt đầu lại từ tài liệu `main` ngày 15/10: nó chưa phản ánh tiến độ này.

Các nguồn đã đọc trực tiếp bằng `git show`:

- `docs/research/PROJECT_STATUS.md` và `docs/research/HANDOFF_PROMPT.md`.
- `research/evidence/course_primary_validation_v1.json`: khối 30 job được ghi nhận, validation `failed_degenerate`.
- `research/qualification/course_matrix_post_validation_gate_v1.json`: matrix v1 bị chặn; không tiếp tục bằng cách sửa tại chỗ.
- `research/qualification/minecart_pcqn_replay_f1.json`: `failed`, không mở F2, matrix v1, checkpoint lock hoặc final test.
- `refine-logs/EXPERIMENT_RESULTS_20261018_035600.md`: sáu job F1, 60 checkpoints, 9.600 lượt đánh giá validation; ba treatment seed không biểu hiện ore dương. Đây không phải 9.600 training replicate độc lập.
- `paper/REL301m/EVIDENCE_INDEX.md`: chỉ mục bằng chứng cho báo cáo tiến độ.

Các con số trên là nội dung hồ sơ versioned đã kiểm tra; chưa tái chạy thí nghiệm hoặc kiểm chứng các hash với raw files trên máy này. Không có cơ sở xác nhận adaptive allocation vượt controls.

Không có file checkpoint `.pt`/`.pth`/`.ckpt`, tensor `.npz`/`.npy`, ZIP, hay file dưới `artifacts/`, `results/`, `outputs/` trong cây Git của nhánh mới nhất. Các thư mục output đó cũng không tồn tại ở clone hiện tại. Một số JSON trong Git giữ số liệu/audit hữu ích, nhưng chưa xác nhận chúng thay thế được đầy đủ raw per-episode tensors. Demo code có thể phục hồi; chưa thể hứa phục hồi demo dùng trained weights.

Commit thực sự chỉ có trên ổ đĩa máy mất không tự xuất hiện trên GitHub. Muốn cứu cần một bản sao object Git/ổ đĩa, clone từng nhận commit, backup, hoặc môi trường chạy từ xa còn dữ liệu. Hash hoặc commit message riêng lẻ không tái tạo được nội dung commit. Checkpoint/log không được Git theo dõi cần khôi phục riêng.

## Kế hoạch tiếp tục

- [x] Xác nhận branch/commit mới nhất bằng remote, kiểm tra reflog/stash/unreachable objects và phân biệt bản `main` cũ với nhánh nghiên cứu.
- [ ] Tạo branch làm việc từ đúng snapshot: `git switch -c codex/course-recovery-20261101 origin/codex/aris-full-workflow`. Giữ ghi chép này khi chuyển nhánh; đọc bootstrap của nhánh mới trước khi chỉnh sửa.
- [ ] Tìm bản sao còn lại của `.git`, `artifacts/`, `outputs/`, checkpoints và raw validation ở cloud sync, ổ ngoài, máy đồng đội, Kaggle notebook/output hoặc W&B nếu từng dùng. Kiểm chứng bằng hash đã ghi trong audit; lập danh sách recovered/missing, không thay raw evidence bằng số liệu tự dựng.
- [ ] Dựng Python 3.11 và dependencies của nhánh mới trong môi trường riêng, ưu tiên Linux/WSL nếu native `cddlib`/Box2D gây trở ngại. Máy kiểm tra hiện chỉ có Python 3.12.10, chưa có `.venv` hay bộ công cụ kiểm định trên PATH. Chạy harness doctor/status/roadmap và bộ kiểm tra bắt buộc của AGENTS; ghi kết quả mới riêng với hồ sơ 214 tests lịch sử.
- [ ] Đối chiếu hạn nộp/rubric với giảng viên để chốt phạm vi: ưu tiên triển khai tái lập được, controls đúng ngân sách, trình bày kết quả âm Minecart và giới hạn dữ liệu. Nếu chỉ dùng một môi trường hoặc thu hẹp ablation, phải ghi rõ amendment và được chấp nhận; chưa coi đó là đáp ứng proposal hai môi trường.
- [ ] Nếu thiếu dữ liệu buộc phải chạy lại, lập study phục hồi mới với ngân sách hữu hạn, paired seeds và provenance mới. Không trình bày run mới là dữ liệu cũ; không mở lại matrix v1 hoặc tăng seed/tuning để tìm kết quả dương; không dùng final test để lựa chọn.
- [ ] Xác minh đầu ra trước khi nộp: bảng kết quả truy được đến dữ liệu, phần missing evidence minh bạch, demo chạy được trên máy trình bày, báo cáo bám sát kết quả. Nhánh cũ ghi nhận yêu cầu tạm giữ manuscript/TeX/PDF; cần giải quyết yêu cầu đó trước khi chỉnh báo cáo. Chưa có lịch hoàn thành vì chưa biết deadline, rubric và compute khả dụng.

Không chạy training, final evaluation, paid review hoặc chỉnh manuscript trong phiên kiểm kê này. Chỉ thêm tài liệu nên không chạy bộ test cho code; chưa có kết luận môi trường hiện tại chạy được.

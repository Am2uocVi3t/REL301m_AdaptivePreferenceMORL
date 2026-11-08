# Rà soát alignment và mốc khôi phục — 01/11/2026

## Kết luận

Cập nhật sau audit: phần triển khai tiếp theo đã sửa startup Windows, protocol binding/default của evaluator, hard-lock final test, path portability và LF cho hash-bound text. Đã chạy 171 tests (4 skips có lý do), hai smoke train/checkpoint/validation và re-audit thành công 28.800 episode nhúng trong Git. Dữ liệu primary raw/discounted có thể khôi phục từ aggregate JSON; checkpoint cũ vẫn thiếu. Các finding bên dưới ghi nhận trạng thái trước sửa, không phải danh sách mọi lỗi còn mở. Xem `docs/WINDOWS_RECOVERY.md` và `research/qualification/windows_course_recovery_20261101.json` cho bằng chứng mới; baseline contract và RQ1 diagnostics vẫn chưa hoàn thiện.

Snapshot nghiên cứu mới nhất tìm được là `e223362` trên `origin/codex/aris-full-workflow`, 18/10/2026 04:18:58 +07. Code lõi PCQN bám thiết kế v2, nhưng chưa thể gọi toàn bộ pipeline là hoàn chỉnh hoặc thực nghiệm được xác nhận trên máy phục hồi. Có khoảng trống cụ thể về evaluator, baseline, phân tích RQ1 và tính di động Windows. Kết quả thất bại Minecart không tự chứng minh code sai, và code khớp công thức không chứng minh mô hình học được.

Đây là review các luồng nghiên cứu trọng yếu, không phải xác nhận đã review từng dòng của mọi script, ARIS skill hoặc frontend. Không sửa thuật toán, protocol, manuscript hoặc kết quả trong phiên này. Session log, state metadata và handoff được cập nhật qua research harness theo bootstrap; không đổi claim, phase hay qualification.

## Snapshot và khoảng 18–22/10

Người dùng xác nhận sau lượt audit: khoảng 18–22/10 có chỉnh sửa code và chạy thí nghiệm trực tiếp trên laptop bị mất. Vì vậy khoảng thiếu không chỉ là output; có thể gồm cả thay đổi implementation. Chưa xác định các thay đổi đó đã commit hay có backup. Kết luận code alignment trong tài liệu này chỉ áp dụng snapshot `e223362`, không xác nhận phiên bản cuối trên laptop.

- Đã kiểm tra trực tiếp `git ls-remote origin`, sau đó fetch tất cả `refs/pull/*/head` và `refs/pull/*/merge` còn công khai vào remote-tracking refs riêng.
- Không tìm thấy commit có committer date 19–23/10 trong lịch sử các refs đã tải. PR #6 head vẫn là `e223362`.
- Ref merge thử của PR #6 là `2f3629d`, 18/10 04:19:11 +07; đây là synthetic merge, không phải phần nghiên cứu mới ngày 22/10.
- Mốc người dùng nhớ chạm laptop lần cuối 22/10/2026 vẫn có giá trị. Không có commit remote ngày đó không có nghĩa không có công việc ngày đó: có thể là code chưa push, file chưa commit, run/log/checkpoint bị ignore hoặc công việc trên máy từ xa.
- Nhánh local hiện tại: `codex/alignment-audit-20261101`, tạo từ `origin/codex/aris-full-workflow`. `main` được giữ nguyên. Ghi chép recovery trước đó vẫn còn.

## Phạm vi đối chiếu

Đã đọc luồng chính trong `scripts/train.py`, `scripts/evaluate.py`, `scripts/train_baseline.py`, `src/models/{q_network,update}.py`, `src/core/replay_buffer.py`, `src/curriculum/{sampler,gap,uncertainty}.py`, `src/evaluation/{protocol,rollout,metrics,stats,course_matrix}.py`, `src/envs/{wrapper,shift}.py`, và phần runtime demo `src/demo/runtime.py`.

Đã đối chiếu thêm phần source/metadata validation, execution gates và API trong `src/evaluation/{course_validation,course_executor}.py`, `src/baselines/morl_baselines_runner.py`, tests liên quan, proposal v2, architecture, frozen course matrix, hai protocol và F1 amendment/qualification. Review không tái thực hiện raw-result audit vì raw artifacts và checkpoints chưa có.

| Contract | Kết quả đọc code |
|---|---|
| Preference-conditioned vector Q, output K × B × A × D | Khớp network và scalarization; inference dùng ensemble mean khi `head_idx=None` |
| Double-DQN riêng từng head | Khớp online argmax/target gather; chỉ `terminated` tắt continuation |
| Replay giữ behavior preference và bootstrap masks | Có; ít nhất một head được kích hoạt khi tạo mask |
| Rollout/update/both allocation | Có nhánh riêng; uniform rollout dùng cùng fixed finite pool |
| Gap empirical, disagreement, coverage/recency, absolute progress | Có công thức và các đường gọi; chưa chứng minh tính hữu ích hay calibration |
| Return discount và reward scaling | Training/archive/gap/evaluation dùng gamma từ protocol và rewards đã scale |
| Validation/test preference sets | Có generation seeds cố định; training chỉ load validation |
| Provenance và counters riêng | Checkpoint lưu protocol/hash, Git/config, training/update/curriculum/validation counters |
| Course executor và validation audit | Có kiểm hash, budgets và khóa matrix-v1; chặt hơn evaluator tổng quát |
| F1 replay amendment | Eligibility completed episode, softplus label/project finite pool, success mixture và relabel nhất quán với Q/targets được thể hiện trong code |
| Demo | Inference trên cùng model, paired panels và tách RNG; thiếu config/weights/output package để xác minh chạy thật |

## Findings cần xử lý trước một đợt nghiên cứu mới

### 1. [P1] Evaluator tổng quát cho phép final test mà không kiểm checkpoint lock

`scripts/evaluate.py:43` mặc định `--split test`. `main()` load protocol và rollout trực tiếp, không đọc checkpoint-lock/qualification hay kiểm trạng thái final-test. Trong khi đó frozen study yêu cầu `test_once_after_lock` và qualification hiện tại không mở final test. Người dùng chạy lệnh đánh giá thông thường có thể truy cập test quá sớm. Đây là lỗ hổng enforcement ở entry point; không phải bằng chứng test đã bị sử dụng trong các run cũ. Cần default validation và ràng buộc final-test với checkpoint/protocol/lock trong workflow chính thức.

### 2. [P1] Evaluator không đối chiếu protocol của checkpoint

`scripts/train.py:328` lưu cả protocol và hash. `scripts/evaluate.py:108` chỉ kiểm gamma; sau đó áp reward scale, environment và preferences của protocol truyền vào mà không so với checkpoint protocol/hash. Hai protocol cùng dimensions/gamma nhưng khác scale vẫn đi tiếp. Điều đó có thể đổi ý nghĩa trade-off và metric mà không báo lỗi. Course validation riêng có kiểm đầy đủ ở `src/evaluation/course_validation.py:847`; lỗi này thuộc evaluator tổng quát. Cần đối chiếu danh tính protocol hoặc có chế độ cross-protocol riêng được khai báo rõ.

### 3. [P1 khi dùng để so sánh] Baseline runtime qualification chưa phải hợp đồng đánh giá chung

`scripts/train_baseline.py:33` load validation preferences nhưng bỏ matrix nhận được (`protocol, _`). Adapter gọi `agent.train()` của thư viện; không truyền fixed preferences, gamma, train frequency, curriculum/validation step ledger theo cùng hợp đồng PCQN. Manifest chỉ truyền tổng training steps và eval frequency cho baseline. Checkpoint baseline là `final.tar`, trong khi evaluator chung chỉ load PCQN network schema. Có runtime adapter không đồng nghĩa đã có fixed-preference evaluation, ngân sách update/evaluation được đối chiếu, raw returns và checkpoint selection đồng nhất. Cần bổ sung adapter đánh giá/ledger trước khi đưa Envelope/GPI-LS vào bảng so sánh công bằng; chưa kết luận baseline cũ đã tiêu sai một số bước cụ thể.

### 4. [P2] Training không mở được trên native Windows

`scripts/train.py:7` import `resource` vô điều kiện; cuối run gọi `getrusage`. Đã chạy `python scripts/train.py --help` trên Windows và nhận `ModuleNotFoundError: No module named 'resource'` trước khi import dependency ML. Python 3.11 cũng không cung cấp module Unix này trên native Windows. Nếu chọn Linux/WSL cho training thì cần nói rõ môi trường hỗ trợ; nếu hỗ trợ Windows cần fallback đo memory. Demo không import training nên finding này không tự chứng minh demo lỗi.

### 5. [P2] Diagnostics hiện chưa trả lời đầy đủ RQ1

`scripts/train.py:231` định nghĩa progress bằng `abs(current_utility - previous_utility)`, đúng định nghĩa executable/proposal hiện tại nhưng bao gồm cả suy giảm. `scripts/train.py:261` chỉ log lagged correlation cho gap và disagreement với absolute change; không log đủ coverage/recency và previous-progress prediction, signed future improvement hoặc held-out/HV improvement. Với uniform, sampler score arrays còn không được cập nhật bởi `update_distribution`, nên các lagged score correlations đó không có cùng ý nghĩa giữa các arm. Có thể báo đây là diagnostics về độ thay đổi utility; chưa thể kết luận tín hiệu nào dự báo cải thiện hoặc learnability tốt nhất. Cần thu hẹp claim hoặc predeclare phép đo đầy đủ trước study mới.

### 6. [P2] RNG isolation được thêm cho F1 nhưng chưa đồng nhất các entry point

`evaluate_preferences` hỗ trợ `isolate_global_rng`; F1 plan yêu cầu flag này và runtime demo tách global NumPy/Python RNG theo panel vì Minecart dùng global sampling. `scripts/evaluate.py:123` không truyền flag; frozen course commands cũng không bật `--isolate-evaluation-rng`. Vì vậy cùng seed reset chưa đủ để hứa kết quả Minecart giống nhau giữa mọi workflow. Cần đối chiếu lựa chọn RNG trong manifest/checkpoint và evaluator; không tự diễn giải điều này là nguyên nhân ore=0. Không sửa ngược protocol/run cũ.

## Semantics và tài liệu dễ gây hiểu nhầm

- `raw_episode_returns` của evaluator là undiscounted **scaled** returns vì env đã wrap scale; không phải native units. Demo ghi `raw_return` native units riêng, còn training trajectory metadata chia lại scale. Audit F1 đã ghi nhận caveat này. Báo cáo phải chỉ rõ đơn vị, tránh trộn trường cùng chữ raw.
- “Compute-matched” hiện chia lịch diagnostic/episode counts và có counters thực tế; không mặc nhiên bằng nhau về số evaluation environment steps hoặc wall time vì episode length phụ thuộc policy. Phải dùng ledger thực tế khi báo cáo.
- Một số bootstrap/memory line vẫn nói reference point chưa freeze, trong khi hai protocol và freeze record đã có giá trị. Không dùng các dòng tóm tắt cũ thay cho protocol/qualification hiện hành.
- `doctor` kiểm tính hợp lệ của research registries; pass không có nghĩa model/raw artifacts đã phục hồi hay thí nghiệm đã được tái kiểm chứng.

## Kiểm tra đã thực thi trên máy hiện tại

- `research_harness.py doctor`: pass.
- `research_harness.py status` và `roadmap list`: chạy được, phase-4 active; failed F1/matrix/final-test locks vẫn được ghi nhận.
- Parse Python AST cho toàn bộ 90 file `.py` trong `src`, `scripts`, `tests`: pass. Đây là kiểm syntax, không phải test runtime.
- Thực thi riêng parser của evaluator với `argparse` và CUDA-availability stub: xác nhận default split `test` và không có CLI lock artifact. Không load checkpoint, environment hoặc test preferences qua kiểm tra này.
- `node --check demo/interactive/app.js` và `renderer.js`: pass; không phải browser/backend verification.
- `python scripts/train.py --help`: fail vì `resource` như trên.
- `git diff --check`: pass cho tracked diff. Code/config không sửa.
- Không chạy lại pytest/Ruff/MyPy/Bandit/full smoke: máy chỉ có Python 3.12, chưa có NumPy/Torch/Gymnasium/pytest và quality tools. Hồ sơ 214 tests là kết quả lịch sử, không phải xác minh mới. Chưa chạy bất kỳ training hoặc final-test episode nào.

## Quyết định cho mục tiêu môn học

Giữ code lõi làm nền; chưa cần viết lại thuật toán. Thứ tự hợp lý là tìm dữ liệu/công việc 18–22/10 còn lại, dựng môi trường hỗ trợ, sửa evaluator/protocol binding và hoàn thiện gói demo. Sau đó chốt với giảng viên phạm vi báo cáo kết quả âm so với study mới có ngân sách hữu hạn. Không tiếp tục matrix-v1 hoặc tăng tuning Minecart để kiếm kết quả dương. Các kết luận hiện tại chỉ áp dụng snapshot 18/10 đã tìm được, không áp dụng phần việc 22/10 chưa khôi phục.

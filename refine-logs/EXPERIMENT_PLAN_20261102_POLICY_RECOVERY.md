# Preference transfer recovery — kế hoạch đề xuất 02/11/2026

Trạng thái: **đề xuất, chưa dispatch**, `execution_enabled=false`.
Machine-readable: `configs/experiments/preference_transfer_recovery_proposal_v1.json`.
Không sửa hoặc chạy lại F1/matrix cũ. Không truy cập final test.

## Mục tiêu và tiêu chí bác bỏ

H1: khai thác các policy nguồn giảm conditioning gap mà không học thêm.
Bác bỏ tính đủ của H1 nếu approximate GPI không cải thiện task và paired utility.
H2: tái sử dụng transition cho trọng số khác cải thiện preference learning.
H3: scalarized auxiliary TD giúp loss khớp với quyết định utility.
Hai giả thuyết training phải tách bằng 2×2; không kết luận nhân quả từ một arm.
Kết quả hiện tại chỉ ra failure modes, chưa xác nhận H1–H3.

## P1 — Can thiệp inference, không training

- Giữ cả 12 final model, dùng bank 32 trọng số train đã freeze.
- Bốn policy: mean greedy; mean epsilon .05; approximate GPI mean greedy;
  approximate GPI mean epsilon .05. Không chọn head tốt nhất.
- `argmax_a max_w_source mean_head Q(s,a,w_source) dot w_target`.
  Source weight bên trong network; target weight bên ngoài. Không dùng max
  vector từng objective, không thay target weight bằng source weight.
- Hai task preference gốc mỗi môi trường, 10 env seed mới 20263101–110:
  **960 episode, tối đa 960.000 bước**, 0 update. Cùng seed/reset và các stream
  exploration/action giữa policy, kiểm tra trace; không pooling control lặp.
- Gate triển vọng: ít nhất 8/10 task success ở mỗi task-oriented profile,
  **mọi training seed**, cùng paired utility tốt hơn plain mean. Báo cáo riêng
  hai n-step arms; không lấy seed/head đẹp đại diện.

Nếu có lợi ích chỉ ở vài profile, báo cáo đúng phạm vi. P1 thất bại không chứng
minh định lý GPI sai vì critic của ta không có bound hiệu chuẩn.

## P2 — Chỉ khi P1 chưa đủ: 2×2 Minecart

| Arm | Trọng số dùng update | Loss |
|---|---|---|
| A | stored behavior weight | vector Huber |
| B | uniform counterfactual từ cùng pool | vector Huber |
| C | stored behavior weight | .5 vector Huber + .5 scalar TD Huber |
| D | uniform counterfactual từ cùng pool | cùng hybrid loss C |

Ba paired seed mới 20263211–213, n=1, 500k/job: **12 job, 6M tương tác,
1.485.012 update**. Một weight cho mỗi replay row; tính lại DDQN target theo
weight đó; không tăng số update, không thêm PER/projection. Scalar TD là
`w dot (target_vector - Q_vector)` trước Huber; mask head áp dụng nhất quán.
Hệ số .5 là lựa chọn cố định để kiểm chứng, không phải kết quả tuning.

Các setting chung và stream RNG độc lập ghi trong JSON. Qualify endpoint n=1
control, mask/loss/target, finite CUDA và exact boundary resume trước dispatch.
Luôn lưu vector raw/discounted, scale, action/task trace và source/checkpoint
hash. Canary chỉ kiểm chứng kỹ thuật, không dùng thành công/thất bại của nó
để bỏ seed khác hoặc đổi budget.

Checkpoint 100k/250k/500k chỉ theo dõi; quyết định bằng **500k cuối**.
Validation: 32 preference ×3 episode ×3 checkpoint ×12 job = **3.456 episode**,
tối đa 3.456.000 bước; task final hai profile ×10 case ×12 job = **240 episode**,
tối đa 240.000 bước. Dev task seed 20263231–240, tách P1 và confirmation.
Training, update, validation, task và engineering budget ghi riêng; curriculum
evaluation = 0 trong P1/P2. Không đánh giá final test.

Gate: giao quặng ít nhất 8/10 ở cả hai task preference, mọi seed; cải thiện
paired utility so với A. Báo cáo interaction effects của 2×2 và cả failure.
Với n=3, coi phân tích estimation-first: hiển thị từng seed/difference, range
và bootstrap interval có cảnh báo bất định; không dựa vào p-value để thắng.
Ưu tiên B hoặc C nếu đủ, không mặc định D phức tạp hơn. Nếu tất cả fail, dừng
study, không tăng bước cho đến khi thắng; đề xuất phương pháp khác riêng.

## P3 — Xác nhận độc lập trước khi gọi là thành công

Freeze một method sau P1/P2, không lựa chọn bằng confirmation. Dùng 32 trọng
số Dirichlet mới (seed 20263421), anchors tách riêng, 10 env seed 20263431–440.
Đây là development confirmation, không mở lại final test gốc.
Nếu inference-only đủ, chỉ evaluate checkpoint cũ; không train mặc định.
Nếu cần method training: control và selected, hai môi trường, ba paired seed
20263311–313, 500k/job: **12 job/6M tương tác**. Trước dispatch phải freeze
qualification receipt, profile cụ thể và evaluation matrix/hash riêng; chưa
đủ chi tiết để coi P3 là executable protocol hiện tại.

Yêu cầu task-oriented profiles đạt 8/10 mọi seed, báo cáo EU/HV cùng native
trade-off và coverage. Không suy ra dynamics generalization. Chỉ tuyên bố
coverage trên phân phối đã kiểm tra, không “parameter bất kỳ đều tốt”.

## P4 — Chỉ nếu muốn giữ claim adaptive allocation

Sau backbone đủ năng lực, freeze study mới: uniform, compute-matched random,
adaptive joint ×3 paired seed ×2 môi trường ×500k = **18 job/9M tương tác**.
Freeze riêng tuning/update/curriculum-evaluation budgets và protocol trước khi
chạy. Không dùng thành công P1/P2 thay bằng chứng adaptive tốt hơn baseline.
Nếu phạm vi môn chỉ là phân tích và sửa backbone, báo cáo thu hẹp rõ và giữ
research question adaptive ở trạng thái chưa trả lời.

Tổng 21M training là **trần nếu mọi nhánh training được kích hoạt**, không phải
queue được chạy hết. Bước ngay tiếp theo chỉ là P1 sau khi hiện thực và qualify
runner theo bản freeze riêng. Mọi compute lưu trên D:. Không cloud trả phí,
unattended dispatch hoặc mở gate cũ từ tài liệu đề xuất này.

## Nguồn và quyết định

Xem `docs/research/ROOT_CAUSE_ANALYSIS_20261102.md` và full-text notes của
Osband 2016, Alegre 2023, Yang 2019 Envelope, Terekhov 2024. GPI và Envelope
động viên thiết kế; không paper nào chứng minh các setting mới tối ưu cho repo.
Protocol implementation/review phải xác nhận lại tính khả thi trước dispatch.

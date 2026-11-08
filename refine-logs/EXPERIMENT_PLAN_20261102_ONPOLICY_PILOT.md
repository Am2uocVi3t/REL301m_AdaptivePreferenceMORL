# Đề xuất mới: kiểm chứng backbone on-policy sau P2

Trạng thái: **đề xuất; chưa triển khai/dispatch training**. Không mở rộng P2.
Machine-readable: `configs/experiments/onpolicy_backbone_pilot_proposal_v1.json`.

Cập nhật triển khai sau đề xuất: F0 đã được kiểm chứng và S có executable riêng
`configs/experiments/minecart_onpolicy_specialist_v1.json`; đọc contract
`docs/research/ONPOLICY_IMPLEMENTATION_V1.md` cho các quyết định đã đóng băng,
đặc biệt scalarization giữ utility gốc thay vì chia sigma từng objective.
JSON đề xuất cũ giữ execution=false để không biến C/G thành queue ngầm.

## Câu hỏi và giả thuyết

Policy greedy Q-learning không thể hiện nhiệm vụ dù training có reward; relabel
và auxiliary loss không cứu được. Trước khi quay lại allocation, cần một
backbone có thể học navigation/mining/delivery đáng tin cậy.

- H-S: một actor PPO học policy task-oriented dưới utility cố định được không?
- H-C: nếu specialist học được, conditional actor còn học được khi phải chia
  cùng ngân sách cho32 preference không?
- H-G: kết quả của conditional actor có lặp lại ở training seed và preference mới?

Một pass không chứng minh PPO tối ưu, entropy là nguyên nhân duy nhất, hoặc
adaptive sampling hữu ích. Một specialist fail thì chưa có cơ sở đổ lỗi cho
preference conditioning. Cả sampled policy và argmax phải được đánh giá riêng.

## F0 — Source/implementation qualification, trước main run

Giữ geometry, gamma, reward scale, reference point và horizon1000 của protocol
hiện tại. Mô hình mới có categorical actor và vector state-value critic;
không dùng ensemble max-Q để quyết định policy. Tách source/runtime mới, giữ
toàn bộ artifact P2. Đọc author implementation pinned và map từng setting từ
paper/default sang bản chạy; các mismatch đã ghi trong báo cáo P2.

Candidate cố định: width256, actor/critic tách riêng, actor LR3e-4 và critic
LR3e-4, clip.2,4 epoch,8 minibatch, PopArt.001; entropy target linear từlog(6)
đến.4, initial multiplier.01, damping.01 và multiplier LR actorLR/10. Đây là
**một candidate đề xuất**; LR/architecture không được chứng minh tối ưu.
Không sweep và không gọi đây là reproduction đầy đủ.

Rollout candidate:8 stream ×64 step =512 samples/update round; final partial
round phải giữ đúng4M interaction. Preference cố định trong episode, không đổi
giữa fragment. Trước dispatch, phải freeze số update actor/critic, cách xử lý
partial minibatch, TD(1)/bootstrap ở fragment và time-limit, masked reset và
việc khôi phục trạng thái tám môi trường. Các chi tiết này hiện **chưa qualified**.
Không chuyển thành executable protocol khi còn thiếu chúng. Native terminal
phải nhận diện cohort mới trước dispatch, không tiếp tục hiển thị P2 thay cho PPO.

Test có ý nghĩa: clipped ratio so với policy tại collection; gradient đúng
đối với vector advantage; PopArt đổi statistics nhưng giữ denormalized output;
không truyền bootstrap qua preference/reset khác; log-prob/entropy hữu hạn;
eval không làm thay đổi RNG training; I/O contention và exact-resume trên
rollout/episode boundary có qualification. Engineering budget tối đa50k tương
tác, tính riêng; không phải task evidence. Cần throughput đo trên máy này,
không lấy thời gian V100 của paper làm ETA laptop.

## S — Specialist feasibility pilot

Một seed mới20264111, preference `[.45,.45,.1]`,4M training interaction cố định.
Milestone500k/1M/2M/4M chỉ mô tả; gate bằng **4M cuối**. Mười development env
seed20264121–130, sampled và argmax riêng, cả hai profile task cũ. Target chính
của specialist là profile nó được train. Success: ít nhất8/10 deliveries và
utility trung bình cao hơn idle tại profile đó. Argmax fail thì không có claim
deterministic demo; sampled-only pass phải gọi đúng là stochastic competence.

Nếu specialist fail: dừng nhánh này ở4M, kiểm tra code/trajectory/optimizer;
không tự chuyển sang conditional hoặc tăng bước. Nếu pass: freeze phần còn lại
của protocol trước bước C; không sửa hyperparameter theo milestone đẹp.

## C — Conditional pilot, chỉ khi S pass

Cùng candidate và seed20264111,4M interaction, episode weight uniform từ đúng
32 training preferences cũ. Không warm-start từ specialist, không dùng demo
trajectory hay replay augmentation. Đây là kiểm tra khả năng mang nhiều
preference của cùng learner, không comparison với historical P2 ở matched budget.
Freeze sampled/argmax evaluation trên cả hai task profile và32 validation
preferences. Gate task:8/10 mỗi profile và utility cao hơn idle; không chỉ HV.

S+C tối đa8M main-pilot interactions, conditional, không phải queue được chạy
hết. Validation/task, optimizer updates và engineering phải có counter riêng.
Candidate evaluation ceiling10k episode /10M step cho cả pilot phải được chia
thành matrix chính xác trước dispatch; không đánh giá theo hứng đến khi tốt.

## G — Confirmation, chỉ sau conditional pilot pass

Ba fresh training seed20264311–313, cùng4M/job (tối đa12M), method freeze trước
khi chạy.32 preference Dirichlet mới, seed20264421, anchors tách riêng;
10 dev env seed20264431–440. Đây không phải test split gốc. Báo cáo từng seed,
EU/HV/native trade-off, sample/argmax riêng. Không chọn mode hay model bằng
confirmation. Giữ gate8/10 mọi seed tại task profiles; không seed replacement.
Nếu có seed fail, không có claim ổn định mọi seed. Matrix/budget evaluation
cụ thể còn phải freeze; giai đoạn này hiện chỉ là conditional design.

Trần training nếu mọi nhánh kích hoạt là20M + tối đa50k engineering; không phải
ngân sách đã dispatch. Giữ scope report là backbone competence/preference
response. Allocation benefit cần study uniform/random/adaptive riêng, dynamics
generalization cần protocol khác. Không có cam kết “mọi parameter đều tốt”.

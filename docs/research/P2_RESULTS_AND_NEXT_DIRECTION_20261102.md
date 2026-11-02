# P2 hoàn tất: kết quả, giới hạn và hướng tiếp theo

## Kết luận

**Thí nghiệm chạy xong, nhiệm vụ chưa học đạt yêu cầu.** Cả 12 job đã chạy đúng
500k tương tác/job. Audit số liệu, source, trace và I/O amendment qua; chín job
trước đó được giữ nguyên, ba job cuối hoàn tất với runtime receipt đầy đủ.
Không có arm nào đạt gate. Đây là kết quả âm có giá trị về tính đủ của hai
can thiệp trong cấu hình này, không phải bằng chứng rằng mọi dạng relabel hay
auxiliary loss đều vô ích.

Evidence đầy đủ: `research/evidence/preference_recovery_p2_v1.json`.
Phân tích tái tạo: `scripts/summarize_p2_findings.py` và
`research/evidence/preference_recovery_p2_findings_v1.json`.
Hình: `outputs/p2-findings-20261102/p2_findings.png` và bản PDF.
Review hiện tại là **executor-only**, chưa có semantic-review PASS độc lập.

## Ngân sách và kết quả chính

- Training: **6.000.000** tương tác logic, **1.485.012** gradient updates.
- Validation: **3.456 episode /3.097.203 bước**, ba checkpoint cố định.
- Task diagnostic cuối: **240 episode /240.000 bước**.
- Final test: **0 bước**. Không chọn lại checkpoint, seed hoặc reference point.
- IO engineering108k và các engineering/interruption trước đó tính riêng.
  Tails phải replay do các lần dừng được giữ trong các receipt interruption,
  không tính thành seed hay tương tác logic mới. Ba segment I/O cuối ghi0 retry;
  điều này xác nhận chúng hoàn tất, không chứng minh khóa file không thể tái diễn.

| Arm | Can thiệp | EU cuối, mean ± sample SD qua3 seed | Paired delta so A | Giao quặng cuối |
|---|---|---:|---:|---:|
| A | stored weight + vector Huber | −.6240 ± .0518 | — | 0/60 |
| B | uniform relabel + vector Huber | −.6436 ± .0376 | −.0196 | 0/60 |
| C | stored weight + auxiliary utility loss | −.5511 ± .1414 | +.0730 | 0/60 |
| D | relabel + auxiliary loss | −.5662 ± .1141 | +.0578 | 0/60 |

Mỗi arm gồm3 training seed ×2 profile ×10 environment case. Các case không
phải60 training replicates độc lập. B/C/D mỗi arm có2/3 seed EU cao hơn A,
nhưng seed còn lại giảm; không dùng n=3 để tuyên bố significance hay superiority.
Các factorial effects từng seed đều được giữ trong evidence; không che seed xấu
bằng mean. C có một seed tốt hơn về EU, nhưng vẫn không có quặng.

## Quan sát mới làm thay đổi cách giải thích

**1. Policy cuối không đào.** Không có quặng trong cả 1.152 episode validation
cuối, và cũng không có quặng trong toàn bộ 3.456 episode tại100k/250k/500k.
Trong 240 trace nhiệm vụ cuối, hành động Mine được chọn **0 lần** trên240.000
bước. Hành động tập trung vào quay, phanh và None; accelerate chỉ50 lần.
Các case cuối đều chạm time limit1000. Không nên gọi chung là “quay về base rỗng”:
ví dụ A seed11 thực hiện None1000 bước. Khác biệt utility/HV cuối hoàn toàn nằm
ở fuel vì cả hai thành phần ore đều bằng0.

**2. Training có reward, nhưng chất lượng trajectory không đồng đều.**

| Arm | Episode training có quặng / episode hoàn tất | Trong số episode có quặng, utility tốt hơn idle tại `[.45,.45,.1]` |
|---|---:|---:|
| A | 889/4314 | 221/889 |
| B | 852/4278 | 221/852 |
| C | 1329/5574 | 368/1329 |
| D | 971/5039 | 254/971 |

Tổng có 4.041 behavior episode có quặng, 1.064 trong số đó tốt hơn baseline idle
ở profile cân bằng. Phần lớn episode có quặng vẫn thua idle; median độ dài của
nhóm này khoảng210–218 bước, làm chi phí nhiên liệu và discounted credit trở
nên quan trọng. Đây là chấm lại các trajectory đã quan sát, không phải chứng
minh một policy greedy đã thành công và không phải phép thử độc lập với4041 mẫu.

**3. Những giả thuyết nào còn đứng vững?** Thiếu reward hoàn toàn bị loại;
“thêm relabel/loss này là đủ” bị bác bỏ trong screen này. Collapse của greedy
control được quan sát trực tiếp. Vai trò nhân quả riêng của bootstrap, exploration,
architecture hoặc ngân sách chưa được tách đủ. Không được suy “PPO chắc chắn sửa
được” từ kết quả âm của Q-learning. Những can thiệp PER/F1/n-step/GPI đã có kết
quả riêng; không chạy lại chúng hoặc kéo dài P2 đến khi thắng.

## Hướng ưu tiên và căn cứ nguồn

Tôi ưu tiên **kiểm chứng actor–critic on-policy với kiểm soát entropy**, trước
hết ở một preference cố định. MOPPO đã nghiên cứu stochastic Minecart; paper
báo cáo collapse khi exploration entropy quá thấp. Đây là động cơ thử một
backbone khác, không phải kết luận cho repo này. Nguồn chính:
[Terekhov & Gulcehre, §5.2/6.2, Table2](https://arxiv.org/html/2407.16807v1).

Phải phân biệt paper và mặc định code. Paper dùng4M interaction; P2 chỉ500k/job,
nên một pilot mới4M không phải so sánh công bằng với P2. Paper Table2 ghi
entropy minimum .4, damping .01, PopArt rate .001. Author defaults đã lưu tại
commit `c568cb6d689d7eaa50a2dec38197de8847f18adc` có lần lượt .1/.05/.01;
`minecart.yaml` giới hạn192 bước, `minecart_long.yaml`1000. Không được nạp default
rồi gọi là reproduction. Base config mặc định chọn Deep Sea Treasure và có thể
được Hydra override; các khác biệt này không chứng minh paper đã chạy sai setting.
Source config được fetch lại công khai và khớp bản
đã lưu: [author repository](https://github.com/CLAIRE-Labo/tunable-morl-public).

PCN cũng không phải một tên khác của PCQN: nó condition theo return/horizon và
học từ trajectory. Các giả định về stochasticity và khác biệt discount làm nó
không phải lựa chọn thay thế nguyên xi ở đây:
[PCN, AAMAS2022](https://aamas.csc.liv.ac.uk/Proceedings/aamas2022/pdfs/p1110.pdf).

Kế hoạch mới: `refine-logs/EXPERIMENT_PLAN_20261102_ONPOLICY_PILOT.md` và
`configs/experiments/onpolicy_backbone_pilot_proposal_v1.json`. Chưa dispatch
training mới. Specialist trước, conditioned sau, rồi xác nhận bằng3 seed mới
nếu đủ năng lực; đó là lộ trình kiểm chứng, không lời hứa đạt parameter bất kỳ.
P3/P4 cũ không tự mở vì P2 đã fail. Claim adaptive allocation vẫn cần đối chứng
uniform và compute-matched random trong study được freeze riêng.

## Điều kiện báo cáo môn

Có thể đưa kết quả âm này vào report như một phân tích thực nghiệm có kiểm soát,
nhưng chưa trình bày dự án như một adaptive learner đã hoàn thành nhiệm vụ.
Tách rõ engineering chạy ổn, chất lượng policy, preference generalization và
environment generalization. Chỉ thay model demo sau khi model mới có task evidence.

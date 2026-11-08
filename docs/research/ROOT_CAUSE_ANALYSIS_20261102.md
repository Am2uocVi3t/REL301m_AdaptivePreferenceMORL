# Chẩn đoán kết quả và hướng cải thiện — 02/11/2026

## Kết luận có thể bảo vệ

Pipeline chạy xong không đồng nghĩa với model học xong. Đợt training 12 job,
6 triệu tương tác đã hoàn tất nhưng không qua các gate nhiệm vụ. Đợt chẩn đoán
mới dùng đúng 12 checkpoint cuối, không chọn seed/checkpoint tốt nhất: 3.720
episode, 2.045.511 bước môi trường, **0 training/update/final-test**. Toàn bộ
240 trường hợp nhiệm vụ cũ được tái lập; trace được kiểm tra hash, vector return,
discount, scale và hành động. Không có bằng chứng lỗi đọc checkpoint hoặc tính
return giải thích các thất bại này. Audit hiện do executor thực hiện, chưa phải
review độc lập về ngữ nghĩa nghiên cứu.

Evidence máy đọc: `research/evidence/policy_extraction_diagnosis_v1.json`.
Protocol: `configs/experiments/policy_extraction_diagnosis_v1.json` và phần phân
tích đăng ký trước khi đọc kết quả mới trong `policy_extraction_analysis_v1.json`.
Hình: `outputs/policy-extraction-diagnosis-v1/policy_extraction_heatmaps.png`.

## Những gì thực sự xảy ra

| Kiểm tra | Kết quả | Giới hạn kết luận |
|---|---|---|
| Minecart, hai trọng số hỗn hợp | Cả 6 model: mean, từng head và voting đều 0/10 giao quặng tại mỗi trọng số | Gộp head không phải lời giải thích duy nhất; voting không cứu được nhiệm vụ |
| Minecart, ưu tiên riêng ore1 `[1,0,0]`, n=20 | Mean greedy: 10/10, 0/10, 0/10; mean + epsilon .05: 10/10, 8/10, 10/10 | Có kỹ năng cục bộ; chưa tổng quát sang trọng số hỗn hợp |
| Minecart random | 8/10 giao quặng trên cùng 10 case | Các hàng random lặp lại cùng case, không phải nhiều mẫu độc lập; đếm giao quặng chưa đủ chứng minh học tốt |
| Lunar, landing-heavy, n=1 | Mean pad success 1/10, 1/10, 4/10 | Không đạt 8/10 mọi seed; khác bộ case chẩn đoán cũ |
| Lunar, landing-heavy, n=20 | Mean pad success 0/10 cả ba seed | Không có cải thiện ổn định từ n-step dài |
| Lunar heuristic cố định | Native +100: 9/10, đúng pad: 6/10 | Môi trường có thể điều khiển được; controller tham chiếu cũng chưa qua gate pad |

Epsilon cứu một số policy ở trọng số thuần ore1 nhưng không cứu ổn định các
trọng số hỗn hợp. Ngay tại ore1, n=20 seed 12 có mean utility .112 với epsilon,
thấp hơn random .138 trên cùng case. Không thể quảng bá epsilon là giải pháp
đã thành công toàn diện.

## Nguyên nhân quan sát được và giả thuyết còn phải kiểm chứng

**1. Policy tất định bị kẹt là hiện tượng quan sát trực tiếp.** Với case
20262101, ore1, n=20 seed 12 dùng accelerate 992/1000 bước, đứng ở góc; seed 13
brake 990/1000 bước, đứng ngoài mỏ. Epsilon .05 trên cùng case thoát và giao
quặng trong 212 và 89 bước. Điều này giải thích thất bại của các rollout đó,
không chứng minh một nguyên nhân training duy nhất.

**2. Reward hiếm và critic chưa khớp tốt, nhưng thiếu reward không phải toàn bộ
vấn đề.** Replay cuối n=1 chỉ có 12, 9, 10 cửa sổ reward quặng dương trên
200.000 transition. n=20 giữ 11.361, 8.490, 11.004 cửa sổ dương mà vẫn thất bại
ở trọng số hỗn hợp. Đây là cửa sổ n-step chồng lấn, không phải số lần giao quặng
độc lập. Mask của head không loại hết tín hiệu dương. TD error ở nhóm dương lớn
hơn nhóm zero; không suy từ TD nhỏ ra policy tốt. PER/F1 cũ đã thất bại, nên
không lặp lại retention/PER mà không có giả thuyết mới.

**3. Conditioning chưa tận dụng được một policy tốt đã tồn tại.** n=20 seed 11
ở ore1 có vector discounted-scaled trung bình
`[.79927013, .06816634, -1.87585830]`. Chấm lại vector này bằng trọng số
`[.45,.45,.1]` được **+.20276**, trong khi policy trực tiếp ở trọng số đó đạt
**−.19610**: chênh lệch thực nghiệm khoảng **.39886**. Vì thế chỉ nói “model
tiết kiệm nhiên liệu là hợp lý” không giải thích được checkpoint này. Đây là
chênh lệch giữa các policy quan sát, trung bình 10 case, không phải optimal
regret hay kết quả mọi seed.

**4. Q dự đoán chưa được hiệu chuẩn theo hành vi thực tế.** Tất cả 18 policy
từng head greedy đều không có ore1 trong các case thuần ore1, dù giá trị scalar
ban đầu dự đoán dương. Chênh dự đoán–return trung bình dương khoảng .223–.566
ở n=20. Điều này ủng hộ việc kiểm tra critic/conditioning; chưa xác nhận sửa
loss hoặc relabel chắc chắn sẽ giải quyết được.

## Liên hệ paper và lựa chọn can thiệp

Bootstrapped DQN lấy một head mỗi episode khi train; bản supplement dùng voting
để đánh giá Atari. Chẩn đoán của ta đã thử cả head và voting, do đó không được
suy “làm đúng voting là xong”. Đây cũng không phải reproduction Atari:
[Osband et al., main + supplement](https://papers.neurips.cc/paper_files/paper/2016/file/8d8818c8e140c64c743113f563cf750f-Paper.pdf).

GPI cung cấp phép chọn hành động theo nhiều policy nguồn. Với conditional Q,
source weight đi **vào network**, target weight dùng **scalarize phía ngoài**
(Alegre et al., Eq. 11). Điều này phù hợp với counterexample conditioning trên.
Q của ta chưa có sai số được chứng nhận, và mean head chưa được chứng minh là
Q của mean-greedy policy, nên phép áp dụng tiếp theo chỉ là **approximate GPI
heuristic**, không thừa hưởng bảo đảm đơn điệu:
[AAMAS 2023, pp. 2005–2008](https://www.ifaamas.org/Proceedings/aamas2023/pdfs/p2003.pdf).

Loss bổ trợ scalarized TD lấy động cơ từ Envelope; phiên bản Huber, hệ số .5
cố định là can thiệp mới của ta, không phải default được paper chứng minh tối
ưu. Giữ vector loss để không chỉ học một utility. Counterfactual relabel dùng
n=1 để tránh thêm vấn đề off-policy từ đoạn n=20. Không thay reward scale,
reference point, hoặc checkpoint theo kết quả.

## Quyết định tiếp theo

Xem `refine-logs/EXPERIMENT_PLAN_20261102_POLICY_RECOVERY.md`: thử inference
không train trước, sau đó mới thí nghiệm nhân tố 2×2 có ngân sách hữu hạn nếu
cần. Chỉ chấp nhận cải thiện khi task và utility cùng đáp ứng trên mọi seed,
rồi xác nhận bằng case mới. Chưa có training mới được dispatch từ kế hoạch này.

Không thể hứa đáp tốt với mọi parameter hoặc mọi trọng số liên tục. Báo cáo cần
phân biệt preference coverage, task competence và dynamics generalization;
trọng số thuần fuel có thể hợp lý khi không đi đào quặng. Adaptive allocation
chỉ được tuyên bố hữu ích sau so sánh uniform/random compute-matched riêng.

## Provenance và giới hạn

Một worker có `git_dirty=true` vì hai file hậu xử lý chưa commit, không phải
actor đang chạy bị sửa. Giữ nguyên cờ và dữ liệu; receipt
`research/qualification/policy_extraction_source_context_v1.json` ghi rõ các
file và kiểm tra canonical source actor khớp dispatch commit. Receipt không
phải lịch sử giám sát filesystem đầy đủ. 40 episode qualification trước cohort
và 23.217 bước engineering được tính riêng, không cộng vào 3.720 episode.
Original matrix/F1/final-test tiếp tục bị khóa; không đổi claim cũ thành đạt.

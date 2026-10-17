# Memo điều tra thất bại Minecart PCQN

Ngày: 17-10-2026  
Trạng thái: điều tra hữu hạn, chỉ đọc; **không** phải kết quả remediation v3 hay quyền chạy mới  
Evidence machine-readable: `research/evidence/minecart_failure_investigation_20261017.json`

## Kết luận ngắn

Giả thuyết có căn cứ nhất hiện nay là **backbone PCQN một bước không chuyển và giữ ổn định tín dụng của trajectory ore dài, thưa thành hành vi greedy theo preference**, chứ không phải môi trường không phát ore, sai reward scale, thiếu hẳn exploration, hay lỗi riêng của một allocation arm.

Minecart chỉ phát ore sau chuỗi rời base → điều hướng → dừng gần mine → `Mine` → quay về base, trong khi fuel cost xuất hiện ngay. Dữ liệu hiện có cho thấy:

- tất cả 15 primary run và cả 3 seed PER-v2 đều từng tạo trajectory có ore trong training archive;
- primary greedy validation vẫn zero ore ở 14.400 episode, với 92,42% timeout; probe 345.417 quyết định không chọn `Mine` một lần nào;
- v1 đôi lúc acquire được hành vi (seed `20264003`, checkpoint 600k: 35 mining, 27 delivery/160 episode) rồi mất ngay ở 700k và vẫn mất tại 1M;
- proportional TD-error PER v2 được source-audit đúng cấu hình nhưng 30/30 checkpoint và 4.800 greedy-validation episode đều zero ore;
- offline extraction mới, không rollout, xác nhận final archive v2 vẫn có lần lượt 21/22, 34/35 và 17/18 điểm dương ở ít nhất một ore objective. Vì archive là lịch sử tích lũy, đây là bằng chứng acquisition trong exploration, không phải retention của current policy.

Vì vậy PER-v2 falsify mệnh đề hẹp “proportional one-step TD-error replay là đủ”. Nó **không** falsify mọi cơ chế retention: v2 không ưu tiên complete successful trajectory, không relabel preference theo achieved return, và vẫn dùng one-step Double-DQN target.

## Evidence-to-hypothesis

| Giả thuyết | Trạng thái | Bằng chứng chính | Điều chưa biết |
| --- | --- | --- | --- |
| Ore reward channel hoặc wrapper/replay/archive bị hỏng | Đã loại trừ như giải thích tổng quát | 15/15 primary selected checkpoint và 3/3 v2 seed có positive ore trong training archive; cùng frozen scale dùng ở train/validation | Scale nhất quán chưa có nghĩa là tối ưu cho học |
| Reward scaling chỉ sai ở validation | Đã loại trừ | Raw lẫn discounted ore đều zero; scale được bind bởi protocol/source audit | Dense fuel vẫn có thể lấn tín dụng delayed ore dù scale đúng |
| Lỗi riêng allocation arm/seed | Đã loại trừ cho primary block | Uniform, matched-random, full đều fail trên 5 paired seeds | Không suy rộng sang mọi allocator tương lai |
| Lỗi plumbing state/preference/action/terminal cơ bản | Không thấy bằng chứng | Network nối `[state, preference]`; replay giữ behavior preference; `Mine` là action 0 nên tie của `argmax` không né Mine; terminated/truncated tách riêng và có invariant tests | Không loại trừ giới hạn function approximation hoặc lỗi chưa quan sát |
| Ensemble mean triệt tiêu một head tốt | Đã loại trừ tại 3 primary probe; chưa rõ cho v2 | Ensemble mean và từng head đều không chọn Mine trong 345.417 decision | V2 chưa có head-specific behavior probe |
| Không bao giờ khám phá được ore | Bị phản chứng | Positive ore training archive xuất hiện ở mọi nhóm đã audit, kể cả v2 từ checkpoint sớm | Archive không cho biết transition còn trong replay hay policy hiện tại giữ hành vi |
| Uniform replay làm mất transition hiếm | Hỗ trợ một phần, nhưng remedy hẹp đã fail | V1 có acquisition rồi loss; exact proportional PER-v2 vẫn zero ore toàn bộ checkpoint | Không có log replay composition/sampling theo ore event, nên chưa biết PER tăng exposure thực tế bao nhiêu |
| One-step delayed credit + preference/trajectory misalignment | **Giả thuyết dẫn đầu, chưa chứng minh nhân quả** | Chuỗi reward dài; trajectory dương không thành greedy behavior; Uniform-PCQN update theo behavior preference; one-step target; plain PER không đủ | Chưa chạy n-step, return-conditioned, envelope hay achieved-return preference replay trong study này |

## Đối chiếu primary literature

1. **Abels et al. (ICML 2019), _Dynamic Weights in Multi-Objective Deep Reinforcement Learning_.** Mạng Q nhận dynamic weight và Diverse Experience Replay chia sẻ kinh nghiệm qua preferences; paper có Minecart rời rạc. Remediation v1/v2 của repo dùng Uniform-PCQN và update mỗi transition bằng `behavior_preference`, nên chưa thực hiện DER. Tuy nhiên cùng tên Minecart không bảo đảm cùng geometry/budget, và DER không tự tạo trajectory hiếm. Nguồn: [PMLR](https://proceedings.mlr.press/v97/abels19a.html), note `research/literature/notes/abels2019dynamic-weights.md`.

2. **Shianifar, Schukat và Mason (author-posted 2026; tác giả ghi accepted AICS 2025), _Hindsight Preference Replay Improves Preference-Conditioned Multi-Objective Reinforcement Learning_.** HPR relabel replay sample bằng preference suy từ achieved vector return, giúp tái sử dụng dữ liệu qua simplex. Đây là cơ chế gần nhất với code gap hiện tại, nhưng thí nghiệm thuộc CAPQL/continuous-control và không chứng minh sửa delayed Minecart credit. Nguồn: [arXiv](https://arxiv.org/abs/2601.11604), note `research/literature/notes/shianifar2026hpr.md`.

3. **Yang, Sun và Narasimhan (NeurIPS 2019), _A Generalized Algorithm for Multi-Objective Reinforcement Learning and Policy Adaptation_.** Envelope Q-learning tối ưu qua candidate value vectors/preferences và tái dùng transition với sampled preferences; khác target hiện tại chỉ `argmax` action theo preference đang truyền vào. Paper hỗ trợ một backbone value-based thay thế, không chứng minh riêng sparse-reward Minecart. Nguồn: [NeurIPS](https://papers.nips.cc/paper_files/paper/2019/hash/4a46fbfca3f1465a27b210f4bdfe6ab3-Abstract.html), note `research/literature/notes/yang2019envelope.md`.

4. **Alegre et al. (AAMAS 2023), _Sample-Efficient Multi-Objective Learning via Generalized Policy Improvement Prioritization_.** GPI-LS ưu tiên weights dựa trên GPI bound và GPI-PD ưu tiên model-generated experience. Đây là antecedent quan trọng cho allocation, nhưng cần một repertoire policy/Q đáng tin; nó không tự giải quyết sparse acquisition khi base learner không hình thành policy ore. Existing 200-step GPILS smoke chỉ chứng minh runtime, không phải performance. Nguồn: [AAMAS paper](https://www.ifaamas.org/Proceedings/aamas2023/pdfs/p2003.pdf), note `research/literature/notes/alegre2023gpi-prioritization.md`.

5. **Reymond, Bargiacchi và Nowé (AAMAS 2022), _Pareto Conditioned Networks_.** PCN học supervised policy theo desired return và remaining horizon từ archive trajectory không bị trội. Cơ chế này trực tiếp giữ lại trajectory thành công, nhưng `ParetoArchive` hiện chỉ lưu return vector + metadata, không lưu trajectory/return-to-go. Đây là pivot lớn, không phải chỉnh replay nhỏ. Nguồn: [AAMAS paper](https://www.ifaamas.org/Proceedings/aamas2022/pdfs/p1110.pdf), note `research/literature/notes/reymond2022pcn.md`.

## Tối đa ba hướng giải pháp

### 1. Trajectory-aware hindsight/diverse preference replay — ưu tiên đề xuất

Thay vì chỉ ưu tiên transition có TD error lớn, lưu outcome/return-to-go của episode thành công và relabel transition bằng preference phù hợp với achieved vector return, với update budget giữ nguyên. Hướng này được Abels 2019 và HPR 2026 hỗ trợ ở mức cơ chế chia sẻ dữ liệu qua preference.

Trade-off: đây là thay đổi nhỏ nhất còn gắn trực tiếp với code gap, nhưng vẫn cần trajectory metadata mới và có thể không đủ cho delayed credit. HPR 2026 không phải bằng chứng trực tiếp trên Minecart/PCQN. Mọi implementation/training cần versioned amendment và supervisor approval.

### 2. Envelope Q-learning làm Minecart backbone

Thay one-step same-preference target bằng envelope value update để trajectory khám phá dưới một preference có thể hỗ trợ preference khác. Hướng này gần kiến trúc discrete value-based hiện tại hơn PCN và có primary evidence mạnh từ NeurIPS 2019.

Trade-off: đây là thay backbone và objective, không còn là remediation v3 một yếu tố. Existing Envelope smoke chỉ chứng minh integration. Cần study mới, fairness qualification và matched budgets.

### 3. Return-and-horizon conditioned trajectory archive kiểu PCN

Giữ full successful trajectories và học supervised policy conditioned theo attainable return/horizon. Hướng này nhắm trực tiếp retention và moving-target instability.

Trade-off: repo hiện không giữ trajectory archive; phải đổi dữ liệu, input và loss, nên là scope amendment lớn nhất. Nó vẫn phụ thuộc vào việc thu được trajectory thành công và không phải bằng chứng cho bốn allocation signals.

GPI-LS nên giữ vai trò comparator/diagnostic sau khi base learner đủ điều kiện, không xếp làm remedy đầu tiên: weight prioritization không chữa được một learner chưa biểu hiện ore policy.

## Bước tiếp theo được khuyến nghị

Trong scope hiện tại, **không chạy thêm**. Dùng memo này để xin một quyết định cụ thể, không phải lời khuyên chung chung:

- nếu chấp nhận amendment: phê duyệt một feasibility study hữu hạn cho trajectory-aware achieved-return preference replay, với seeds/budgets/checkpoints/logging/falsifier khóa trước;
- nếu không chấp nhận amendment: giữ Minecart như negative blocked result và thu hẹp deliverable, không diễn giải LunarLander diagnostics thành course comparison hoàn tất.

Không nên lặp lại plain TD-error PER, tăng interactions đơn thuần hay hyperparameter sweep. Envelope hoặc PCN chỉ nên được xét nếu amendment cho replay relabeling bị falsify hoặc supervisor chọn thay backbone ngay từ đầu.

## Falsification plan tương lai — chỉ là đề xuất

Một plan mới chỉ được tạo sau approval và phải giữ final test đóng. Plan nên log tách biệt:

1. **Acquisition:** mỗi seed có bao nhiêu delivery transition/trajectory và chúng được sample/relabel bao nhiêu lần.
2. **Expression:** tại mọi checkpoint khóa trước, greedy policy có chọn `Mine`, lấy cargo, delivery và positive ore hay không.
3. **Retention:** sau checkpoint đầu tiên pass ore gate, phải pass ít nhất hai checkpoint tiếp theo; một spike rồi mất không đạt.
4. **Falsifier của remedy ưu tiên:** nếu relabeling tăng rõ exposure với successful trajectories nhưng tất cả seed vẫn zero greedy ore và action margin của `Mine` không cải thiện, bác bỏ replay relabeling như remedy chính và dừng, không chồng thêm thay đổi.

## Authority gate

Memo và JSON đi kèm không thay đổi protocol, claim, roadmap, checkpoint hay experiment status. Remediation v3, reward/hyperparameter change, rollout/training mới, checkpoint lock, final test, paid review, commit/push và submission vẫn bị cấm nếu chưa có authority riêng.

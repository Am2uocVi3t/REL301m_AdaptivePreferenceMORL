# 📚 CẨM NANG DÀNH CHO TEAM REL301m — TỔNG QUAN DỰ ÁN & GIẢI THÍCH THUẬT NGỮ
*(Việt và Nam đọc kỹ file này khoảng 10-15 phút là nắm vững toàn bộ dự án từ gốc rễ đến chi tiết!)*

---

## 🎯 1. DỰ ÁN NÀY LÀM CÁI GÌ? (NÓI DỄ HIỂU NHẤT)

### Bài toán đời thực:
* Trong học tăng cường truyền thống (RL thông thường), con AI chỉ tối ưu **1 mục tiêu duy nhất** (ví dụ: chơi game đạt điểm cao nhất).
* Nhưng ngoài đời, mọi bài toán đều có **nhiều mục tiêu xung đột nhau (Multi-Objective RL - MORL)**:
  * **Tàu đáp mặt trăng (LunarLander)**: Vừa muốn đáp nhanh, vừa muốn tiết kiệm nhiên liệu, vừa muốn đáp thật êm để không nổ tàu. Nếu đáp quá nhanh thì dễ nổ; nếu bay quá cẩn thận thì hết sạch xăng!
  * **Xe chở quặng (Minecart)**: Vừa muốn đào Quặng 1, vừa muốn đào Quặng 2, lại vừa muốn tiết kiệm nhiên liệu di chuyển.

### Cái hay của dự án nhóm mình:
* Bình thường nếu người dùng muốn ưu tiên "tiết kiệm xăng", người ta phải train lại một con AI mới từ đầu. Nếu muốn "đáp nhanh", lại train một con AI khác.
* Nhóm mình nghiên cứu **Conditioned Policy (Chính sách có điều kiện)**: **Một mô hình AI duy nhất** nhận thêm đầu vào là **Preference vector $w$ (Trọng số mong muốn của người dùng)**. Khi người dùng kéo thanh trượt (slider) trên Web demo, con AI sẽ tự động đổi hành vi ngay lập tức trong thời gian thực mà **KHÔNG CẦN TRAIN LẠI!**

---

## 📖 2. TỪ ĐIỂN THUẬT NGỮ (GLOSSARY) ĐỂ TỰ TIN TRƯỚC MẶT THẦY TIẾN SĨ

| Thuật ngữ | Tên tiếng Anh | Giải thích dễ hiểu nhất | Thầy Tiến sĩ sẽ đánh giá gì? |
| :--- | :--- | :--- | :--- |
| **MORL** | Multi-Objective Reinforcement Learning | Học tăng cường đa mục tiêu. Thay vì nhận 1 số điểm thưởng, AI nhận một mảng (vector) điểm thưởng cho từng mục tiêu $r_t = [r_1, r_2, \dots, r_d]$. | Thấy nhóm hiểu rõ bài toán không gian vector. |
| **Preference Vector ($w$)** | Preference / Weight Vector | Vector trọng số do người dùng đặt ra, ví dụ $[0.7, 0.1, 0.1, 0.1]$ (tổng bằng 1). Số nào to hơn nghĩa là người dùng đang ưu tiên mục tiêu đó hơn. | Phân biệt được input của người dùng với reward của môi trường. |
| **Linear Scalarization** | Tuyến tính hóa vô hướng ($w^\top r$) | Cách nhân trọng số với từng reward rồi cộng lại: $U = w_1 r_1 + w_2 r_2 + \dots$ để tính ra tổng độ hữu dụng (Utility). | Hiểu cách tính utility mục tiêu. |
| **Pareto Front** | Mặt tiền Pareto | Tập hợp các giải pháp tối ưu mà ở đó bạn không thể làm tốt hơn ở mục tiêu này mà không làm tệ đi ở mục tiêu khác (sự đánh đổi hoàn hảo). | Khái niệm nền tảng của tối ưu hóa đa mục tiêu. |
| **Value-based (DQN)** | Phương pháp dựa trên giá trị | AI học cách ước lượng điểm số Q-value cho từng hành động. Giai đoạn đầu nhóm dùng mạng **PCQN (Pareto Conditioned Q-Network)** 3 nhánh. | Biết được kiến trúc nhóm đã thử nghiệm ở nửa đầu kỳ. |
| **Credit Assignment Problem** | Vấn đề gán công trạng | Trong Minecart, AI phải đi một đoạn đường dài, rẽ đúng góc, đào quặng rồi mang về bãi giao thì mới có thưởng lớn. Nếu mạng DQN đi loanh quanh, nó không biết hành động nào trong quá khứ đem lại thành công ➔ Dẫn đến học thất bại. | **Đây là câu trả lời đắt giá nhất khi giải thích vì sao DQN thất bại!** |
| **PPO + GAE** | Proximal Policy Optimization + Generalized Advantage Estimation | Thuật toán học chính sách trực tiếp (Policy Gradient) on-policy. Ổn định hơn DQN rất nhiều, giúp AI học được chuỗi hành vi phức tạp. | Đây là giải pháp bứt phá cuối kỳ của nhóm. |
| **Seed** | Random Seed | Con số khởi tạo ngẫu nhiên. Trong Machine Learning, chạy 1 seed thành công có thể do "ăn may". Nhóm mình chạy **3 seed độc lập** (mỗi seed 4 triệu bước) để chứng minh kết quả là thật và ổn định. | Thầy tiến sĩ cực kỳ tôn trọng tính trung thực qua nhiều seed. |
| **Argmax vs Sampled** | Quyết định Tất định vs Lấy mẫu | • **Sampled**: AI chọn hành động theo xác suất (dùng lúc train để khám phá).<br>• **Argmax**: AI luôn chọn hành động có xác suất cao nhất (dùng lúc demo để hành động chuẩn xác nhất). | Thể hiện nhóm hiểu sâu cơ chế inference. |
| **Failure Analysis** | Phân tích thất bại | Thay vì giấu giếm việc DQN thất bại (0 quặng), nhóm phân tích rõ tại sao nó fail và lưu lại số liệu. Trong nghiên cứu khoa học, Failure Analysis có giá trị tương đương kết quả dương. | Điểm cộng nghiên cứu lớn nhất của đồ án! |

---

## ⚡ 3. CÂU CHUYỆN (STORYLINE) TOÀN BỘ ĐỒ ÁN — ĐỌC ĐỂ KHÔNG BỊ KHỚP

1. **Khởi đầu (Giữa kỳ)**: Nhóm đặt mục tiêu làm MORL phân bổ việc học giữa các mục tiêu. Nhóm dùng mạng Value-based (DQN/PCQN).
2. **Cú ngã khoa học**: Chạy 30 jobs, 28.800 validation episodes. Kết quả: **Minecart đạt 0 quặng!** Con xe chỉ chạy tới chạy lui để tiết kiệm xăng chứ không chịu đi lấy quặng vì bài toán Credit Assignment quá khó đối với DQN rời rạc.
3. **Bước ngoặt (Cuối kỳ)**: Nhóm nhận ra: *Muốn phân bổ trọng số, con AI trước hết phải biết làm nhiệm vụ đã (Task Competence)!* Nhóm chuyển sang kiến trúc **PPO (On-Policy Actor-Critic)** chạy 4 triệu bước.
4. **Trái ngọt**: 
   * **Minecart**: Cả 3 seed huấn luyện đều vượt qua bài kiểm tra, đạt **10/10 lượt giao quặng thành công**.
   * **Lunar Lander**: Đạt **10/10 lần hạ cánh êm ái vào bãi đáp**.
5. **Sản phẩm bàn giao**: Giao diện Web tương tác trực tiếp chạy trên mô hình PPO thật, kéo slider đổi hành vi ngay lập tức.


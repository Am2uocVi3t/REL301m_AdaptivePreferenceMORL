# 🎯 HƯỚNG DẪN DÀNH CHO TEAM REL301m — BÁO CÁO & THUYẾT TRÌNH CUỐI KỲ (FINAL)
*Ngày chốt phiên bản: 03/11/2026 (Phiên bản LunarPPO Final)*

---

## ⚠️ LƯU Ý SỐNG CÒN: PHÂN BIỆT BẢN GIỮA KỲ VS BẢN CUỐI KỲ (FINAL)
* Rất nhiều nhóm/tài liệu cũ bị nhầm lẫn giữa bản **Giữa kỳ (DQN/Value-based)** và bản **Cuối kỳ (PPO)**. Team mình cần nắm rõ mạch này để thuyết trình và trả lời vấn đáp của giảng viên:
  1. **Giai đoạn giữa kỳ / Thử nghiệm ban đầu (Mô hình Value-based / PCQN)**:
     - Nhóm dùng Q-learning 3 heads chia chung trunk.
     - **Kết quả âm (Negative Result)**: Minecart giao được 0 quặng (zero ore) suốt 14.400 episodes; Lunar Lander không đáp trúng bãi.
     - *Ý nghĩa*: Đây là bằng chứng phân tích lỗi (failure analysis) rất đắt giá được giữ lại trong báo cáo, chứng minh nhóm làm thật - đo thật.
  2. **Giai đoạn CUỐI KỲ CHÍNH THỨC (Mô hình PPO - On-Policy Backbone)**:
     - Nhóm chuyển sang kiến trúc **PPO + GAE (4 triệu bước huấn luyện)**.
     - **Kết quả thành công vượt trội**:
       * **Minecart**: 3 seed độc lập, **10/10 lượt hoàn thành nhiệm vụ** ở cả 2 profile thử nghiệm!
       * **Lunar Lander**: Checkpoint cuối đạt **10/10 lần hạ cánh native +100 an toàn bên trong bãi đáp**!

---

## 📂 DANH MỤC CÁC TÀI LIỆU TRONG THƯ MỤC NÀY:

1. **[KICH_BAN_SLIDE_VA_PHAN_CHIA_3_NGUOI.md](KICH_BAN_SLIDE_VA_PHAN_CHIA_3_NGUOI.md)**:
   - Dàn ý 10 slide trực quan hoá cao (ít chữ, nhiều hình ảnh).
   - Phân chia vai trò 3 người:
     * **Hưng (Demo & Dẫn nhập)**: Nêu bài toán thực tế, dẫn dắt câu chuyện nghiên cứu và live demo kéo slider.
     * **Việt (Kiến trúc & Thuật toán)**: Giải thích toán MORL, vector reward và so sánh PCQN vs PPO.
     * **Nam (Thực nghiệm & Phân tích lỗi)**: Thuyết trình số liệu đo đạc (10/10 task success), phân tích giới hạn và trả lời phản biện giảng viên.
   - Bộ câu hỏi phản biện sâu và câu trả lời mẫu cho Tiến sĩ phản biện.

2. **[KICH_BAN_THUYET_TRINH_CUOI_KY_FINAL.md](KICH_BAN_THUYET_TRINH_CUOI_KY_FINAL.md)**:
   - Kịch bản thuyết trình cuối kỳ phân bổ thời gian chi tiết (~6 phút từ intro đến demo).

3. **[DOC_CHO_TEAM_TONG_QUAN_VA_THUAT_NGU.md](DOC_CHO_TEAM_TONG_QUAN_VA_THUAT_NGU.md)**:
   - Cẩm nang nhập môn và từ điển thuật ngữ A-Z (MORL, Pareto Front, PPO vs DQN, GAE, Coverage, v.v.) giải thích cực kỳ dễ hiểu cho toàn bộ team.

4. **[HUONG_DAN_CHAY_DEMO.md](HUONG_DAN_CHAY_DEMO.md)**:
   - Hướng dẫn các bước mở demo và kịch bản thao tác trong 3 phút (kéo slider, bấm so sánh, xem reward).

5. **Thư mục hình ảnh làm slide: `figures/`**:
   - `1_Learning_Curves_That_Bai_DQN.png`: Đường cong học thất bại của DQN (động lực khoa học).
   - `2_Ket_Qua_Minecart_PPO_3_Seeds.png`: Kết quả Minecart PPO qua 3 seed (10/10 task success).
   - `3_Ket_Qua_Lunar_PPO_10_Tren_10.png`: Kết quả Lunar Lander PPO 10/10 hạ cánh an toàn.
   - `4_Thu_Nghiem_Cac_Trong_So_Kho.png`: Biểu đồ radar chẩn đoán các preference biên cực hạn.

---

## 📦 GÓI ĐÓNG GÓI SẴN GỬI TEAM (STANDALONE):
Gói hoàn chỉnh nén tại `REL301m_Team_Package_Full.zip` gồm:
- Báo cáo PDF LaTeX chính thức (`outputs/REL301m_Course_Reference_Review_20261103/docs/Bao_cao.pdf`).
- Server demo standalone offline kèm model PPO 4M bước (`START_DEMO.bat`).


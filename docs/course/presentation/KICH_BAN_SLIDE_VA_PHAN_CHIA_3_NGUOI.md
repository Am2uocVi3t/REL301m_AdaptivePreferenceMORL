# 🎬 KỊCH BẢN THUYẾT TRÌNH CUỐI KỲ & HƯỚNG DẪN THIẾT KẾ SLIDE (3 NGƯỜI)
**Môn học: REL301m — Reinforcement Learning**  
**Đề tài: Preference-Conditioned Multi-Objective Reinforcement Learning (MORL)**  
**Đối tượng chấm: Giảng viên là Tiến sĩ (Đòi hỏi tính trung thực, phương pháp chuẩn, không làm màu)**

---

## 👥 PHÂN CHIA VAI DIỄN CHO 3 NGƯỜI:

| Thành viên | Vai trò | Điểm mạnh & Phong cách thể hiện |
| :--- | :--- | :--- |
| **HƯNG** *(Trưởng nhóm)* | **Dẫn chuyện, Khái niệm trực quan & Master Demo** | Phong thái tự tin, đời thường, không nặng toán lý thuyết. Dẫn dắt vấn đề thực tế cuốn hút, trực tiếp biểu diễn Web Demo trước mặt thầy và tổng kết đồ án. |
| **VIỆT** | **Kiến trúc mô hình & Phương pháp luận** | Đảm nhiệm phần toán học, định nghĩa vector reward, cơ chế Conditioned Policy, giải thích kiến trúc PPO Actor-Critic và pipeline huấn luyện. |
| **NAM** | **Thực nghiệm, Failure Analysis & Phản biện (Counter Q&A)** | Trình bày các biểu đồ số liệu, phân tích vì sao mô hình DQN ban đầu bị thất bại (Failure Analysis), kết quả bứt phá 10/10 của PPO và "bật" lại các câu hỏi hóc búa của thầy. |

---

## 🖼️ NGUYÊN TẮC THIẾT KẾ SLIDE (THEO YÊU CẦU: RẤT NHIỀU HÌNH ẢNH — CỰC ÍT CHỮ)
* **Tuyệt đối không nhồi nhét đoạn văn (no walls of text)**: Thầy tiến sĩ đọc rất nhanh, nếu slide nhiều chữ thầy sẽ đọc slide chứ không nghe bạn nói.
* **Mỗi slide chỉ có 1 hình ảnh trọng tâm + 3 đến 4 từ khóa (Bullet points ngắn)**.
* **Toàn bộ hình ảnh biểu đồ xịn đã được trích xuất sẵn** trong thư mục:  
  📁 `REL301m_Team_Package/Hinh_Anh_Lam_Slide/`

---

## 📑 CHI TIẾT TỪNG SLIDE: NỘI DUNG, HÌNH ẢNH & LỜI THOẠI

---

### SLIDE 1: TIÊU ĐỀ ĐỀ TÀI & GIỚI THIỆU NHÓM
* **Người nói**: **HƯNG** (30 giây)
* **Visual trên Slide**: 
  * Logo trường + Tiêu đề đề tài: **Preference-Conditioned Multi-Objective Reinforcement Learning (MORL)**.
  * Tên 3 thành viên: Hưng, Việt, Nam.
* **Chữ trên slide**: 
  * *Học tăng cường đa mục tiêu có điều kiện*
  * *Giảng viên hướng dẫn: [Tên Thầy]*
* **Lời thoại của Hưng**:
  > *"Em xin chào Thầy và các bạn. Hôm nay nhóm em gồm 3 thành viên: em là Hưng, bạn Việt và bạn Nam, xin được báo cáo đồ án cuối kỳ môn REL301m với đề tài: Nghiên cứu học tăng cường đa mục tiêu có điều kiện (Preference-Conditioned MORL). Trong bài báo cáo hôm nay, nhóm em không chỉ trình bày kết quả thành công, mà còn đem đến một bức tranh thực nghiệm trung thực: từ những thất bại ban đầu với mô hình Value-based đến bước ngoặt thành công với PPO và sản phẩm demo tương tác trực tiếp."*

---

### SLIDE 2: BÀI TOÁN THỰC TẾ — TẠI SAO PHẢI CẦN MORL?
* **Người nói**: **HƯNG** (45 giây)
* **Visual trên Slide**: 
  * Chia đôi màn hình:
    * Bên trái: Ảnh xe mỏ **Minecart** (Mining vs Fuel).
    * Bên phải: Ảnh tàu vũ trụ **Lunar Lander** (Soft Landing vs Fuel).
* **Chữ trên slide**:
  * **RL truyền thống**: 1 mục tiêu duy nhất $\rightarrow$ Bất khả thi trong thực tế.
  * **Đời thực luôn xung đột**: Muốn an toàn $\leftrightarrow$ Muốn nhanh; Muốn đào nhiều quặng $\leftrightarrow$ Muốn ít tốn xăng.
  * **Giải pháp thông thường**: Mỗi nhu cầu train lại 1 con AI $\rightarrow$ Quá tốn kém!
* **Lời thoại của Hưng**:
  > *"Thưa Thầy, trong học tăng cường kinh điển, agent chỉ tối ưu 1 con số reward duy nhất. Nhưng thực tế thì khác: Một chiếc tàu đáp mặt trăng vừa phải hạ cánh an toàn, vừa phải tiết kiệm nhiên liệu; nếu bay quá cẩn thận thì cạn xăng nổ tung, nếu lao quá nhanh thì đâm sầm vào đá. Tương tự, xe chở quặng Minecart vừa phải tìm quặng, vừa phải tính toán quãng đường ngắn nhất. Bình thường, cứ mỗi lần người dùng đổi ý muốn tiết kiệm xăng hơn, chúng ta lại phải train lại một mạng neural mới từ đầu. Câu hỏi đặt ra là: Liệu có thể huấn luyện DUY NHẤT MỘT mô hình mà có thể đáp ứng linh hoạt mọi nhu cầu của người dùng hay không? Sau đây bạn Việt sẽ trình bày về giải pháp kiến trúc của nhóm."*

---

### SLIDE 3: KIẾN TRÚC MÔ HÌNH — PREFERENCE-CONDITIONED POLICY
* **Người nói**: **VIỆT** (60 giây)
* **Visual trên Slide**: 
  * Sơ đồ mạng: Input gồm $[s, w]$ đưa vào chung một Trunk $\rightarrow$ Rẽ sang Actor và Critic. (Có thể chụp từ file `ppo-inference.tex`).
* **Chữ trên slide**:
  * **Vector Reward**: $r_t \in \mathbb{R}^d$ (Không cộng gộp reward khác đơn vị).
  * **Preference Vector ($w$)**: Trọng số người dùng mong muốn ($\sum w_i = 1$).
  * **Linear Scalarized Utility**: $U_w(G) = w^\top G$.
  * **Conditioned Policy**: $\pi(a \mid s, w)$ — Nhận preference như một biến trạng thái mở rộng.
* **Lời thoại của Việt**:
  > *"Kính thưa Thầy, để giải bài toán này, nhóm em xây dựng một mạng Conditioned Policy $\pi(a \mid s, w)$. Điểm khác biệt cốt lõi ở đây là reward không còn là 1 con số vô hướng, mà là một vector $r_t$ trong không gian $d$ chiều. Người dùng sẽ cung cấp một vector trọng số $w$ phản ánh mức độ ưu tiên của họ, với tổng trọng số bằng 1. Tổng độ hữu dụng được tính bằng tích vô hướng $U = w^\top G$. Nhờ đưa trực tiếp vector $w$ vào cùng với trạng thái quan sát $s$, mô hình có thể điều chỉnh phân phối hành động tức thì theo ý muốn của người dùng mà hoàn toàn không cần cập nhật lại trọng số mạng."*

---

### SLIDE 4: THỰC THI THUẬT TOÁN — TẠI SAO CHỌN PPO + GAE?
* **Người nói**: **VIỆT** (45 giây)
* **Visual trên Slide**:
  * Sơ đồ pipeline huấn luyện: Environment $\rightarrow$ Rollout buffer $\rightarrow$ PPO Clipped Objective + GAE $\rightarrow$ MultiBody Actor-Critic.
* **Chữ trên slide**:
  * **Actor-Critic tách biệt**: Mạng Actor sinh xác suất hành động, Critic đánh giá vector giá trị $V(s)$.
  * **GAE (Generalized Advantage Estimation)**: Giảm phương sai trong môi trường có horizon dài.
  * **Inference tối ưu**: Dùng **Sampled** lúc huấn luyện để khám phá, dùng **Argmax** lúc Demo để ra quyết định tất định, chuẩn xác nhất.
* **Lời thoại của Việt**:
  > *"Để huấn luyện ổn định trên không gian đa mục tiêu, nhóm em sử dụng khung thuật toán PPO kết hợp GAE. Mạng gồm hai phần tách biệt: Critic ước lượng vector giá trị và chuẩn hóa bằng PopArt trong quá trình train; còn Actor sẽ học chính sách hành động tương ứng với trọng số $w$. Trong quá trình huấn luyện, nhóm dùng chế độ Sampled để agent khám phá đa dạng không gian trạng thái; còn khi triển khai thực tế trên sản phẩm demo, nhóm cố định chế độ Argmax để đưa ra các hành động có độ tin cậy và xác suất cao nhất. Tiếp theo, bạn Nam sẽ trình bày về quá trình thực nghiệm đầy kịch tính của nhóm."*

---

### SLIDE 5: FAILURE ANALYSIS — CÚ NGÃ KHOA HỌC VỚI VALUE-BASED (DQN)
* **Người nói**: **NAM** (60 giây)
* **Visual trên Slide**: 
  * Chèn ảnh: `1_Learning_Curves_That_Bai_DQN.png` (Nằm trong folder `Hinh_Anh_Lam_Slide`).
* **Chữ trên slide**:
  * **Thử nghiệm ban đầu**: Value-based (PCQN 3 heads) — 30 runs, 28.800 validation episodes.
  * **Kết quả âm (Negative Result)**: Minecart đạt **0 QUẶNG** suốt toàn bộ quá trình!
  * **Nguyên nhân cốt lõi**: *Credit Assignment Failure* — Không gian rời rạc quá thưa, xe chỉ học được cách đứng yên hoặc đi lùi để tiết kiệm xăng.
  * **Giá trị nghiên cứu**: Giữ nguyên toàn bộ số liệu làm **Phân tích thất bại (Failure Analysis)**, không làm đẹp số liệu.
* **Lời thoại của Nam**:
  > *"Kính thưa Thầy, đây là phần thực nghiệm mà nhóm em tự hào nhất về tính trung thực học thuật. Ở nửa đầu dự án, nhóm triển khai mô hình dựa trên Q-learning (PCQN) với 30 job độc lập và gần 30.000 tập validation. Nhưng biểu đồ trên slide đã chỉ ra một sự thật: Mô hình hoàn toàn thất bại trên Minecart, số lượng quặng giao được bằng 0! Phân tích sâu nguyên nhân, nhóm nhận ra mô hình bị mắc kẹt ở bài toán Credit Assignment: chuỗi hành động tìm quặng và mang về bãi quá dài, mạng Q-learning bị bias vào mục tiêu tiết kiệm nhiên liệu nên chỉ chọn đứng yên. Thay vì giấu kết quả này, nhóm em giữ lại toàn bộ trong báo cáo làm Failure Analysis — vì trong nghiên cứu, hiểu rõ lý do thất bại cũng quan trọng như một kết quả thành công."*

---

### SLIDE 6: BƯỚC NGOẶT THÀNH CÔNG — PPO FEASIBILITY SCREENING
* **Người nói**: **NAM** (60 giây)
* **Visual trên Slide**: 
  * Ghép 2 ảnh cạnh nhau:
    * Trái: `2_Ket_Qua_Minecart_PPO_3_Seeds.png` (Minecart 3 seeds 10/10).
    * Phải: `3_Ket_Qua_Lunar_PPO_10_Tren_10.png` (Lunar 10/10 landings).
* **Chữ trên slide**:
  * **Nguyên lý tiên quyết**: *Muốn phân bổ trọng số tốt, Policy trước hết phải làm được nhiệm vụ (Task Competence)!*
  * **Minecart (PPO 4M steps)**: 3 seeds độc lập $\rightarrow$ **10/10 lượt giao quặng thành công**.
  * **Lunar Lander (PPO 4M steps)**: **10/10 lần hạ cánh an toàn** native +100 bên trong bãi đáp.
* **Lời thoại của Nam**:
  > *"Từ thất bại trên, nhóm em rút ra một luận điểm cốt tử: Muốn đánh giá việc phân bổ trọng số ưu tiên, agent trước hết phải có đủ năng lực giải quyết tác vụ cơ bản. Nhóm quyết định chuyển sang PPO huấn luyện 4 triệu bước. Kết quả đã tạo ra bước ngoặt hoàn toàn: Trên Minecart, cả 3 seed huấn luyện độc lập đều vượt qua task gate, đạt 10/10 lượt giao quặng thành công. Trên Lunar Lander, mô hình đạt tỷ lệ 10/10 lần hạ cánh êm ái vào chính giữa bãi đáp với điểm native +100. Điều này chứng minh kiến trúc Policy Gradient đã khắc phục triệt để điểm nghẽn của Q-learning."*

---

### SLIDE 7: KIỂM THỬ ĐỘ NHẠY TRỌNG SỐ — CORNER TESTING
* **Người nói**: **NAM** (45 giây)
* **Visual trên Slide**: 
  * Chèn ảnh: `4_Thu_Nghiem_Cac_Trong_So_Kho.png`.
* **Chữ trên slide**:
  * **Thử nghiệm trên 5 môi trường mới hoàn toàn (Unseen seeds)**.
  * **Trọng số đồng đều & mặc định**: Giữ vững tỷ lệ thành công 4/5 và 5/5.
  * **Trọng số cực đoan (Corner)**: Nhóm thẳng thắn ghi nhận giới hạn khi ép model vào các góc cực đoan (chỉ tiết kiệm xăng thì không giao quặng).
* **Lời thoại của Nam**:
  > *"Không dừng lại ở các ca thử nghiệm quen thuộc, nhóm em tiến hành kiểm thử độ nhạy với các trọng số cực đoan trên 5 môi trường mới. Kết quả cho thấy với các trọng số cân bằng, mô hình duy trì độ ổn định rất cao. Tuy nhiên, nhóm cũng trung thực chỉ ra rằng khi người dùng đặt trọng số tuyệt đối vào việc tiết kiệm nhiên liệu, agent sẽ hy sinh việc giao quặng — điều này hoàn toàn hợp lý về mặt tối ưu toán học nhưng là giới hạn cần lưu ý khi áp dụng thực tế. Bây giờ, bạn Hưng sẽ trực tiếp biểu diễn sản phẩm demo trước Thầy."*

---

### SLIDE 8: TRỰC TIẾP DEMO SẢN PHẨM — INTERACTIVE DEMO (LIVE)
* **Người nói & Thao tác**: **HƯNG** (90 giây)
* **Visual trên Slide**: 
  * Chụp ảnh màn hình Web Demo (giao diện 2 panel so sánh, thanh trượt Slider, các đồng hồ đo Reward).
  * **(Hưng mở cửa sổ trình duyệt Web Demo chạy song song)**.
* **Các bước Hưng thao tác trước mặt Thầy**:
  1. *Bấm chạy Lunar Lander panel trái (trọng số mặc định: ưu tiên hạ cánh 0.7)* $\rightarrow$ Tàu đáp chuẩn vào bãi.
  2. *Kéo thanh trượt panel phải (tăng ưu tiên tiết kiệm nhiên liệu)* $\rightarrow$ Bấm chạy so sánh để Thầy thấy tàu đốt ít động cơ hơn hẳn.
  3. *Chuyển sang Minecart* $\rightarrow$ Cho xe chạy và bấm nút **Tải file Trace JSON** để chứng minh đây là inference mạng thật 100%, không phải video phát lại.
* **Lời thoại của Hưng**:
  > *"Em xin phép mở giao diện Demo của nhóm. Thưa Thầy, gói demo này chạy inference trực tiếp từ 2 checkpoint PPO 4 triệu bước mới nhất. Ở panel bên trái, em để trọng số mặc định: con tàu đốt động cơ liên tục để giữ thăng bằng và hạ cánh êm ái. Bây giờ ở panel bên phải, em kéo thanh trượt để tăng tối đa ưu tiên tiết kiệm nhiên liệu. Khi bấm chạy so sánh, Thầy có thể thấy ngay sự khác biệt: con tàu bên phải hạn chế tối đa việc kích hoạt động cơ chính, chấp nhận rơi tự do nhiều hơn để tiết kiệm xăng. Mọi tham số trạng thái và reward đều được xuất ra file JSON thời gian thực, chứng minh toàn bộ quá trình inference diễn ra trực tiếp trên laptop."*

---

### SLIDE 9: TỔNG KẾT ĐÓNG GÓP & HƯỚNG PHÁT TRIỂN
* **Người nói**: **HƯNG** (45 giây)
* **Visual trên Slide**:
  * Bảng tổng kết 3 trụ cột:
    1. Pipeline kiểm thử MORL chặt chẽ có khả năng tái lập (Reproducibility).
    2. Bộ dữ liệu Failure Analysis đối chứng giữa Value-based và Policy Gradient.
    3. Bộ demo tương tác trực quan thời gian thực.
* **Chữ trên slide**:
  * **Đóng góp**: Phương pháp luận thực nghiệm chuẩn mực, giải quyết trọn vẹn task competence bằng PPO.
  * **Giới hạn**: Chưa chứng minh adaptive allocation vượt trội hơn uniform trên mọi miền preference.
  * **Hướng tương lai**: Mở rộng sang không gian hành động liên tục và mạng Pareto Front đa chính sách.
* **Lời thoại của Hưng**:
  > *"Tóm lại, đồ án của nhóm em mang lại 3 đóng góp thực tế: Thứ nhất là xây dựng một pipeline chuẩn mực có khả năng tái lập và đối chứng khoa học. Thứ hai là bộ phân tích thất bại sâu sắc chỉ rõ vì sao mô hình Value-based thất bại trên bài toán dài hạn. Và thứ ba là minh chứng sống động về năng lực giải quyết đa mục tiêu của PPO. Nhóm em không nhận vơ những kết quả ngoài tầm đo, mà tự hào vì đã thực hiện một nghiên cứu nghiêm túc, trung thực từ thất bại đến thành công. Chúng em xin chân thành cảm ơn Thầy và sẵn sàng lắng nghe câu hỏi từ Thầy ạ."*

---

### SLIDE 10: PHIÊN HỎI ĐÁP (Q&A) — CÁC ĐÒN "COUNTER" DÀNH CHO NAM & VIỆT
*(Khi Thầy đặt câu hỏi, Nam và Việt sẽ phụ trách trả lời chính)*

#### Câu hỏi 1: *"Tại sao nhóm đổi từ Q-learning sang PPO? PPO có phải thuật toán nhóm tự nghĩ ra không?"*
* **Việt trả lời**: 
  > *"Dạ thưa Thầy, nhóm em hoàn toàn không nhận PPO là thuật toán mới do nhóm tự phát minh. Việc chuyển sang PPO là một bước kiểm tra tính khả thi (feasibility screen). Lý do là vì mạng Q-learning ban đầu gặp bế tắc nghiêm trọng ở bài toán Credit Assignment, khiến agent không học được cách nhặt quặng. Nhóm nhận thấy muốn đánh giá các chiến lược phân bổ mục tiêu, điều kiện tiên quyết là policy phải hoàn thành được nhiệm vụ cơ bản trước. Vì vậy, PPO được nhóm áp dụng như một on-policy backbone đáng tin cậy để vượt qua ngưỡng task competence này ạ."*

#### Câu hỏi 2: *"Khi người dùng kéo slider trên web demo, mạng có phải đang train lại ngầm không?"*
* **Việt trả lời**: 
  > *"Dạ thưa Thầy, tuyệt đối không có quá trình training lại nào diễn ra lúc demo ạ. Trọng số weights của mạng neural hoàn toàn cố định. Thanh trượt slider chỉ thay đổi vector đầu vào $w$ được truyền vào mạng cùng với observation $s$. Mạng thực hiện một lượt forward pass inference thông thường để tính ra hành động tối ưu theo preference mới ạ."*

#### Câu hỏi 3: *"Tại sao nhóm chỉ chạy 3 seed, liệu có đủ độ tin cậy thống kê không?"*
* **Nam trả lời**: 
  > *"Dạ thưa Thầy, trong phạm vi tài nguyên tính toán và thời gian của một đồ án môn học, việc chạy 3 seed độc lập với 4 triệu bước huấn luyện cho mỗi seed (tổng cộng 12 triệu bước) là nỗ lực rất lớn của nhóm để đảm bảo kết quả không phải do ăn may của một seed đơn lẻ. Nhóm cũng đã thực hiện audit chéo số liệu trên toàn bộ các episodes và nêu rõ đây là kết quả kiểm chứng tính ổn định trên tập phát triển, chứ nhóm không hề phóng đại thành kết luận tổng quát tuyệt đối ạ."*

---

> 💡 **Lời khuyên cho cả nhóm**: 
> * Hưng chỉ cần mở đầu thật tự tin, nói to, rõ ràng và biểu diễn demo mượt mà. 
> * Việt nói ngắn gọn về công thức và cấu trúc mạng. 
> * Nam chỉ cần bám chắc vào câu chuyện "Thất bại của DQN là bằng chứng quý giá ➔ PPO giải quyết bài toán". 
> * Khi thầy khen hay chê, hãy giữ thái độ khiêm tốn, cầu thị và dùng số liệu thật để trả lời. Điểm số chắc chắn sẽ rất cao!


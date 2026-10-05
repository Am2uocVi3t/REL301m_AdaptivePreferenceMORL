# Task 1: Thuật toán Cốt lõi & Adaptive Preference Curriculum
**Nhánh Git:** `feat/algorithm-curriculum`  
**Cặp phụ trách:** **Ngô Hoài Nam & Huỳnh Quốc Việt**

---

## 🎯 1. Mục tiêu công việc
Xây dựng toàn bộ mô hình mạng neural đa mục tiêu và cơ chế lập trình chương trình ưu tiên thích ứng (Adaptive Curriculum) theo đúng mô tả tại Mục 5 trong Proposal:
1. **Preference-Conditioned Vector Q-Network (PCQN)** với cấu trúc multi-head ($K=3$).
2. **Double-DQN style Vector Bellman Update** và hàm loss Huber theo từng objective.
3. **Bộ lấy mẫu thích nghi (Adaptive Sampler)** kết hợp 3 tín hiệu:
   - **Conditioning Gap** $g(\mathbf{w})$
   - **Bootstrap Ensemble Uncertainty** $u(\mathbf{w})$
   - **Coverage / Recency** $c(\mathbf{w})$
4. **Unit Tests** kiểm tra tính hội tụ và tính đúng đắn của phép tính vector Q.

---

## 📂 2. Các file cần triển khai & Chữ ký hàm

### 2.1. `src/models/q_network.py`
* **Nhiệm vụ:**
  - Định nghĩa lớp `VectorQNetwork(nn.Module)`.
  - Input: State $[B, d_s]$ và Preference $[B, d]$. Concatenate thành $[B, d_s + d]$.
  - MLP Trunk: 2 hidden layers $\times$ 256 units, kích hoạt ReLU.
  - Multi-Head Bootstrap: Xuất $K=3$ heads độc lập, mỗi head có kích thước $[B, |\mathcal{A}|, d]$.
  - Hàm `predict_scalarized(state, preference, head_idx=0)`: Tính tích vô hướng $\mathbf{w}^\top Q_\theta(s, a, \mathbf{w})$ và trả về action tối ưu $\arg\max_a$.

### 2.2. `src/curriculum/uncertainty.py`
* **Nhiệm vụ:**
  - Cài đặt công thức (12) từ Proposal:
    $$u(\mathbf{w}) = \mathbb{E}_{s \sim \mathcal{B}} \left[ \text{Var}_{k=1}^K \left( \mathbf{w}^\top Q_{\theta_k}(s, a_k^*, \mathbf{w}) \right) \right]$$
  - Lấy một mini-batch trạng thái $s$ từ Replay Buffer, tính phương sai dự đoán giữa 3 heads cho preference $\mathbf{w}$.

### 2.3. `src/curriculum/gap.py`
* **Nhiệm vụ:**
  - Cài đặt công thức (11) từ Proposal:
    $$g(\mathbf{w}) = \left[ \max_{\mathbf{v} \in \mathcal{A}} \mathbf{w}^\top \mathbf{v} - \mathbf{w}^\top \hat{\mathbf{v}}_{\pi_\theta(\cdot \mid \mathbf{w})} \right]_+$$
  - Đo khoảng cách giữa performance của policy hiện tại $\hat{\mathbf{v}}$ và điểm tốt nhất có trong Pareto Archive $\mathcal{A}$ dưới góc nhìn trọng số $\mathbf{w}$.

### 2.4. `src/curriculum/sampler.py`
* **Nhiệm vụ:**
  - Tạo candidate pool $\mathcal{W}$ ban đầu (gồm các đỉnh simplex cực biên, các cạnh, và Dirichlet distribution $\text{Dir}(\mathbf{1})$).
  - Chuẩn hóa 3 tín hiệu $\hat{g}(\mathbf{w}), \hat{u}(\mathbf{w}), \hat{c}(\mathbf{w})$ theo Min-Max hoặc Z-score.
  - Tính điểm tổng hợp: $z(\mathbf{w}) = \alpha \hat{g}(\mathbf{w}) + \beta \hat{u}(\mathbf{w}) + \eta \hat{c}(\mathbf{w})$.
  - Cài đặt Softmax phân phối lấy mẫu kết hợp với uniform exploration floor $\epsilon_c \ge 0.2$ (Công thức 14):
    $$p(\mathbf{w}) = (1 - \epsilon_c) \frac{\exp(z(\mathbf{w})/\tau)}{\sum_{\mathbf{w}'} \exp(z(\mathbf{w}')/\tau)} + \frac{\epsilon_c}{|\mathcal{W}|}$$

---

## 🤖 3. Hướng dẫn Vibe Coding cùng AI Assistant

Khi sử dụng Antigravity / Cursor / Copilot trên nhánh này, các bạn có thể chỉ định file tài liệu này làm context:
> *"Tôi đang làm Task 1 theo tài liệu `docs/tasks/task1_algorithm.md`. Hãy triển khai file `src/models/q_network.py` theo đúng kiến trúc 2 hidden layers 256 units, K=3 bootstrap heads, input là [s, w] và output là tensor kích thước [K, B, num_actions, num_objectives]. Hãy thêm docstrings đầy đủ và type hinting."*

---

## ✅ 4. Tiêu chí Hoàn thành (Checklist)
- [ ] `VectorQNetwork` chạy thử forward pass không bị lỗi shape tensor.
- [ ] Target Double-DQN tính đúng vector $\mathbf{y}_t$ theo từng chiều objective.
- [ ] Hàm tính Uncertainty $u(\mathbf{w})$ xuất giá trị $\ge 0$.
- [ ] Phân phối xác suất $p(\mathbf{w})$ có tổng bằng $1.0$ và không có giá trị NaN.
- [ ] Viết unit test trong `tests/test_algorithm.py` kiểm tra các thành phần trên pass 100%.

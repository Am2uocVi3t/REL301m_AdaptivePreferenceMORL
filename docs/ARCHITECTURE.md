# System Architecture & Technical Specifications

Tài liệu này quy chuẩn toàn bộ kiến trúc toán học, luồng dữ liệu (Data Flow) và giao diện lập trình (API Interfaces) của hệ thống **Adaptive Preference MORL**. Tất cả các module trong `src/` phải tuân thủ nghiêm ngặt các định dạng dữ liệu và chữ ký hàm này.

---

## 📐 1. Nền tảng Toán học & Công thức cốt lõi

### 1.1. Multi-Objective Markov Decision Process (MOMDP)
Môi trường được mô hình hóa bởi tuple:
$$M = (\mathcal{S}, \mathcal{A}, P, \mathbf{r}, \gamma)$$
- Trạng thái $s \in \mathcal{S} \subseteq \mathbb{R}^{d_s}$
- Hành động rời rạc $a \in \mathcal{A}$
- Vector phần thưởng $\mathbf{r}(s, a, s') \in \mathbb{R}^d$ với $d$ là số chiều objectives ($d=4$ cho `MO-LunarLander`, $d=3$ cho `Minecart`).
- Vector trọng số ưu tiên $\mathbf{w}$ thuộc simplex $\Delta^{d-1}$:
  $$\Delta^{d-1} = \left\{ \mathbf{w} \in \mathbb{R}^d : w_i \ge 0, \sum_{i=1}^d w_i = 1 \right\}$$
- Hàm độ thỏa dụng tuyến tính (Linear Scalarized Utility):
  $$J(\pi, \mathbf{w}) = \mathbf{w}^\top \mathbb{E}_\pi \left[ \sum_{t=0}^T \gamma^t \tilde{\mathbf{r}}_t \right]$$

---

### 1.2. Preference-Conditioned Vector Q-Network (PCQN)
Mạng neural nhận đầu vào là cặp ghép $[s, \mathbf{w}] \in \mathbb{R}^{d_s + d}$ và dự đoán vector Q-values cho toàn bộ các hành động:
$$Q_\theta(s, a, \mathbf{w}) \in \mathbb{R}^d, \quad \forall a \in \mathcal{A}$$

* **Lựa chọn hành động (Action Selection):**
  $$a_t = \arg\max_{a \in \mathcal{A}} \mathbf{w}^\top Q_\theta(s_t, a, \mathbf{w})$$
  *(Kết hợp thăm dò $\epsilon$-greedy trong giai đoạn huấn luyện).*

* **Mục tiêu Bellman theo phong cách Double DQN:**
  $$a^* = \arg\max_{a' \in \mathcal{A}} \mathbf{w}^\top Q_\theta(s_{t+1}, a', \mathbf{w})$$
  $$\mathbf{y}_t = \mathbf{r}_t + \gamma (1 - d_t) Q_{\bar{\theta}}(s_{t+1}, a^*, \mathbf{w})$$
  Loss được tính bằng Huber loss hoặc Smooth L1 Loss trên từng chiều objective:
  $$\mathcal{L}(\theta) = \sum_{i=1}^d \text{Huber}\left( y_{t, i} - Q_{\theta, i}(s_t, a_t, \mathbf{w}) \right)$$

---

### 1.3. Cơ chế Adaptive Preference Curriculum

Mỗi chu kỳ curriculum checkpoint (mỗi $10{,}000 - 25{,}000$ steps), hệ thống tính điểm cho từng preference candidate $\mathbf{w} \in \mathcal{W}$ dựa trên 3 tín hiệu:

1. **Conditioning Gap $g(\mathbf{w})$:**
   Đo khoảng cách giữa policy hiện tại với các nghiệm tốt nhất đã tìm thấy trong Pareto Archive $\mathcal{A}$:
   $$g(\mathbf{w}) = \left[ \max_{\mathbf{v} \in \mathcal{A}} \mathbf{w}^\top \mathbf{v} - \mathbf{w}^\top \hat{\mathbf{v}}_{\pi_\theta(\cdot \mid \mathbf{w})} \right]_+$$

2. **Bootstrap Ensemble Uncertainty $u(\mathbf{w})$:**
   Độ lệch (phương sai) dự đoán giữa $K=3$ bootstrap heads:
   $$u(\mathbf{w}) = \mathbb{E}_{s \sim \mathcal{B}} \left[ \text{Var}_{k=1}^K \left( \mathbf{w}^\top Q_{\theta_k}(s, a_k^*, \mathbf{w}) \right) \right]$$

3. **Coverage / Recency $c(\mathbf{w})$:**
   Tăng điểm khi vùng lân cận của $\mathbf{w}$ ít được lấy mẫu hoặc đã lâu chưa được thăm:
   $$c(\mathbf{w}) = \frac{1}{1 + N(\mathbf{w})}$$

* **Tổng hợp và phân phối lấy mẫu (Sampling Distribution):**
  $$z(\mathbf{w}) = \alpha \hat{g}(\mathbf{w}) + \beta \hat{u}(\mathbf{w}) + \eta \hat{c}(\mathbf{w})$$
  $$p(\mathbf{w}) = (1 - \epsilon_c) \frac{\exp(z(\mathbf{w}) / \tau)}{\sum_{\mathbf{w}'} \exp(z(\mathbf{w}') / \tau)} + \frac{\epsilon_c}{|\mathcal{W}|}$$
  *(Với $\epsilon_c \ge 0.2$ là uniform exploration floor).*

---

## 🔄 2. Sơ đồ Luồng Dữ liệu (Data Flow)

```text
       ┌────────────────────────────────────────────────────────┐
       │             Candidate Preference Pool W                │
       └──────────────────────────┬─────────────────────────────┘
                                  │ Lấy mẫu p(w) từ Curriculum
                                  ▼
                     Preference w ~ p(w)
                                  │
                                  ▼
   ┌──────────────────────────────────────────────────────────────────┐
   │                         Environment Rollout                      │
   │  Agent chọn: a = argmax w^T Q(s, a, w)  (e-greedy)               │
   │  Nhận transition: (s_t, a_t, r_t_vector, s_{t+1}, done)          │
   └───────────────┬──────────────────────────────────┬───────────────┘
                   │ Transition                       │ Episodic Return Vector v
                   ▼                                  ▼
      ┌─────────────────────────┐        ┌─────────────────────────┐
      │   Vector ReplayBuffer   │        │     Pareto Archive A    │
      │ (Lưu r dạng vector R^d) │        │ (Lọc Pareto non-dom)    │
      └────────────┬────────────┘        └────────────┬────────────┘
                   │ Mini-batch                       │ v in A
                   ▼                                  │
      ┌─────────────────────────┐                     │
      │  Train Vector Q-Network │                     │
      │  - Double DQN Bellman   │                     │
      │  - Multi-Head Bootstrap │                     │
      └────────────┬────────────┘                     │
                   │                                  │
                   ▼                                  ▼
      ┌────────────────────────────────────────────────────────┐
      │                Curriculum Sampler Update               │
      │   Tính: Gap g(w), Uncertainty u(w), Coverage c(w)      │
      │   Cập nhật phân phối p(w) cho chu kỳ tiếp theo         │
      └────────────────────────────────────────────────────────┘
```

---

## 🧩 3. Quy chuẩn Interface của các Module (API Contracts)

### 3.1. `src.models.q_network.VectorQNetwork`
```python
class VectorQNetwork(nn.Module):
    def __init__(self, state_dim: int, action_dim: int, reward_dim: int, num_heads: int = 3):
        ...
    def forward(self, state: torch.Tensor, preference: torch.Tensor) -> torch.Tensor:
        """
        Args:
            state: Tensor shape [batch_size, state_dim]
            preference: Tensor shape [batch_size, reward_dim]
        Returns:
            q_values: Tensor shape [batch_size, action_dim, reward_dim] hoặc [num_heads, batch_size, action_dim, reward_dim]
        """
```

### 3.2. `src.core.replay_buffer.VectorReplayBuffer`
```python
class VectorReplayBuffer:
    def add(self, state: np.ndarray, action: int, reward: np.ndarray, next_state: np.ndarray, done: bool):
        """Lưu reward dưới dạng vector float32 R^d."""
        ...
    def sample(self, batch_size: int) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        ...
```

### 3.3. `src.core.pareto_archive.ParetoArchive`
```python
class ParetoArchive:
    def add(self, candidate_vector: np.ndarray, metadata: Optional[dict] = None) -> bool:
        """Thêm vector return vào archive nếu nó không bị Pareto-dominated."""
        ...
    def is_dominated(self, v: np.ndarray) -> bool:
        ...
    def get_points(self) -> np.ndarray:
        """Trả về toàn bộ các điểm non-dominated hiện tại [N, reward_dim]."""
        ...
```

### 3.4. `src.curriculum.sampler.AdaptivePreferenceSampler`
```python
class AdaptivePreferenceSampler:
    def __init__(self, pool_size: int, reward_dim: int, alpha: float = 0.25, beta: float = 0.25, eta: float = 0.25, eps_c: float = 0.2):
        ...
    def sample(self) -> np.ndarray:
        """Lấy 1 vector preference w tuân theo phân phối p(w)."""
        ...
    def update_scores(self, gap_scores: np.ndarray, uncertainty_scores: np.ndarray):
        """Cập nhật điểm z(w) và phân phối p(w) tại mỗi checkpoint."""
        ...
```

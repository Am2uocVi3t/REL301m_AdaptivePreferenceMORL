# Task 2: Môi trường, Dynamics Shifts & Baselines
**Nhánh Git:** `feat/env-baselines`  
**Cặp phụ trách:** **Lê Nguyễn Gia Hưng & Ngô Hoài Nam**

---

## 🎯 1. Mục tiêu công việc
Chuẩn hóa môi trường chạy thực nghiệm và tích hợp các thuật toán baseline để so sánh theo đúng Mục 4 & Mục 6 trong Proposal:
1. **Thiết lập Wrapper môi trường** trên `MO-Gymnasium`:
   - `mo-lunar-lander-v2` (4 reward dimensions: landing/crash, shaping, main fuel, side fuel).
   - `minecart-v0` (3 reward dimensions: ore 1, ore 2, fuel).
2. **Cài đặt cơ chế Dynamics Shift (Environment Generalization):**
   - Thay đổi các thông số vật lý (trọng lực, gió, lực nhiễu loạn trên LunarLander; tiêu hao nhiên liệu trên Minecart).
3. **Chuẩn hóa Reward (Reward Normalization):**
   - Đảm bảo các chiều reward có biên độ scale tương đồng để tránh 1 objective lấn át các objective còn lại.
4. **Tích hợp các Baseline so sánh:**
   - **Uniform-PCQN** (Mạng giống mô hình chính nhưng lấy mẫu preference hoàn toàn đồng đều).
   - **Envelope Q-Learning** (từ `morl-baselines`).
   - **GPI-LS** (Generalized Policy Improvement with Linear Support từ `morl-baselines`).

---

## 📂 2. Các file cần triển khai & Chữ ký hàm

### 2.1. `src/envs/wrapper.py`
* **Nhiệm vụ:**
  - Định nghĩa lớp `MORewardNormalizeWrapper(gym.RewardWrapper)`: Chuẩn hóa vector phần thưởng $\mathbf{r}_t \in \mathbb{R}^d$ theo scale cố định xác định từ trước (freeze scales).
  - Định nghĩa hàm khởi tạo môi trường chuẩn: `make_mo_env(env_id, seed, dynamics_shift_config=None)`.
  - Hỗ trợ headless rendering để ghi video trajectory phục vụ demo của Hưng.

### 2.2. `src/envs/shift.py`
* **Nhiệm vụ:**
  - Định nghĩa các kịch bản shift theo bảng quy chuẩn:
    - **LunarLander Nominal:** Trọng lực gốc ($-10.0$), gió tắt.
    - **Shift 1 (Heavy Gravity):** Tăng trọng lực lên $1.5\times$.
    - **Shift 2 (Strong Wind):** Bật gió lớn (`enable_wind=True`, `wind_power=15.0`).
    - **Shift 3 (Turbulence & Low Gravity):** Trọng lực thấp kết hợp gió giật ngẫu nhiên (`turbulence_power=1.5`).
  - Hàm `apply_dynamics_shift(env, shift_name)`: Can thiệp trực tiếp vào thuộc tính của môi trường Box2D / Minecart trước khi reset.

### 2.3. `src/baselines/morl_baselines_runner.py`
* **Nhiệm vụ:**
  - Xây dựng class/hàm wrapper chạy các thuật toán có sẵn trong thư viện `morl_baselines` (Envelope Q-Learning và GPI-LS) sao cho nhận cùng interface, cùng số lượng environment steps và cùng cách thức logging ra WandB.

### 2.4. `configs/env/lunarlander.yaml` & `configs/env/minecart.yaml`
* **Nhiệm vụ:**
  - Khai báo thông số môi trường, observation dimensions, action space, và reference point chuẩn cho việc tính Hypervolume.

---

## 🤖 3. Hướng dẫn Vibe Coding cùng AI Assistant

Khi làm việc trên nhánh này, các bạn có thể prompt AI:
> *"Tôi đang làm Task 2 theo tài liệu `docs/tasks/task2_env_baselines.md`. Hãy viết class `MORewardNormalizeWrapper` kế thừa từ `gymnasium.RewardWrapper` trong file `src/envs/wrapper.py`. Wrapper này cần nhận một vector scaling factor tĩnh để chuẩn hóa vector reward 4 chiều của MO-LunarLander. Đồng thời viết hàm `make_mo_env` hỗ trợ khởi tạo seed và dynamics shift."*

---

## ✅ 4. Tiêu chí Hoàn thành (Checklist)
- [ ] Khởi tạo được `mo-lunar-lander-v2` và `minecart-v0` mà không bị crash.
- [ ] Ghi nhận đúng vector reward 4 chiều (LunarLander) và 3 chiều (Minecart).
- [ ] Hàm `apply_dynamics_shift` thay đổi thành công trọng lực hoặc gió trong runtime.
- [ ] Baseline `Envelope Q-Learning` và `GPI-LS` chạy thử $10{,}000$ steps và log được metrics lên console/WandB.
- [ ] Viết test trong `tests/test_envs_baselines.py` xác nhận wrapper hoạt động đúng.

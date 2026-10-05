# Adaptive Preference Curriculum for Zero-Shot Multi-Objective Reinforcement Learning under Environment Shift

[![Python 3.10](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org/downloads/release/python-3100/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Course: REL301m](https://img.shields.io/badge/Course-REL301m--FPTU-orange.svg)]()
[![Framework: MO--Gymnasium](https://img.shields.io/badge/Framework-MO--Gymnasium-green.svg)](https://mo-gymnasium.farama.org/)

> **Đồ án cuối kỳ môn Học tăng cường (Reinforcement Learning - REL301m)**  
> **Trường Đại học FPT TP. Hồ Chí Minh — Học kỳ Fall 2026**

---

## 📌 1. Giới thiệu tổng quan (Project Overview)

Trong các bài toán RL truyền thống, hàm reward thường là một giá trị vô hướng (scalar). Khi một bài toán có nhiều mục tiêu xung đột (ví dụ: hạ cánh an toàn vs. tiết kiệm nhiên liệu vs. thời gian bay), việc cố định trọng số $\lambda$ buộc người thiết kế phải huấn luyện lại toàn bộ mô hình mỗi khi ưu tiên thay đổi.

Dự án này tập trung vào bài toán **Multi-Objective Reinforcement Learning (MORL)** với mục tiêu:
1. **Huấn luyện một Preference-Conditioned Policy duy nhất** $\pi_\theta(a \mid s, \mathbf{w})$ có thể tức thời thích nghi với vector ưu tiên $\mathbf{w}$ bất kỳ từ người dùng mà không cần tái huấn luyện (*zero-shot adaptation*).
2. **Đề xuất cơ chế Adaptive Preference Curriculum**: Tự động phân bổ dữ liệu huấn luyện vào các vùng preference mà agent đang yếu (dựa vào *Conditioning Gap* so với Pareto Archive), có độ bất định cao (*Bootstrap Uncertainty*), hoặc ít được khám phá (*Coverage/Recency*).
3. **Đánh giá tính bền vững (Robustness)** khi môi trường có sự thay đổi động lực học (*Environment/Dynamics Shift*: trọng lực, gió, lực cản, ma sát, phân bố quặng...).

---

## 👥 2. Thành viên nhóm & Phân công ghép cặp (Team & Pair Matrix)

Dự án áp dụng mô hình **Ghép cặp chéo (Pair-Programming Matrix)**: Mỗi nhánh kỹ thuật có **2 thành viên** cùng phụ trách và review chéo nhằm tối ưu hóa thế mạnh cá nhân và đảm bảo chất lượng code.

* **Huỳnh Quốc Việt (SE194225)** — *Team Leader*: Thế mạnh về Core Algorithm, Math, Evaluation & Metrics Pipeline.
* **Ngô Hoài Nam** — *AI Engineer*: Thế mạnh về Core Algorithm, Model Architecture, Baselines Reproduction.
* **Lê Nguyễn Gia Hưng** — *AI & Research Engineer*: Thế mạnh về Environment Setup, LaTeX Paper, Demo Visualizer.

### Bảng phân công nhánh & Nhiệm vụ:

| Nhánh Git (Branch) | Cặp phụ trách | Nhiệm vụ chính & Phạm vi công việc | Tài liệu hướng dẫn chi tiết |
| :--- | :--- | :--- | :--- |
| **`feat/algorithm-curriculum`** | **Nam & Việt** | • Cài đặt Preference-Conditioned Vector Q-Network ($Q_\theta(s, a, \mathbf{w})$).<br>• Cài đặt Multi-Head Bootstrap ensemble ($K=3$).<br>• Xây dựng bộ lấy mẫu thích nghi (Adaptive Sampler) kết hợp Gap, Uncertainty và Coverage. | [📖 Task 1 Guide](docs/tasks/task1_algorithm.md) |
| **`feat/env-baselines`** | **Hưng & Nam** | • Thiết lập wrapper cho `MO-LunarLander-v2` và `Minecart-v0`.<br>• Xây dựng injector cho Dynamics Shifts (trọng lực, gió, tiêu hao nhiên liệu).<br>• Chuẩn hóa baseline từ `morl-baselines` (GPI-LS, Envelope Q-Learning, Uniform-PCQN). | [📖 Task 2 Guide](docs/tasks/task2_env_baselines.md) |
| **`feat/eval-pipeline`** | **Hưng & Việt** | • Tính toán Pareto Metrics: Hypervolume (HV), Sparsity, Scalarized Regret.<br>• Thiết lập module logging (WandB & TensorBoard) tối ưu cho Kaggle.<br>• Phân tích thống kê (Permutation Test, Wilcoxon, CI 95%) & Demo Slider. | [📖 Task 3 Guide](docs/tasks/task3_eval_pipeline.md) |

---

## 📂 3. Cấu trúc thư mục (Repository Structure)

```text
REL301m_AdaptivePreferenceMORL/
├── configs/                        # Cấu hình YAML cho env, thuật toán & dynamics shift
│   ├── algo/                       # pcqn.yaml, curriculum.yaml
│   ├── env/                        # lunarlander.yaml, minecart.yaml
│   └── shifts/                     # dynamics_shifts.yaml
├── docs/                           # Tài liệu thiết kế & hướng dẫn chi tiết cho từng task
│   ├── ARCHITECTURE.md             # Luồng dữ liệu, phương trình toán học & API interfaces
│   ├── KAGGLE_GUIDE.md             # Cẩm nang train và lưu artifacts trên Kaggle GPU
│   └── tasks/                      # Hướng dẫn chi tiết từng nhánh cho các cặp thành viên
│       ├── task1_algorithm.md      # Dành cho Nam & Việt
│       ├── task2_env_baselines.md  # Dành cho Hưng & Nam
│       └── task3_eval_pipeline.md  # Dành cho Hưng & Việt
├── notebooks/                      # Jupyter notebook chạy thực nghiệm trên Kaggle
│   └── kaggle_quickstart.ipynb
├── proposal/                       # Proposal gốc của nhóm (PDF)
│   └── REL301m_Research_Project_Proposal_MORL_VI.pdf
├── scripts/                        # Entry points chạy từ dòng lệnh CLI
│   ├── train.py                    # Script huấn luyện chính
│   └── evaluate.py                 # Script đánh giá trên unseen preferences & shifts
├── src/                            # Mã nguồn lõi (Source code)
│   ├── baselines/                  # Wrapper cho Envelope Q-Learning, GPI-LS, Uniform-PCQN
│   ├── core/                       # Vector Replay Buffer & Pareto Archive
│   ├── curriculum/                 # Module tính Gap, Uncertainty, Coverage & Sampler
│   ├── envs/                       # Wrapper MO-Gymnasium & Bộ tạo Dynamics Shift
│   ├── evaluation/                 # Tính Hypervolume, Regret, Pareto Frontier & Stats
│   ├── models/                     # Vector Q-Network & Bootstrap Ensemble Heads
│   └── utils/                      # Logger tích hợp WandB/Tensorboard, helpers
├── .gitignore
├── README.md
└── requirements.txt
```

---

## 🚀 4. Hướng dẫn cài đặt & Khởi động nhanh (Quickstart)

### 4.1. Cài đặt trên máy cục bộ (Local Environment)

```bash
# 1. Clone repository
git clone https://github.com/Am2uocVi3t/REL301m_AdaptivePreferenceMORL.git
cd REL301m_AdaptivePreferenceMORL

# 2. Tạo môi trường ảo Python 3.10
python -m venv .venv
# Trên Windows:
.venv\Scripts\activate
# Trên Linux/macOS:
source .venv/bin/activate

# 3. Cài đặt dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 4.2. Huấn luyện trên Kaggle (Khuyên dùng)
Dự án được tối ưu hóa cho Kaggle GPU (P100 / T4). Để train trên Kaggle:
1. Mở Kaggle, tạo một Notebook mới với Accelerator: **GPU P100** hoặc **GPU T4 x2**.
2. Tham khảo hướng dẫn chi tiết tại [docs/KAGGLE_GUIDE.md](docs/KAGGLE_GUIDE.md) hoặc import file [notebooks/kaggle_quickstart.ipynb](notebooks/kaggle_quickstart.ipynb).
3. Đăng nhập WandB (`wandb login`) để theo dõi biểu đồ thời gian thực từ xa mà không cần treo máy.

---

## 🌿 5. Quy trình làm việc với Git & Branches (Workflow)

Để tránh xung đột code, nhóm thống nhất quy trình làm việc chuẩn sau:

1. **Nhận task & Chuyển sang nhánh tương ứng:**
   ```bash
   # Nếu bạn làm Task 1 (Nam & Việt):
   git checkout feat/algorithm-curriculum
   git pull origin feat/algorithm-curriculum

   # Nếu bạn làm Task 2 (Hưng & Nam):
   git checkout feat/env-baselines
   git pull origin feat/env-baselines

   # Nếu bạn làm Task 3 (Hưng & Việt):
   git checkout feat/eval-pipeline
   git pull origin feat/eval-pipeline
   ```

2. **Đọc tài liệu nhiệm vụ:** Đọc kỹ hướng dẫn trong thư mục `docs/tasks/` trước khi bắt tay vào code hoặc "vibe code" cùng AI assistant.
3. **Commit & Push:** Đặt commit message rõ ràng theo quy chuẩn:
   ```bash
   git add .
   git commit -m "feat(algorithm): implement vector Q-network with bootstrap heads"
   git push origin <tên-nhánh>
   ```
4. **Pull Request & Peer Review:** Tạo PR vào nhánh `main` khi một module hoàn thành và được thành viên cùng cặp xác nhận chạy ổn định.

---

## 🎯 6. Tiêu chí thành công của đồ án (Success Metrics)
- **Minimum Viable Project:** Hoàn thành train trên cả 2 môi trường (`MO-LunarLander` và `Minecart`), chạy được `Uniform-PCQN` và tối thiểu 2 baselines với 5 seeds độc lập.
- **Strong Course Project:** Hoàn thiện Full Adaptive Curriculum, phân tích Ablation Study, đánh giá Dynamics Shift, kiểm định thống kê và có Interactive Preference Slider Demo.
- **Paper-Oriented:** Tối ưu hóa code và số liệu sẵn sàng xuất bản tại student research track hoặc workshop.

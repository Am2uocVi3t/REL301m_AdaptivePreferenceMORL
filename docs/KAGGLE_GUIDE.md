# Cẩm nang Huấn luyện Thực nghiệm trên Kaggle GPU (Kaggle Guide)

Tài liệu này hướng dẫn chi tiết cách thiết lập, chạy ngầm (Save & Run All) và lưu trữ checkpoint an toàn trên nền tảng **Kaggle GPU**.

---

## ⚡ 1. Ưu điểm của Kaggle đối với Đồ án MORL
- **Tài nguyên miễn phí:** ~30 giờ GPU mỗi tuần (NVIDIA Tesla P100 hoặc 2x T4).
- **Chạy ngầm (Background Session):** Bấm "Save & Run All (Commit)", đóng trình duyệt, tắt laptop đi ngủ máy vẫn tự chạy tối đa 12 tiếng liên tục.
- **Tương thích Python 3.10:** Môi trường Kaggle hiện tại mặc định Python 3.10.

---

## 🔑 2. Chuẩn bị Tài khoản & Secrets trên Kaggle

### 2.1. Thiết lập WandB API Key (Bắt buộc để theo dõi biểu đồ từ xa)
1. Truy cập [wandb.ai/authorize](https://wandb.ai/authorize) và copy API Key của bạn.
2. Trên thanh menu của Kaggle Notebook: chọn **Add-ons** $\rightarrow$ **Secrets**.
3. Thêm secret mới:
   - **Label:** `WANDB_API_KEY`
   - **Value:** *(Dán API Key của bạn vào đây)*

---

## 🚀 3. Các bước thiết lập trong Kaggle Notebook

Mỗi thành viên khi tạo Notebook mới chỉ cần thực hiện các cell sau:

### Cell 1: Cài đặt thư viện hệ thống cho môi trường Headless (Box2D / Pygame)
```python
# Cài đặt xvfb để render môi trường LunarLander không cần màn hình vật lý
!apt-get update -y > /dev/null
!apt-get install -y xvfb python-opengl ffmpeg swig > /dev/null
!pip install pyvirtualdisplay
```

### Cell 2: Clone repository từ GitHub
```python
import os
import shutil

REPO_URL = "https://github.com/Am2uocVi3t/REL301m_AdaptivePreferenceMORL.git"
REPO_DIR = "/kaggle/working/REL301m_AdaptivePreferenceMORL"

if not os.path.exists(REPO_DIR):
    !git clone {REPO_URL} {REPO_DIR}

%cd {REPO_DIR}
!pip install -r requirements.txt
```

### Cell 3: Đăng nhập WandB tự động từ Secrets
```python
from kaggle_secrets import UserSecretsClient
import wandb

user_secrets = UserSecretsClient()
wandb_key = user_secrets.get_secret("WANDB_API_KEY")
wandb.login(key=wandb_key)
```

### Cell 4: Chạy huấn luyện (Ví dụ với MO-LunarLander)
```python
# Chạy training script với WandB logging
!python scripts/train.py \
    --env mo-lunar-lander-v2 \
    --algo adaptive-pcqn \
    --seed 42 \
    --total-timesteps 500000 \
    --wandb-project REL301m-MORL \
    --output-dir /kaggle/working/checkpoints
```

---

## 💾 4. Quản lý Checkpoints & Dữ liệu đầu ra (Tránh mất mát)

> ⚠️ **LƯU Ý CỰC KỲ QUAN TRỌNG:**
> Mọi file tạo ra trong `/kaggle/working/` chỉ được giữ lại nếu bạn bấm **Save Version** $\rightarrow$ **Save & Run All (Commit)**.
> Nếu bạn chỉ chạy interactive (chạy từng cell) và tắt tab, toàn bộ file trong `/kaggle/working/` sẽ bị xóa sau 20-30 phút không hoạt động!

### Cách lưu an toàn:
1. **Dữ liệu log biểu đồ:** Đã được tự động đẩy trực tiếp lên Cloud WandB, không bao giờ lo mất.
2. **Model Weights (`.pt`):** Script `train.py` sẽ lưu checkpoint định kỳ (mỗi $50{,}000$ steps) vào `/kaggle/working/checkpoints/`.
3. Khi bấm **Save & Run All**, sau khi notebook chạy xong, bạn vào tab **Output** của Notebook để tải file checkpoint về máy hoặc bấm "Create Dataset" để biến checkpoints thành dataset dùng cho notebook Evaluation!

---

## 🛠️ 5. Xử lý sự cố thường gặp (Troubleshooting)

1. **Lỗi `ModuleNotFoundError: No module named 'box2d'`:**
   - Chạy: `!pip install swig` sau đó `!pip install box2d-py gymnasium[box2d]`.
2. **Lỗi `Rendering error / No display found`:**
   - Khởi động virtual display bằng code Python:
     ```python
     from pyvirtualdisplay import Display
     display = Display(visible=0, size=(1400, 900))
     display.start()
     ```
3. **Kaggle GPU bị timeout sau 12h:**
   - Chia nhỏ số steps hoặc lưu checkpoint sau mỗi run để notebook sau có thể `--load-checkpoint` tiếp tục train.

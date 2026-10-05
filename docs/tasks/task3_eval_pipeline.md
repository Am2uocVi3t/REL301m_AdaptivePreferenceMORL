# Task 3: Pipeline Đánh giá, Thống kê, Visualizer & Demo
**Nhánh Git:** `feat/eval-pipeline`  
**Cặp phụ trách:** **Lê Nguyễn Gia Hưng & Huỳnh Quốc Việt**

---

## 🎯 1. Mục tiêu công việc
Xây dựng toàn bộ hệ thống đo lường chất lượng Pareto, kiểm định thống kê và các công cụ trực quan hóa (phục vụ viết paper của Hưng và kiểm chứng giả thuyết $H_1, H_2, H_3$ của Việt) theo Mục 6.3 & Mục 6.5 trong Proposal:
1. **Các chỉ số Pareto cốt lõi:**
   - **Hypervolume (HV):** Đo thể tích không gian objective bị thống trị bởi tập nghiệm so với điểm tham chiếu $\mathbf{r}_{\text{ref}}$.
   - **Worst-decile Scalarized Regret:** Đo độ hụt hẫng (regret) ở phân vị 10% tồi tệ nhất trên tập $\ge 100$ unseen preference vectors.
   - **Pareto-front Sparsity & Inverted Generational Distance (IGD).**
2. **Kiểm định Thống kê Khoa học (Statistical Rigor):**
   - 95% Bootstrap Confidence Intervals trên 5 seeds độc lập.
   - Phép kiểm định hoán vị (Permutation test) hoặc Wilcoxon signed-rank test.
   - Hiệu chỉnh Holm-Bonferroni khi kiểm định trên nhiều metrics.
3. **Bộ công cụ Logger:**
   - Unified Logger tích hợp mượt mà với **Weights & Biases (WandB)** và **TensorBoard**.
4. **Trực quan hóa & Demo:**
   - Xuất biểu đồ Pareto 2D/3D chất lượng cao (publication-ready cho LaTeX).
   - Demo tương tác (Preference Slider): Kéo thanh trượt đổi $\mathbf{w} \rightarrow$ Agent lập tức thay đổi hành vi tương ứng!

---

## 📂 2. Các file cần triển khai & Chữ ký hàm

### 2.1. `src/evaluation/metrics.py`
* **Nhiệm vụ:**
  - `compute_hypervolume(points: np.ndarray, ref_point: np.ndarray) -> float`: Tính HV (tận dụng hàm tính nhanh từ `morl-baselines` hoặc `scipy/pymoo`).
  - `compute_scalarized_regret(returns: np.ndarray, reference_front: np.ndarray, preferences: np.ndarray) -> dict`: Trả về Mean Regret và Worst-Decile (90th percentile) Regret.
  - `pareto_prune(points: np.ndarray) -> np.ndarray`: Lọc bỏ toàn bộ các điểm bị Pareto-dominated.

### 2.2. `src/evaluation/stats.py`
* **Nhiệm vụ:**
  - `bootstrap_ci(data: np.ndarray, n_boot: int = 1000, ci: float = 0.95) -> Tuple[float, float, float]`: Trả về (mean, lower_bound, upper_bound).
  - `statistical_compare(method_a_seeds: np.ndarray, method_b_seeds: np.ndarray) -> dict`: Thực hiện Wilcoxon/Permutation test và trả về p-value.

### 2.3. `src/utils/logger.py`
* **Nhiệm vụ:**
  - Định nghĩa lớp `ExperimentLogger`: Tự động nhận diện nếu có WandB API key thì log lên Cloud WandB, nếu không có mạng thì log vào TensorBoard cục bộ.
  - Hàm `log_metrics(step, metrics_dict)`.

### 2.4. `src/evaluation/visualizer.py`
* **Nhiệm vụ:**
  - `plot_pareto_fronts(methods_dict, ref_point, save_path)`: Vẽ biểu đồ so sánh Pareto fronts giữa Adaptive Curriculum vs Uniform-PCQN vs Envelope Q-Learning.
  - `plot_dynamics_shift_heatmap(shift_results, save_path)`: Vẽ heatmap đo độ suy giảm khi gặp bão gió/trọng lực mạnh.
  - `create_interactive_slider_demo(model, env)`: Tạo widget thanh trượt (slider) chạy demo live hành vi của Agent.

---

## 🤖 3. Hướng dẫn Vibe Coding cùng AI Assistant

Khi làm việc trên nhánh này, các bạn có thể prompt AI:
> *"Tôi đang làm Task 3 theo tài liệu `docs/tasks/task3_eval_pipeline.md`. Hãy triển khai file `src/evaluation/metrics.py` gồm các hàm `compute_hypervolume`, `compute_scalarized_regret` tính worst-decile regret trên unseen preferences, và `pareto_prune`. Sử dụng numpy tối ưu hóa vectorization."*

---

## ✅ 4. Tiêu chí Hoàn thành (Checklist)
- [ ] Hàm `compute_hypervolume` tính toán chính xác thể tích Pareto trên dữ liệu mẫu.
- [ ] Hàm `compute_scalarized_regret` xuất được giá trị worst-decile trên 100 test preferences ngẫu nhiên.
- [ ] `ExperimentLogger` đồng bộ thành công một chỉ số test lên dashboard WandB.
- [ ] Xuất ra được một hình vẽ scatter plot Pareto Front 2D định dạng PNG/PDF sắc nét.
- [ ] Viết test trong `tests/test_evaluation.py` kiểm tra độ chuẩn xác của các metric.

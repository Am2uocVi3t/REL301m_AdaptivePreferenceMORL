# Quy Chuẩn Quản Lý Mã Nguồn Git & Quy Tắc Phê Duyệt Pull Request (Git Workflow & Pair Review Policy)

Tài liệu này quy chuẩn quy trình làm việc nhóm, phân quyền nhánh và **chính sách phê duyệt Pull Request (PR)** bắt buộc trên GitHub cho toàn bộ thành viên dự án **REL301m - Adaptive Preference MORL**.

---

## 👥 1. Ma trận Phân công Nhánh & Trách nhiệm (Pair Matrix)

Dự án có 3 nhánh chức năng chính (`feat/*`) tương ứng với 3 nhiệm vụ lớn. Mỗi nhánh có **2 thành viên trực tiếp phụ trách (Co-owners)** và **1 thành viên giữ vai trò Giám sát (Observer/Only-View)**:

| Nhánh Chức năng (Feature Branch) | 2 Thành viên phụ trách (Direct Assignees / Co-owners) | Thành viên thứ 3 (Observer / Only View) | Nhiệm vụ trọng tâm |
| :--- | :--- | :--- | :--- |
| **`feat/algorithm-curriculum`** | **Ngô Hoài Nam & Huỳnh Quốc Việt** | **Lê Nguyễn Gia Hưng** | • Mô hình Vector Q-Network (PCQN) & Bootstrap Heads.<br>• Thuật toán Adaptive Curriculum (Gap, Uncertainty, Coverage).<br>• Vòng lặp huấn luyện chính `scripts/train.py`. |
| **`feat/env-baselines`** | **Lê Nguyễn Gia Hưng & Ngô Hoài Nam** | **Huỳnh Quốc Việt** | • Wrapper môi trường MO-Gymnasium & Reward Normalization.<br>• Injector tạo Dynamics Shifts (trọng lực, gió, lực cản).<br>• Tích hợp Baselines (Envelope Q-Learning, GPI-LS). |
| **`feat/eval-pipeline`** | **Lê Nguyễn Gia Hưng & Huỳnh Quốc Việt** | **Ngô Hoài Nam** | • Pareto Metrics (Hypervolume, Worst-decile Regret).<br>• Kiểm định thống kê (Bootstrap CI 95%, Wilcoxon).<br>• Script đánh giá `scripts/evaluate.py` & Demo Slider. |

---

## 🔒 2. Quy Tắc Phê Duyệt Pull Request (2-Approvals Merge Rule)

Để đảm bảo chất lượng code cao nhất và bảo vệ nhánh `main` luôn ở trạng thái sẵn sàng chạy thực nghiệm (production-ready):

### 2.1. Quy tắc Bắt buộc: "2 People Must Approve Before Merge"
> ⚠️ **ĐIỀU KIỆN TIÊN QUYẾT ĐỂ MERGE VÀO `main`:**  
> Một Pull Request (PR) từ nhánh chức năng chỉ được phép bấm **Merge** vào `main` khi và chỉ khi **CẢ 2 THÀNH VIÊN TRỰC TIẾP PHỤ TRÁCH NHÁNH ĐÓ ĐÃ REVIEW VÀ NHẤN "APPROVE"** trên GitHub.

* **Ví dụ 1:** Khi nhánh `feat/algorithm-curriculum` muốn merge vào `main`:
  * Người mở PR (ví dụ: Việt) gắn reviewer là Nam.
  * Nam phải đọc code, chạy thử unit tests trên máy cục bộ hoặc Kaggle, review và bấm **Approve**.
  * Sau khi cả 2 người đã thống nhất và approve, PR mới đủ điều kiện merge.
* **Ví dụ 2:** Khi nhánh `feat/env-baselines` muốn merge:
  * Cả Hưng và Nam đều phải review chéo và approve code của nhau trước khi merge.
* **Ví dụ 3:** Khi nhánh `feat/eval-pipeline` muốn merge:
  * Cả Hưng và Việt đều phải review chéo và approve code của nhau.

---

### 2.2. Vai trò của Thành viên thứ 3: "Only View / Oversight (Giám sát)"
Thành viên không trực tiếp code ở nhánh đó (thành viên thứ 3) đóng vai trò là **Người giám sát độc lập (Independent Monitor)**:

1. **Quyền hạn:** Có quyền **View**, xem toàn bộ code diff, lịch sử commit, bình luận hỏi lý do nếu thấy có chỗ chưa rõ.
2. **Nhiệm vụ giám sát:** Kiểm tra xem:
   * PR đó đã đủ chữ ký **2 Approvals** của 2 người phụ trách chính hay chưa?
   * Pipeline kiểm thử (Unit Tests / CI) có pass 100% hay không?
   * Có bị xung đột (merge conflicts) với `main` hay không?
3. **Nguyên tắc can thiệp:** Thành viên thứ 3 **không cần và không tự ý bấm merge** thay cho cặp phụ trách, trừ khi 2 người phụ trách đã đồng thuận và ủy quyền bằng văn bản trong phần comment của PR.

---

## 🛠️ 3. Hướng Dẫn Thiết Lập Branch Protection trên GitHub (Dành cho Repo Admin - Việt)

Để GitHub tự động khóa nhánh `main` và bắt buộc tuân thủ quy tắc trên, Việt (Team Leader / Repo Admin) hãy làm theo các bước:

1. Vào repository trên GitHub: **Settings** $\rightarrow$ **Branches** $\rightarrow$ chọn **Add branch protection rule**.
2. **Branch name pattern:** Điền `main`.
3. Tích chọn các mục sau:
   - ✅ **Require a pull request before merging**
   - ✅ **Require approvals**: Điền số lượng tối thiểu là `2` (hoặc `1` nếu người tạo PR không được tự approve chính PR của mình theo cơ chế GitHub).
   - ✅ **Dismiss stale pull request approvals when new commits are pushed**: Tự động hủy approve cũ nếu có commit mới được push lên.
   - ✅ **Require status checks to pass before merging** (nếu có GitHub Actions).
   - ✅ **Do not allow bypassing the above settings**: Ngăn không cho bất kỳ ai (kể cả Admin) bypass luật để merge ẩu.
4. Bấm **Create / Save Changes**.

---

## 🌿 4. Quy trình Đóng góp Hàng ngày (Step-by-step Daily Workflow)

```text
 1. Checkout nhánh của bạn  ───>  2. Code & Chạy Unit Tests  ───>  3. Commit & Push
 (git checkout feat/...)           (pytest tests/)                 (git push origin feat/...)
                                                                           │
                                                                           ▼
 6. Thành viên 3 giám sát   <───  5. Người cùng cặp Review    <───  4. Mở Pull Request
 (Observer kiểm tra đủ 2-App)      (Chạy test & Bấm Approve)       (Gán Pair Member làm Reviewer)
           │
           ▼
 7. SQUASH & MERGE VÀO MAIN (An toàn & Sạch lịch sử Git!)
```

### 4.1. Lệnh Git chuẩn:
```bash
# Cập nhật code mới nhất từ main trước khi code
git checkout main
git pull origin main

# Chuyển sang nhánh của bạn
git checkout <ten-nhanh-cua-ban>
git merge main  # Đồng bộ các cập nhật mới từ main

# Thực hiện công việc, viết test
pytest tests/

# Commit với message chuẩn (Conventional Commits)
git add .
git commit -m "feat(module): mô tả rõ công việc đã hoàn thành"
git push origin <ten-nhanh-cua-ban>
```

### 4.2. Mẫu Tiêu đề & Nội dung Pull Request (PR Template)
Khi mở PR, hãy copy template sau vào phần mô tả PR:

```markdown
### 📌 Tóm tắt Thay đổi (Summary)
- Mô tả 1-3 gạch đầu dòng những gì đã làm trong PR này.

### 👥 Trách nhiệm & Review Checklist
- [ ] Thành viên A (Co-owner): Đã kiểm tra code & unit test.
- [ ] Thành viên B (Co-owner): Đã review & APPROVE.
- [ ] Thành viên C (Observer): Đã giám sát xác nhận 2 approvals trước khi merge.

### ✅ Kết quả Kiểm thử (Test Verification)
- [ ] `pytest tests/` pass 100%.
- [ ] Không có lỗi import hoặc NaN loss.
```

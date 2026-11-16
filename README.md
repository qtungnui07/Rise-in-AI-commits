# Sự tăng trưởng của commit hỗ trợ bởi AI

> [!NOTE]
> Đây là dự án "Khoa học dữ liệu" của sinh viên trường Đại học CMC.

## Thông tin dự án
Kho lưu trữ này chứa dữ liệu và các phân tích về xu hướng sử dụng AI trong các dự án mã nguồn mở Python và JavaScript trên GitHub. Mục tiêu là khảo sát sự thay đổi theo thời gian, vai trò của file trong dự án, tỷ lệ code được chỉnh sửa trong 30 ngày đầu cùng mục đích sửa đổi (sửa lỗi, cập nhật tính năng, dọn dẹp code), từ đó rút ra các khuyến nghị thực tế khi dùng AI lập trình.

Dữ liệu được trích xuất từ repo: https://github.com/MSwadhin/empirical-study-dev-ai-usage (commit `3ec63b48e2`), là gói replication của bài báo:

> Empirical Study on the Characteristics and Evolution of AI-usage in GitHub Repositories. arXiv:2606.06843. https://arxiv.org/abs/2606.06843

Dữ liệu chỉ gồm các comment tự khai báo có dùng AI trong code Python và JavaScript, nên kết quả không đại diện cho mọi "commit AI".

## Lưu ý về dữ liệu
- Đơn vị phân tích là khối code duy nhất `(repo, file, code_block)`. Dữ liệu gốc có nhiều dòng cho cùng một khối vì một comment khớp với nhiều mẫu tìm kiếm.
- `has_recorded_change` cho biết khối code có ghi nhận lần thay đổi đầu tiên hay không (cận dưới của việc code bị sửa). Để so sánh công bằng giữa các năm, phân tích sử dụng thêm `change_30d` (có sửa trong 30 ngày đầu, chỉ tính trên các khối có đủ ít nhất 30 ngày theo dõi).
- `commit_date` lấy từ `git blame` trên dòng comment ở một phiên bản file về sau, nên chỉ là cận trên của ngày code được đưa vào. Khoảng thời gian <= 0 đến lần thay đổi đầu tiên bị loại khỏi `days_to_modification` và `change_30d`.
- `ai_tool`, `ai_verb`, `file_role` và `change_intent` được phân loại bằng quy tắc từ khóa từ comment, đường dẫn file và `change_commit_message`.
- Notebook 08 dùng nhãn do LLM gán (chưa được kiểm chứng, mức đồng thuận với nhãn nhóm còn thấp) kết hợp đối chiếu với mô hình TF-IDF + Logistic Regression trên mẫu nhãn của nhóm.

## Cách chạy
```bash
git lfs pull
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cd notebooks
for f in 0[2-8]_*.ipynb; do jupyter nbconvert --to notebook --execute --inplace "$f"; done
```

Thứ tự notebook:
1. `01_standardize`: gộp 2 file jsonl của nguồn, giữ lại `comment`, `file_url`, `change_commit_message` và lấy `commit_date` qua GitHub GraphQL API. Cần đặt 2 file dữ liệu gốc vào `data/raw/` và thiết lập biến môi trường `GITHUB_TOKEN`.
2. `02_missing_data_exploration_commits`: thống kê dữ liệu thiếu và xuất danh sách thiếu `commit_date` ra `data/interim/missing_cases_extracted/` (có thể kiểm tra link repo bằng `src/check_github_urls.py`).
3. `03_data_quality_and_processing_commits`: lọc, gộp dòng trùng, tạo các đặc trưng (`change_30d`, `file_role`, `change_intent`, kích thước code) và xuất `data/processed/commits_features.csv`.
4. `04_visualization` -> `07_classification`: đọc `commits_features.csv` để trực quan hóa, kiểm định thống kê theo cụm repo, phân tích hồi quy và chạy mô hình phân loại `change_30d`. Kết quả lưu vào `reports/` và `reports/figures/`.
5. `08_ai_task_contribution`: đọc thêm `commit_annotations_llm.csv` (nhãn LLM) và `commit_annotations.csv` (nhãn của nhóm) để phân tích tác vụ AI, đối chiếu sai số giữa LLM với nhóm và thử nghiệm mô hình TF-IDF.

## Thông tin mã nguồn
Dự án được triển khai bằng Python + Jupyter Notebook.

```
Rise-in-AI-commits/
├── data/
│   ├── raw/                # Dữ liệu gốc (không commit)
│   ├── interim/            # Dữ liệu trung gian đang xử lý
│   ├── processed/          # Dữ liệu sạch và bộ nhãn
├── notebooks/              # Các Jupyter Notebook chính của dự án (01 - 08)
├── reports/                # Báo cáo EDA.md, bảng kết quả CSV và thư mục figures/
├── src/                    # Script hỗ trợ (check_github_urls.py)
├── .gitignore
├── requirements.txt
└── README.md
```

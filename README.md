# Sự tăng truởng của commit hỗ trợ bởi AI

> [!NOTE]
> Đây là dự án "Khoa học dữ liệu" của sinh viên truờng Đại học CMC.

## Thông tin dự án
Kho lưu trữ này chứa tập hợp dữ liệu và các phân tích liên quan đến sự gia tăng số lượng commit liên quan đến AI trong nhiều dự án mã nguồn mở khác nhau. Mục tiêu là phân tích dữ liệu và trực quan hóa các xu hướng sử dụng AI của các lập trình viên theo thời gian, cũng như xác định những tác vụ cụ thể mà AI hỗ trợ, từ đó rút ra những thông tin hữu ích để đưa ra các dự đoán và khuyến nghị.

Các dữ liệu đã đuợc trích xuất từ repo sau: https://github.com/MSwadhin/empirical-study-dev-ai-usage, cố định ở commit `3ec63b48e2`. Đây là gói replication của bài báo:

> Empirical Study on the Characteristics and Evolution of AI-usage in GitHub Repositories. arXiv:2606.06843. https://arxiv.org/abs/2606.06843

Dữ liệu chỉ gồm các comment tự khai báo có dùng AI trong code Python và JavaScript, nên kết quả không đại diện cho mọi "commit AI".

## Lưu ý về dữ liệu
- Đơn vị phân tích là khối code duy nhất `(repo, file, code_block)`. Dữ liệu gốc có nhiều dòng cho cùng một khối vì một comment khớp với nhiều mẫu tìm kiếm.
- `has_recorded_change` cho biết khối code có ghi nhận lần thay đổi đầu tiên hay không. Theo schema của nguồn, ô trống nghĩa là không thu thập được, nên đây là cận dưới của việc code bị sửa.
- `commit_date` lấy từ `git blame` trên dòng comment ở một phiên bản file về sau, nên chỉ là cận trên của ngày code được đưa vào. Khoảng thời gian ≤ 0 đến lần thay đổi đầu tiên bị loại khỏi `days_to_modification`.
- Notebook 08 dùng nhãn do LLM gán, chưa được kiểm chứng, nên chỉ là phân tích thăm dò.

## Cách chạy
```bash
git lfs pull
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cd notebooks
for f in 0[2-8]_*.ipynb; do jupyter nbconvert --to notebook --execute --inplace "$f"; done
```

Thứ tự notebook:
1. `01_standardize` — gộp 2 file jsonl của nguồn và lấy `commit_date` qua GitHub GraphQL API. Cần đặt `comment_codeblock_dataset.jsonl` và `comment_codeblock_first_change_dataset.jsonl` (từ repo nguồn ở commit `3ec63b48e2`) vào `data/raw/` và đặt biến môi trường `GITHUB_TOKEN`. Kết quả `data/interim/latest_standardized_data.csv` đã có trong repo, nên có thể bỏ qua bước này.
2. `02_missing_data_exploration_commits` — xuất các dòng thiếu dữ liệu ra `data/interim/missing_cases_extracted/`.
3. `03_data_quality_and_processing_commits` — lọc, gộp dòng trùng và tạo `data/processed/commits_features.csv`.
4. `04_visualization` → `07_classification` — đọc `commits_features.csv`, ghi bảng vào `reports/` và hình vào `reports/figures/`.
5. `08_ai_task_contribution` — đọc thêm `commit_annotations_llm.csv` (nhãn LLM) và `commit_annotations.csv` (nhãn của nhóm).

## Thông tin mã nguồn
Dự án đuợc triển khai hoàn toàn bằng Python + Jupyter Notebook

Cấu trúc:
```
Rise-in-AI-commits/
├── data/
│   ├── raw/                # Dữ liệu gốc (không commit)
│   ├── interim/            # Các dữ liệu đang đuợc xử lý
│   ├── processed/          # Các dữ liệu đã đuợc xử lý
├── notebooks/              # Các script Jupyter Notebook chính của dự án
├── reports/                # Các báo cáo liên quan đến dự án
├── src/                    # Các script hỗ trợ
├── .gitignore
├── requirements.txt
└── README.md
```

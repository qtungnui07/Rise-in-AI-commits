# Rise in AI commits - Báo cáo phân tích dữ liệu (EDA)

## 1. Tổng quan dự án

Dự án này khảo sát xu hướng sử dụng AI trong các dự án mã nguồn mở Python và JavaScript trên GitHub. Thay vì chỉ đếm số lượng commit theo thời gian, báo cáo tập trung vào 3 câu hỏi thực tế:

1. Lập trình viên đang dùng công cụ AI nào, ở đâu trong dự án (code chính, file test, frontend hay script cá nhân) và xu hướng này dịch chuyển ra sao từ cuối năm 2022 đến quý 1 năm 2026?
2. Sau khi code AI được đưa vào dự án, tỷ lệ bị chỉnh sửa trong 30 ngày đầu là bao nhiêu và mục đích của lần sửa đầu tiên đó là gì (sửa lỗi, cập nhật tính năng hay dọn dẹp code)?
3. AI thường được giao những tác vụ gì (viết code mới, viết tài liệu, viết test, sửa lỗi) và mức độ tin cậy của bộ nhãn do LLM gán đến đâu?

Dữ liệu được trích xuất từ bộ `MSwadhin/empirical-study-dev-ai-usage` (commit `3ec63b48e2`), nhận diện code AI dựa trên các comment tự khai báo trong mã nguồn (như "written by ChatGPT", "claude generated", "copilot"...). Vì không có nhóm đối chứng là code không dùng AI, các tỷ lệ chỉnh sửa trong báo cáo không dùng để kết luận code AI "tốt hơn hay tệ hơn" code người viết, mà phản ánh mức độ ổn định và mục đích bảo trì thực tế sau khi đưa AI vào dự án.

---

## 2. Từ điển dữ liệu (Data Dictionary)

| Cột | Kiểu dữ liệu | Ý nghĩa |
|---|---|---|
| `id` | string | Mã định danh của match trong dữ liệu gốc. |
| `repo` | string | Tên đầy đủ của repository (`owner/repo`). |
| `language` | string | Ngôn ngữ lập trình (`python` hoặc `js`). |
| `file_url` | string | Đường dẫn tới phiên bản file trong dữ liệu gốc. |
| `commit_url` | string | Link commit cuối cùng sửa dòng comment AI (lấy qua `git blame` bằng GitHub GraphQL API). |
| `file` | string | Đường dẫn tương đối của file trong repo. |
| `comment` | string | Nội dung comment nhắc tới AI. |
| `code_block` | string | Đoạn code đi kèm comment AI. |
| `commit_date` | datetime (UTC) | Thời điểm của `commit_url`. Đây là cận trên của ngày code được đưa vào. |
| `change_commit_url` | string | Link commit đầu tiên chỉnh sửa đoạn code này (nếu thu thập được). |
| `change_commit_date` | datetime (UTC) | Thời điểm của lần chỉnh sửa đầu tiên. |
| `change_commit_message` | string | Nội dung commit message của lần chỉnh sửa đầu tiên. |
| `has_recorded_change` | boolean | `True` nếu có `change_commit_date` (cận dưới của việc code bị sửa). |
| `days_to_modification` | float | Số ngày từ `commit_date` đến `change_commit_date` (chỉ giữ giá trị > 0). |
| `change_30d` | boolean | Đoạn code có bị sửa trong 30 ngày đầu hay không (chỉ tính trên các khối có đủ ít nhất 30 ngày theo dõi). |
| `code_lines`, `code_chars` | int | Số dòng và số ký tự của đoạn code. |
| `comment_chars` | int | Độ dài của đoạn comment AI. |
| `has_function_def`, `has_class_def` | boolean | Đoạn code có chứa định nghĩa hàm hoặc class hay không. |
| `ai_tool` | string | Công cụ AI được nhận diện bằng từ khóa (`chatgpt_gpt`, `claude`, `github_copilot`, `gemini_bard`, `llama_meta`, `other_tool`, `other_ai`). |
| `ai_verb` | string | Mức độ đóng góp từ mẫu comment (`written` hoặc `assisted`). |
| `file_role` | string | Vai trò của file trong dự án (`core_source`, `notebook_or_script`, `test`, `frontend_web`, `docs_or_config`). |
| `change_intent` | string | Mục đích lần sửa đầu tiên phân loại từ `change_commit_message` (`bug_fix`, `feature_update`, `refactor_cleanup`, `docs_or_test`, `other_change`, `no_recorded_change`). |
| `repo_ai_commit_count` | int | Số commit AI của repo xuất hiện trong tập dữ liệu này. |
| `AI_task_type`, `AI_contribution_type` | string | Nhãn tác vụ và cách đóng góp của AI (lưu riêng trong `commit_annotations_llm.csv`). |

---

## 3. Quy trình chuẩn hóa và làm sạch dữ liệu

### 3.1. Chuẩn hóa dữ liệu thô (`01_standardize.ipynb`)
1. Đọc 2 file JSONL gốc (`comment_codeblock_dataset.jsonl` và `comment_codeblock_first_change_dataset.jsonl`) và gộp theo `match_id`.
2. Sử dụng GitHub GraphQL API (kèm batching và chạy song song bằng `ThreadPoolExecutor`) để lấy nội dung file và chạy `git blame` trên dòng chứa comment AI, qua đó lấy `commit_url` và `commit_date`. Cách làm này giúp giảm tỷ lệ lỗi xuống còn khoảng 3,9% so với cách đọc file `.patch` ban đầu.
3. Giữ lại các cột `comment`, `file_url` và `change_commit_message` để phục vụ phân tích ngữ cảnh và mục đích sửa code ở các bước sau.

### 3.2. Xử lý dữ liệu thiếu và gộp trùng (`02` và `03`)
1. **Thiếu `commit_date` (~3,9%):** Có 1.361/35.278 dòng không lấy được ngày commit qua GraphQL (do repo bị xóa, chuyển riêng tư hoặc lịch sử bị ghi đè). Các dòng này được loại bỏ vì không thể phân tích theo thời gian.
2. **Thiếu `change_commit_date` (~63,2%):** Theo schema gốc, ô trống nghĩa là lần thay đổi đầu tiên không thu thập được chứ không phải code chưa từng bị sửa. Nhóm giữ lại toàn bộ các dòng này và đánh dấu qua biến `has_recorded_change`.
3. **Gộp dòng trùng lặp:** Một đoạn comment có thể khớp với nhiều mẫu tìm kiếm nên xuất hiện nhiều lần. Sau khi gộp theo khóa `(repo, file, code_block)` và loại 4 khối của tháng 4/2026 (chưa đủ dữ liệu cả tháng), tập dữ liệu cuối cùng (`commits_features.csv`) còn **21.287 khối code duy nhất** thuộc **12.087 repository** (từ 03/12/2022 đến 31/03/2026).
4. **Khoảng thời gian âm hoặc bằng 0:** Có 1.733 khối có `change_commit_date <= commit_date` (do comment bị sửa sau khi code đã thay đổi ở một phiên bản về sau). Các giá trị này được chuyển thành `NaN` ở cột `days_to_modification` và loại khỏi cửa sổ `change_30d`.

---

## 4. Kết quả khám phá và phân tích

### 4.1. Xu hướng sử dụng và bối cảnh dự án
- **Tăng trưởng theo thời gian:** Số lượng khối code có comment AI tăng mạnh từ khoảng 55 khối (12/2022) lên mức trung bình ~300-400 khối/tháng trong năm 2024, bùng nổ từ tháng 5/2025 (~1.140 khối/tháng) và đạt đỉnh ~1.580 khối/tháng vào 02/2026.
- **Sự dịch chuyển công cụ AI:** Trong năm 2023 đến nửa đầu 2024, `chatgpt_gpt` chiếm ưu thế áp đảo (55% - 73% mỗi quý). Tuy nhiên từ năm 2025 đến quý 1/2026, tỷ trọng `chatgpt_gpt` giảm dần xuống còn khoảng 12%, trong khi **`claude` tăng vọt lên khoảng 32%** vào quý 1/2026. Tính chung cả tập dữ liệu: `other_ai` (không nêu rõ tên công cụ) chiếm 30,6% (6.507 khối), `chatgpt_gpt` 30,1% (6.408), `claude` 19,5% (4.160), `github_copilot` 12,6% (2.691), `gemini_bard` 5,2% (1.101) và `llama_meta` 1,8% (387).
- **Ngôn ngữ và vai trò file:** Python chiếm 73,4% (15.624 khối), JavaScript chiếm 26,6% (5.663 khối). Phần lớn code AI nằm trong mã nguồn chính `core_source` (15.708 khối, 73,8%), tiếp theo là `notebook_or_script` (9,4%), `test` (7,2%), `frontend_web` (7,1%) và `docs_or_config` (2,5%).
- **Lưu ý độ lệch theo repo:** Repo `conradhuebler/ALIMA` chiếm tỷ trọng lớn nhất trong tập dữ liệu (hơn 1.600 khối, dùng Claude rất nhiều), nên mọi kiểm định và ước lượng đều phải tính sai số chuẩn theo cụm `repo` và kiểm tra độ nhạy khi loại bỏ repo này.

### 4.2. Tỷ lệ chỉnh sửa trong 30 ngày (`change_30d`) và mục đích sửa đổi (`change_intent`)
- **Tỷ lệ sửa trong 30 ngày:** Trong 19.554 khối đủ điều kiện theo dõi ít nhất 30 ngày, có **23,0% (4.497 khối)** bị chỉnh sửa trong vòng 30 ngày đầu. Trung vị thời gian đến lần sửa đầu tiên (trên 5.714 khối có thời gian hợp lệ) là **3,07 ngày** (95% CI: `[2.89, 3.59]`).
- **Khác biệt theo vai trò file:** Nhóm `core_source` (23,7%), `frontend_web` (23,8%) và `docs_or_config` (24,4%) có tỷ lệ bị sửa trong 30 ngày cao hơn rõ rệt so với `notebook_or_script` (19,4%) và `test` (19,4%).
- **Mục đích của lần sửa đầu tiên:** Trên 7.445 khối có ghi nhận thay đổi, 28,6% là cập nhật tính năng (`feature_update`, 2.132 khối), **25,6% là sửa lỗi (`bug_fix`, 1.905 khối)**, 10,1% là dọn dẹp/refactor (`refactor_cleanup`, 752 khối), 8,1% là sửa test/tài liệu (`docs_or_test`, 602 khối) và 27,6% là thay đổi khác.

### 4.3. Kiểm định thống kê theo cụm repo (`05_statistical_inference.ipynb`)
- **Các yếu tố liên hệ có ý nghĩa thống kê với `change_30d`** (mức ý nghĩa alpha = 0,05, sai số chuẩn theo cụm `repo`):
  - **Kích thước code (`code_lines`):** `p_cluster = 8,77e-27` (rank-biserial = -0,166). Các đoạn code dài hơn có xu hướng bị chỉnh sửa trong 30 ngày nhiều hơn.
  - **Năm commit (`year`):** `p_cluster = 4,61e-5` (tỷ lệ sửa 30 ngày giảm từ 30,5% năm 2023 xuống ~21,9% năm 2025 và ~22,4% năm 2026; khi bỏ `ALIMA` thì năm 2025-2026 còn ~21,1% - 21,3%).
  - **Vai trò file (`file_role`):** `p_cluster = 0,024`. Phép thử A/B cho thấy `core_source` có tỷ lệ sửa trong 30 ngày cao hơn `notebook_or_script` là **+4,34 điểm phần trăm** (`p_cluster = 0,006`, 95% CI: `[1,23%, 7,45%]`).
  - **Công cụ AI (`ai_tool`):** `p_cluster = 0,014` trên `change_30d` và liên hệ mạnh với tỷ lệ sửa lỗi `is_bug_fix` (`p_cluster = 2,65e-18`, Cramer's V = 0,257).
- **Các yếu tố không có khác biệt có ý nghĩa thống kê sau khi gom cụm repo:**
  - Python so với JS trên `change_30d` (`p_cluster = 0,055`) và trên `days_to_modification` (`p_cluster = 0,323`).
  - Cuối tuần so với ngày thường (`p_cluster = 0,197`).
  - `written` so với `assisted` (`p_cluster = 0,220`).

### 4.4. Hồi quy và mô hình phân loại (`06` và `07`)
- **Hồi quy tuyến tính D2 (`log1p(days_to_modification)`):** R-squared đạt **0,072** (tăng so với 0,025 khi chưa biến đổi logarit), tất cả hệ số VIF đều dưới 1,6 (không bị đa cộng tuyến). `log_code_lines` có hệ số âm (`-0,158`, `p = 1,6e-5`), cho thấy khối code càng dài thì thời gian tới lần sửa đầu tiên càng ngắn.
- **Hồi quy Logistic D3 (`change_30d`):** `log_code_lines` làm tăng khả năng bị sửa trong 30 ngày (`OR = 1,24`, `p = 2,1e-31`), trong khi `notebook_or_script` (`OR = 0,76`, `p = 0,006`) và `test` (`OR = 0,80`, `p = 0,048`) ít bị sửa trong 30 ngày hơn `core_source`.
- **Hồi quy Logistic D3b (`is_bug_fix`):** Trong các khối đã từng bị sửa, file `test` có tỷ lệ lần sửa đầu là sửa lỗi cao hơn `core_source` (`OR = 1,63`, `p = 0,00025`). Nhóm `claude` (`OR = 4,45`) và `llama_meta` (`OR = 5,13`) có tỷ lệ `bug_fix` cao hơn `chatgpt_gpt` (cần lưu ý yếu tố tập trung theo một số repo lớn như `ALIMA`).
- **Phân loại `change_30d` (Notebook 07):** Khi chia train/test và 5-fold GroupKFold theo `repo` với các đặc trưng sạch (không dùng giờ UTC hay số lượng commit trong dataset), Random Forest đạt **ROC-AUC = 0,601** (test) và **0,595 ± 0,006** (5-fold CV), Logistic Regression đạt **0,600** (test) và **0,581 ± 0,008** (CV). Hai đặc trưng quan trọng nhất là `log_code_lines` và `comment_chars`. Điều này cho thấy chỉ dựa vào thông tin bề mặt của đoạn code chưa đủ để dự đoán chính xác khả năng code bị sửa trong 30 ngày, vì việc sửa đổi còn phụ thuộc vào nghiệp vụ và logic bên trong dự án.

### 4.5. Phân tích tác vụ AI và độ tin cậy nhãn (`08_ai_task_contribution.ipynb`)
- Trên 21.276 khối khớp được với bộ nhãn LLM (`17.676` khối không bị gán `False Positive`, chiếm 83,1%): tác vụ phổ biến nhất là **Code Implementation (47,8%)**, tiếp theo là **Documentation (17,0%)**, **Code Enhancement (11,7%)**, **Testing (5,5%)** và **Bug Fixing (0,7%)**.
- Mối liên hệ giữa tác vụ AI và `file_role` rất rõ rệt (`Cramer's V = 0,358`): ở các file `test`, tỷ lệ tác vụ `Testing` chiếm tới **63%**, còn ở `core_source` thì `Code Implementation` chiếm **57%**.
- **Giới hạn của nhãn LLM:** Đối chiếu với 355 dòng do nhóm tự gán thủ công, độ đồng thuận Cohen's kappa chỉ đạt **0,23 - 0,24**. Ma trận nhầm lẫn cho thấy LLM thường gán nhầm các đoạn `Code Implementation` (theo nhóm) sang `Code Enhancement`, `Documentation` hoặc `Generic / Indeterminate`. Nhóm đã trích xuất sẵn một mẫu ngẫu nhiên phân tầng 300 dòng (`reports/team_labeling_sample_300.csv`) để có thể kiểm chứng lại khách quan hơn ở các nghiên cứu tiếp theo.

---

## 5. Khuyến nghị thực tế khi sử dụng AI trong lập trình

Dựa trên các kết quả định lượng thu được từ dữ liệu, nhóm rút ra một số gợi ý thực tế cho lập trình viên:

1. **Chia nhỏ đoạn code khi nhờ AI sinh mới (`code_lines`):** Dữ liệu ở cả kiểm định C1.5, hồi quy D2 và D3 đều cho thấy đoạn code AI càng dài thì khả năng bị chỉnh sửa trong 30 ngày càng cao (`OR = 1,24`) và thời gian tới lần sửa đầu tiên càng ngắn. Nên yêu cầu AI viết từng hàm nhỏ, rõ ràng thay vì sinh cả một file dài hàng trăm dòng cùng lúc.
2. **Kiểm tra kỹ khi dùng AI cho mã nguồn chính (`core_source`) và file `test`:** Code AI nằm trong `core_source` có tỷ lệ phải sửa trong 30 ngày đầu cao hơn hẳn các script/notebook thử nghiệm (`23,7%` so với `19,4%`). Đáng chú ý, dù file `test` ít bị sửa tổng thể hơn, nhưng khi đã phải sửa thì tỷ lệ sửa lỗi (`bug_fix`) lại cao hơn (`OR = 1,63`). Lập trình viên cần tự kiểm tra lại logic kiểm thử (assertions, edge cases) khi nhờ AI viết unit test.
3. **Không quá phụ thuộc vào việc chọn "công cụ nào tốt nhất" theo cảm tính:** Mặc dù tỷ trọng người dùng đang chuyển dịch mạnh từ ChatGPT sang Claude trong năm 2025-2026, sự khác biệt về tỷ lệ code phải sửa trong 30 ngày giữa các công cụ là rất nhỏ (`Cramer's V = 0,04`). Chất lượng đầu ra vẫn phụ thuộc chủ yếu vào ngữ cảnh bài toán, độ dài đoạn code yêu cầu và cách lập trình viên review lại trước khi commit.
4. **Minh bạch và rõ ràng khi ghi chú AI trong dự án nhóm:** Tỷ lệ comment ghi chung chung (`other_ai`, chiếm 30,6%) hoặc khó phân loại (`Generic / Indeterminate`, 9,2%) còn cao. Khi làm việc nhóm, nên ghi rõ AI được dùng cho phần việc nào (viết mới, gợi ý sửa lỗi hay tạo tài liệu) để đồng đội dễ review và bảo trì về sau.

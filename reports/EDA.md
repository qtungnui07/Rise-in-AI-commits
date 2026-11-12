# Rise in AI commits - Báo cáo EDA

## Tổng quan

Dự án này nhằm khảo sát xu hướng sử dụng AI trong các dự án IT, cụ thể là xem AI đang được dùng nhiều nhất ở đâu, trong loại công việc nào (viết hàm mới, sửa lỗi, viết test, ...), và mức độ đóng góp của AI vào từng đoạn code (viết toàn bộ hay chỉ hỗ trợ một phần). Từ những quan sát này, mục tiêu cuối cùng là đưa ra một số gợi ý về việc nên và không nên dùng AI trong trường hợp nào khi lập trình.

Dữ liệu được thu thập từ các repository công khai trên GitHub, dựa vào các comment trong code có nhắc đến AI (ví dụ "written by ChatGPT", "AI generated", ...) để xác định những đoạn code có khả năng do AI tạo ra hoặc hỗ trợ. Sau khi thu thập, dữ liệu sẽ được phân tích thêm để xem các đoạn code này có bị chỉnh sửa lại sau đó hay không, dựa vào thời điểm của lần thay đổi đầu tiên (change_commit_date). Dữ liệu không có nhóm đối chứng là code không dùng AI, nên tỷ lệ này không dùng để đánh giá độ tin cậy của code do AI viết.

Dữ liệu chỉ gồm các comment tự khai báo có dùng AI trong code Python và JavaScript, nên kết quả không đại diện cho mọi "commit AI" hay "code AI".

## Lý do cần chuẩn hoá dữ liệu

Dữ liệu gốc được lưu dưới dạng 2 file jsonl riêng biệt, một file chứa các đoạn code được match, một file chứa thông tin về lần thay đổi đầu tiên của các đoạn code đó. Hai file này có cấu trúc cột khác nhau và không được liên kết sẵn với nhau thành một bảng duy nhất.

Ngoài ra, dữ liệu gốc còn thiếu một số thông tin quan trọng cho việc phân tích sau này, cụ thể là thời điểm commit của từng đoạn code (chỉ có link tới file, không có link tới commit và cũng không có ngày commit). Vì vậy, bước chuẩn hoá là cần thiết để:

- Gộp 2 nguồn dữ liệu lại thành một bảng duy nhất, có cấu trúc rõ ràng và nhất quán
- Bổ sung các thông tin còn thiếu (link commit, ngày commit) bằng cách truy vấn thêm từ GitHub
- Đưa dữ liệu về một định dạng chuẩn (ví dụ định dạng ngày giờ thống nhất) để các bước xử lý và phân tích phía sau không phải xử lý lại từ đầu

## Data dictionary

| Cột | Kiểu dữ liệu | Ý nghĩa |
|---|---|---|
| id | string | Mã định danh của từng dòng dữ liệu, được sinh ra từ dataset gốc, bao gồm ngôn ngữ lập trình, loại comment tìm được và một số định danh phụ để phân biệt các match với nhau |
| repo | string | Tên đầy đủ của repository GitHub chứa đoạn code, theo định dạng owner/ten-repo |
| language | string | Ngôn ngữ lập trình của file chứa đoạn code, ví dụ python, js |
| commit_url | string | Đường dẫn tới commit cuối cùng sửa dòng comment AI, lấy bằng `git blame` (GitHub GraphQL API) trên phiên bản file trong dữ liệu gốc. Cột này không có sẵn trong dữ liệu gốc |
| file | string | Đường dẫn tương đối của file trong repository, tính từ thư mục gốc |
| code_block | string | Đoạn code thực tế được match với comment liên quan đến AI. Ký tự xuống dòng trong code được thay bằng chuỗi ký tự "\n" để tránh làm hỏng định dạng khi lưu vào file csv |
| commit_date | datetime (UTC, ISO 8601) | Thời điểm của commit `commit_url`. Phiên bản file trong dữ liệu gốc là một phiên bản về sau, nên một lần sửa dòng comment sau khi code được đưa vào sẽ làm ngày này muộn hơn thực tế. Vì vậy đây chỉ là cận trên của ngày code được đưa vào. Có thể bị thiếu (null), xem phần Dữ liệu bị thiếu |
| change_commit_url | string | Đường dẫn tới commit đầu tiên sửa đổi đoạn code này (nếu thu thập được), lấy trực tiếp từ dữ liệu gốc |
| change_commit_date | datetime (UTC, ISO 8601) | Thời điểm của commit sửa đổi nêu trên. Bị để trống nếu nguồn không thu thập được lần thay đổi đầu tiên, xem phần Dữ liệu bị thiếu |
| has_recorded_change | boolean | True nếu có `change_commit_date`. Là cận dưới của việc code bị sửa (tạo ở notebook 03) |
| AI_task_type | string | AI được dùng cho việc gì (Code Implementation, Documentation, Testing, ...). Do LLM gán, lưu trong `data/processed/commit_annotations_llm.csv`. Chưa được kiểm chứng, xem notebook 08 |
| AI_contribution_type | string | AI đóng góp theo cách nào (Implementation, Artifact Generation, Knowledge Support, ...). Do LLM gán, cùng file với `AI_task_type` |

## Quy trình xử lý và chuẩn hoá dữ liệu thô

Dữ liệu gốc nằm trong 2 file jsonl:
- comment_codeblock_dataset.jsonl: chứa toàn bộ các đoạn code được match với comment liên quan đến AI
- comment_codeblock_first_change_dataset.jsonl: chứa thông tin về lần commit đầu tiên sửa đổi các đoạn code đó (nếu có)

Các bước xử lý chính như sau:

1. Đọc cả 2 file jsonl bằng pandas, sau đó merge lại với nhau bằng left join để giữ nguyên toàn bộ số dòng của bảng gốc, đồng thời bổ sung thêm thông tin thay đổi nếu match được.
2. Tạo bảng output mới, lấy các cột cần thiết từ dataset gốc và đổi tên lại cho ngắn gọn, rõ ràng hơn (id, repo, language, file, code_block).
3. Dữ liệu gốc chỉ có đường dẫn tới file (blob url) ở một phiên bản về sau, không có đường dẫn tới commit đưa code vào. Notebook tìm dòng comment AI trong phiên bản file đó và chạy `git blame` trên dòng này để lấy commit cuối cùng sửa nó.
4. Dữ liệu gốc cũng không có sẵn ngày commit, nên cần gọi thêm GitHub API để lấy. Cách tiếp cận ban đầu là lấy file .patch của từng commit (không cần token xác thực) rồi tìm dòng "Date:" trong nội dung trả về. Tuy nhiên cách này thất bại ở phần lớn số dòng (khoảng 97%), do GitHub từ chối render file patch khi diff quá lớn hoặc commit có chứa nội dung nhị phân. Sau đó, quy trình được chuyển sang dùng GitHub API chính thức (GraphQL) để lấy riêng ngày commit mà không cần render toàn bộ diff, giúp tỉ lệ thất bại giảm xuống còn khoảng 3%.
5. Do số lượng commit cần truy vấn khá lớn, để tránh vượt giới hạn số lượng request của GitHub và rút ngắn thời gian xử lý, các kỹ thuật sau được áp dụng: loại bỏ các đường dẫn commit bị trùng lặp trước khi gọi API (do nhiều dòng dữ liệu có thể trỏ đến cùng một commit), gộp nhiều commit vào chung một truy vấn GraphQL duy nhất (batching), và thực hiện nhiều truy vấn song song bằng multithreading.
6. Bổ sung 2 cột change_commit_url và change_commit_date từ dataset gốc vào bảng output.
7. Xuất bảng kết quả ra file csv, lưu vào thư mục data/interim để phục vụ cho các bước xử lý tiếp theo.

## Hướng xử lý Dữ liệu bị thiếu (Data Cleaning)

Trong bảng dữ liệu sau khi chuẩn hoá, có 2 cột chính bị thiếu giá trị ở một số dòng. Dựa trên tính chất của từng loại missing data, chúng tôi đã đưa ra các hướng xử lý cụ thể như sau:

**1. Cột `commit_date` (~3,9%)**:
1.361/35.278 dòng không lấy được commit qua `git blame`, nên cả `commit_url` và `commit_date` đều trống. Với 1.082 dòng thiếu ngày ở lần chạy trước, kiểm tra bằng HTTP request cho thấy các URL trả về lỗi 404 (Not Found) hoặc 429 (Rate Limit). Nguyên nhân có thể là:
- Repository đã bị xóa hoặc chuyển sang chế độ private sau thời điểm dữ liệu gốc được thu thập.
- Lịch sử commit bị ghi đè (ví dụ force push hoặc amend).
- Repository bị đổi tên hoặc chuyển chủ sở hữu.
**-> Hướng xử lý: Xóa** 1.361 dòng này, vì không có ngày thì không dùng được cho phân tích theo thời gian. Còn lại 33.917 dòng.

**2. Cột `change_commit_url` và `change_commit_date` (~63,2%)**:
22.282/35.278 dòng bị để trống ở 2 cột này. Theo `dataset/SCHEMA.md` của nguồn, ô trống nghĩa là lần thay đổi đầu tiên "was not successfully collected" (không thu thập được). Vì vậy không thể kết luận rằng code ở các dòng này chưa từng bị sửa.
**-> Hướng xử lý: Không xóa.** Tạo cột `has_recorded_change` (Boolean):
- Có ngày thay đổi: `has_recorded_change = True`.
- Để trống: `has_recorded_change = False`. Không biết code có bị sửa hay không.

Tỷ lệ `has_recorded_change = True` là cận dưới của tỷ lệ code bị sửa.

**3. Dòng trùng lặp**:
33.917 dòng chỉ có 21.502 khối `(repo, file, code_block)` duy nhất, chủ yếu do một comment khớp với nhiều mẫu tìm kiếm. Giữ một dòng cho mỗi khối; khi các dòng trùng có `commit_date` khác nhau, giữ ngày sớm nhất. Loại thêm 4 khối của tháng 4/2026 vì dữ liệu tháng này chưa đủ. Còn lại 21.498 khối.

**4. `commit_date` chỉ là cận trên**:
`git blame` chạy trên một phiên bản file về sau, nên một lần sửa dòng comment sau khi code được đưa vào sẽ làm `commit_date` muộn hơn thực tế. Trong dữ liệu chưa gộp, 17% dòng có thay đổi có lần thay đổi đầu tiên xảy ra trước `commit_date` và 12% có thời điểm trùng nhau. Sau khi gộp, 1.742 khối có khoảng thời gian ≤ 0; các khoảng này bị loại khỏi `days_to_modification` nhưng khối vẫn giữ `has_recorded_change = True`.

## Công cụ sử dụng

- Python: ngôn ngữ chính được dùng để viết toàn bộ pipeline xử lý dữ liệu
- Jupyter Notebook: môi trường thực thi code theo từng bước, thuận tiện cho việc kiểm tra kết quả ở mỗi giai đoạn
- pandas: đọc file jsonl/csv, xử lý và merge dữ liệu dạng bảng
- requests: gửi request tới API của GitHub
- GitHub GraphQL API: truy vấn metadata của commit (cụ thể là ngày commit), được dùng thay cho phương pháp scrape trực tiếp vì cho kết quả nhanh và ổn định hơn
- concurrent.futures (ThreadPoolExecutor): thực hiện nhiều request song song để rút ngắn thời gian xử lý
- Các thư viện chuẩn khác: os, io (StringIO), datetime, time, phục vụ việc đọc file, tạo thư mục và quản lý thời gian khi xuất file

## Phân tích trực quan hóa (Visualization):

Trong phần này, chúng ta sẽ tiến hành khám phá và trực quan hóa dữ liệu tương tác AI để làm rõ các đặc trưng hành vi và xu hướng phát triển theo thời gian. Việc phân tích đa chiều qua các biểu đồ sẽ giúp cung cấp cái nhìn tổng quan lẫn chi tiết về sự dịch chuyển trong quá trình ứng dụng công cụ hỗ trợ lập trình.

**1.** Khảo sát số lượng và sự tăng trưởng theo năm:
- **Mục tiêu:** Khảo sát nhịp độ phát triển dài hạn và đo lường mức độ bùng nổ trong việc ứng dụng AI vào các code commit qua từng năm.
- **Phân tích:** Năm 2022 chỉ có 55 khối (0,3%), đều từ tháng 12. Số khối tăng từ 1.539 (2023) lên 4.001 (2024) và 11.382 (2025, 52,9% trong tổng số 21.498 khối). Năm 2026 chỉ có dữ liệu quý 1 (4.521 khối), nên không so sánh trực tiếp với các năm đủ 12 tháng.
- **Giới hạn:** Dữ liệu bắt đầu từ 3/12/2022, sau ngày ChatGPT ra mắt (30/11/2022), nên không so sánh được giai đoạn trước và sau ChatGPT. Hoạt động chung trên GitHub cũng tăng trong giai đoạn này, nên cần chuẩn hóa theo số lần push trước khi kết luận về tốc độ tăng.
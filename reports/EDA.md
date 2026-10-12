# Rise in AI commits - Báo cáo EDA

## Tổng quan

Dự án này nhằm khảo sát xu hướng sử dụng AI trong các dự án IT, cụ thể là xem AI đang được dùng nhiều nhất ở đâu, trong loại công việc nào (viết hàm mới, sửa lỗi, viết test, ...), và mức độ đóng góp của AI vào từng đoạn code (viết toàn bộ hay chỉ hỗ trợ một phần). Từ những quan sát này, mục tiêu cuối cùng là đưa ra một số gợi ý về việc nên và không nên dùng AI trong trường hợp nào khi lập trình.

Dữ liệu được thu thập từ các repository công khai trên GitHub, dựa vào các comment trong code có nhắc đến AI (ví dụ "written by ChatGPT", "AI generated", ...) để xác định những đoạn code có khả năng do AI tạo ra hoặc hỗ trợ. Sau khi thu thập, dữ liệu sẽ được phân tích thêm để xem các đoạn code này có bị chỉnh sửa lại sau đó hay không, dựa vào thời điểm của lần thay đổi đầu tiên (change_commit_date). Đây là cơ sở để đánh giá mức độ đáng tin cậy của code do AI viết.

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
| commit_url | string | Đường dẫn tới commit trên GitHub chứa đoạn code này. Cột này không có sẵn trong dữ liệu gốc, được suy ra từ đường dẫn file (blob url) rồi chuyển đổi thành đường dẫn commit |
| file | string | Đường dẫn tương đối của file trong repository, tính từ thư mục gốc |
| code_block | string | Đoạn code thực tế được match với comment liên quan đến AI. Ký tự xuống dòng trong code được thay bằng chuỗi ký tự "\n" để tránh làm hỏng định dạng khi lưu vào file csv |
| commit_date | datetime (UTC, ISO 8601) | Thời điểm commit nêu trên được tạo ra, được truy vấn thêm từ GitHub API do dữ liệu gốc không có sẵn. Có thể bị thiếu (null) trong một số trường hợp, xem phần Dữ liệu bị thiếu |
| change_commit_url | string | Đường dẫn tới commit đầu tiên sửa đổi đoạn code này sau khi được tạo ra (nếu có), lấy trực tiếp từ dữ liệu gốc |
| change_commit_date | datetime (UTC, ISO 8601) | Thời điểm của commit sửa đổi nêu trên. Bị để trống nếu đoạn code chưa từng được sửa lại, xem phần Dữ liệu bị thiếu |
| task_type (dự kiến bổ sung) | string | Loại công việc mà đoạn code do AI thực hiện, ví dụ viết hàm mới, sửa lỗi, viết test, viết docstring, refactor, ... Cột này chưa có trong dữ liệu hiện tại, sẽ được gắn nhãn ở bước tiếp theo |
| contribution_type (dự kiến bổ sung) | string | Mức độ đóng góp của AI vào đoạn code, ví dụ viết toàn bộ, hỗ trợ một phần, hoặc chỉ gợi ý/chỉnh sửa nhỏ. Cũng sẽ được gắn nhãn ở bước tiếp theo |

## Quy trình xử lý và chuẩn hoá dữ liệu thô

Dữ liệu gốc nằm trong 2 file jsonl:
- comment_codeblock_dataset.jsonl: chứa toàn bộ các đoạn code được match với comment liên quan đến AI
- comment_codeblock_first_change_dataset.jsonl: chứa thông tin về lần commit đầu tiên sửa đổi các đoạn code đó (nếu có)

Các bước xử lý chính như sau:

1. Đọc cả 2 file jsonl bằng pandas, sau đó merge lại với nhau bằng left join để giữ nguyên toàn bộ số dòng của bảng gốc, đồng thời bổ sung thêm thông tin thay đổi nếu match được.
2. Tạo bảng output mới, lấy các cột cần thiết từ dataset gốc và đổi tên lại cho ngắn gọn, rõ ràng hơn (id, repo, language, file, code_block).
3. Dữ liệu gốc chỉ có đường dẫn tới file (blob url) chứ không có đường dẫn tới commit, do đó cần parse lại đường dẫn file để suy ra đường dẫn commit tương ứng.
4. Dữ liệu gốc cũng không có sẵn ngày commit, nên cần gọi thêm GitHub API để lấy. Cách tiếp cận ban đầu là lấy file .patch của từng commit (không cần token xác thực) rồi tìm dòng "Date:" trong nội dung trả về. Tuy nhiên cách này thất bại ở phần lớn số dòng (khoảng 97%), do GitHub từ chối render file patch khi diff quá lớn hoặc commit có chứa nội dung nhị phân. Sau đó, quy trình được chuyển sang dùng GitHub API chính thức (GraphQL) để lấy riêng ngày commit mà không cần render toàn bộ diff, giúp tỉ lệ thất bại giảm xuống còn khoảng 3%.
5. Do số lượng commit cần truy vấn khá lớn, để tránh vượt giới hạn số lượng request của GitHub và rút ngắn thời gian xử lý, các kỹ thuật sau được áp dụng: loại bỏ các đường dẫn commit bị trùng lặp trước khi gọi API (do nhiều dòng dữ liệu có thể trỏ đến cùng một commit), gộp nhiều commit vào chung một truy vấn GraphQL duy nhất (batching), và thực hiện nhiều truy vấn song song bằng multithreading.
6. Bổ sung 2 cột change_commit_url và change_commit_date từ dataset gốc vào bảng output.
7. Xuất bảng kết quả ra file csv, lưu vào thư mục data/interim để phục vụ cho các bước xử lý tiếp theo.

## Hướng xử lý Dữ liệu bị thiếu (Data Cleaning)

Trong bảng dữ liệu sau khi chuẩn hoá, có 2 cột chính bị thiếu giá trị ở một số dòng. Dựa trên tính chất của từng loại missing data, chúng tôi đã đưa ra các hướng xử lý cụ thể như sau:

**1. Cột `commit_date` (Thiếu ngẫu nhiên do lỗi 404 - ~3.1%)**:
Khoảng 1.082/35.278 dòng (tương ứng 486 commit duy nhất) không lấy được ngày commit. Kết quả ping trực tiếp bằng HTTP Request cho thấy 100% các URL này trả về lỗi 404 (Not Found) hoặc 429 (Rate Limit). Nguyên nhân:
- Repository đã bị xóa hoặc chuyển sang chế độ private sau thời điểm dữ liệu gốc được thu thập.
- Lịch sử commit bị ghi đè (ví dụ force push hoặc amend).
- Repository bị đổi tên hoặc chuyển chủ sở hữu.
**-> Hướng xử lý (Quyết định): Xóa bỏ (Drop)** toàn bộ 1.082 dòng này. Do dữ liệu thiếu ngày tháng sẽ không có ý nghĩa khi phân tích xu hướng chuỗi thời gian (time-series) và tỷ lệ 3.1% là rất nhỏ, việc xóa không làm ảnh hưởng đến tính đại diện của dữ liệu.

**2. Cột `change_commit_url` và `change_commit_date` (Thiếu có chủ đích MNAR - ~63.1%)**:
Khoảng 22.282/35.278 dòng bị để trống ở 2 cột này. Đây không phải là lỗi rỗng dữ liệu, mà phản ánh một sự thật ngầm hiểu (insight) quan trọng: những đoạn code AI sinh ra ở các dòng này **chưa từng bị con người chỉnh sửa lại** kể từ lúc được commit.
**-> Hướng xử lý (Quyết định): Không xóa (Giữ nguyên và Feature Engineering)**. Chúng tôi biến sự khuyết thiếu này thành một Đặc trưng (Feature) mới mang tên `is_modified` (kiểu Boolean). 
- Nếu có ngày chỉnh sửa: `is_modified = True` (Code AI đã bị sửa).
- Nếu để trống (NaN): `is_modified = False` (Code AI được giữ nguyên bản). Các ô NaN sau đó được lấp đầy (Fillna) bằng chuỗi `"Not Modified"` để phục vụ trực quan hóa.

## Công cụ sử dụng

- Python: ngôn ngữ chính được dùng để viết toàn bộ pipeline xử lý dữ liệu
- Jupyter Notebook: môi trường thực thi code theo từng bước, thuận tiện cho việc kiểm tra kết quả ở mỗi giai đoạn
- pandas: đọc file jsonl/csv, xử lý và merge dữ liệu dạng bảng
- requests: gửi request tới API của GitHub
- GitHub GraphQL API: truy vấn metadata của commit (cụ thể là ngày commit), được dùng thay cho phương pháp scrape trực tiếp vì cho kết quả nhanh và ổn định hơn
- concurrent.futures (ThreadPoolExecutor): thực hiện nhiều request song song để rút ngắn thời gian xử lý
- Các thư viện chuẩn khác: os, io (StringIO), datetime, time, phục vụ việc đọc file, tạo thư mục và quản lý thời gian khi xuất file

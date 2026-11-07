# Sự tăng truởng của commit hỗ trợ bởi AI

> [!NOTE]
> Đây là dự án "Khoa học dữ liệu" của sinh viên truờng Đại học CMC.

## Thông tin dự án
Kho lưu trữ này chứa tập hợp dữ liệu và các phân tích liên quan đến sự gia tăng số lượng commit liên quan đến AI trong nhiều dự án mã nguồn mở khác nhau. Mục tiêu là phân tích dữ liệu và trực quan hóa các xu hướng sử dụng AI của các lập trình viên theo thời gian, cũng như xác định những tác vụ cụ thể mà AI hỗ trợ, từ đó rút ra những thông tin hữu ích để đưa ra các dự đoán và khuyến nghị.

Các dữ liệu đã đuợc trích xuất từ repo sau: https://github.com/MSwadhin/empirical-study-dev-ai-usage

## Thông tin mã nguồn
Dự án đuợc triển khai hoàn toàn bằng Python + Jupyter Notebook

Cấu trúc:
```
Rise-in-AI-commits/
├── data/
│   ├── interim/            # Các dữ liệu đang đuợc xử lý
│   ├── processed/          # Các dữ liệu đã đuợc xử lý
├── notebooks/              # Các script Jupyter Notebook chính của dự án
├── reports/                # Các báo cáo liên quan đến dự án
├── src/                    # Các script hỗ trợ
├── .gitignore
├── requirements.txt
└── README.md
```

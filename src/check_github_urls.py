import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib3
import os

urllib3.disable_warnings()

input_csv = r"data\interim\missing_cases_extracted\missing_commit_date.csv"
output_csv = r"data\interim\missing_cases_extracted\url_status_check.csv"

print("Reading data from file:", input_csv)
df = pd.read_csv(input_csv)

# Lọc ra các URL cần kiểm tra
urls = df['commit_url'].dropna().unique().tolist()
print(f"Total unique URLs to check: {len(urls)}")

def check_url(url):
    try:
        # Cấu hình headers để giả mạo trình duyệt, tránh bị block
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        resp = requests.head(url, headers=headers, allow_redirects=True, timeout=10)
        
        # Nếu GitHub chặn method HEAD (405) thì dùng GET thử lại
        if resp.status_code == 405:
            resp = requests.get(url, headers=headers, allow_redirects=True, timeout=10, stream=True)
            
        return url, resp.status_code
    except Exception as e:
        return url, "Error/Timeout"

results = []
print("Pinging URLs... (please wait 1-2 minutes)")

# Sử dụng ThreadPoolExecutor để ping song song 15 request cùng lúc cho nhanh
completed = 0
with ThreadPoolExecutor(max_workers=15) as executor:
    future_to_url = {executor.submit(check_url, url): url for url in urls}
    for future in as_completed(future_to_url):
        url, status = future.result()
        results.append({"commit_url": url, "http_status": status})
        
        completed += 1
        if completed % 100 == 0:
            print(f"Checked {completed}/{len(urls)} URLs...")

print(f"Finished checking {completed}/{len(urls)} URLs!")

# Tạo DataFrame kết quả và merge vào dữ liệu ban đầu
status_df = pd.DataFrame(results)
df_merged = df.merge(status_df, on='commit_url', how='left')

# Lưu kết quả
df_merged.to_csv(output_csv, index=False)

print("\n" + "="*40)
print("HTTP STATUS SUMMARY:")
summary = df_merged['http_status'].value_counts()
for status, count in summary.items():
    if str(status) == '200':
        print(f" - [200 OK] (Working link): {count} links")
    elif str(status) == '404':
        print(f" - [404 Not Found] (Dead link): {count} links")
    elif str(status) == '429':
        print(f" - [429 Too Many Requests] (Rate limited): {count} links")
    else:
        print(f" - [Status {status}]: {count} links")
print("="*40)

print(f"\nDetailed results saved to: {output_csv}")

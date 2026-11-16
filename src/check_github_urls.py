import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib3
from pathlib import Path

urllib3.disable_warnings()

EXTRACT_DIR = Path(__file__).resolve().parents[1] / "data" / "interim" / "missing_cases_extracted"
input_csv = EXTRACT_DIR / "missing_commit_date.csv"
output_csv = EXTRACT_DIR / "url_status_check.csv"

print("Reading data from file:", input_csv)
df = pd.read_csv(input_csv)

url_col = "repo_url" if "repo_url" in df.columns else "commit_url"
urls = df[url_col].dropna().unique().tolist()
print(f"Total unique URLs to check ({url_col}): {len(urls)}")

def check_url(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        resp = requests.head(url, headers=headers, allow_redirects=True, timeout=10)
        if resp.status_code == 405:
            resp = requests.get(url, headers=headers, allow_redirects=True, timeout=10, stream=True)
        return url, resp.status_code
    except Exception:
        return url, "Error/Timeout"

results = []
print("Pinging URLs... (please wait 1-2 minutes)")

completed = 0
with ThreadPoolExecutor(max_workers=15) as executor:
    future_to_url = {executor.submit(check_url, url): url for url in urls}
    for future in as_completed(future_to_url):
        url, status = future.result()
        results.append({url_col: url, "http_status": status})
        completed += 1
        if completed % 100 == 0:
            print(f"Checked {completed}/{len(urls)} URLs...")

print(f"Finished checking {completed}/{len(urls)} URLs!")

status_df = pd.DataFrame(results)
df_merged = df.merge(status_df, on=url_col, how="left")
df_merged.to_csv(output_csv, index=False)

print("\n" + "=" * 40)
print("HTTP STATUS SUMMARY:")
summary = df_merged["http_status"].value_counts()
for status, count in summary.items():
    if str(status) == "200":
        print(f" - [200 OK] (Working link): {count} links")
    elif str(status) == "404":
        print(f" - [404 Not Found] (Dead link): {count} links")
    elif str(status) == "429":
        print(f" - [429 Too Many Requests] (Rate limited): {count} links")
    else:
        print(f" - [Status {status}]: {count} links")
print("=" * 40)
print(f"\nDetailed results saved to: {output_csv}")

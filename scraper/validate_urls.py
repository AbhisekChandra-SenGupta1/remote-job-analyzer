import requests
import pandas as pd
import time
import re
from urllib.parse import urlparse

INPUT = "data/processed/wwr_jobs_clean.csv"
OUTPUT = "data/raw/url_validation_report.csv"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (educational project; URL validation check; contact: your-email@example.com)"
}
DELAY = 2            # same politeness standard used throughout the scraper
CHECKPOINT_EVERY = 50

# Set to a small number (e.g. 10) to pilot before checking all 285 -- same discipline
# as Step 4B: never run a new network script at full scale untested.
LIMIT = None

JOB_PATH = re.compile(r"^/remote-jobs/[^/]+$")
CATEGORY_PATH = re.compile(r"^/categories/")


def classify_final(final_path):
    if JOB_PATH.match(final_path):
        return "job_page"
    if final_path == "/remote-jobs":
        return "general_jobs_page"
    if CATEGORY_PATH.match(final_path):
        return "category_page"
    if final_path in ("", "/"):
        return "homepage"
    return "other"


def check_url(url, retries=3):
    for attempt in range(retries):
        try:
            return requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True), None
        except requests.RequestException as e:
            wait = 2 ** attempt
            print(f"    attempt {attempt + 1} failed ({e}); retrying in {wait}s")
            time.sleep(wait)
    return None, "request_failed_after_retries"


def main():
    df = pd.read_csv(INPUT)
    df = df.dropna(subset=["url"]).drop_duplicates(subset="url").reset_index(drop=True)
    if LIMIT:
        df = df.head(LIMIT)
        print(f"LIMIT set -- checking only the first {LIMIT} rows as a pilot run.\n")

    results = []
    for i, row in df.iterrows():
        url = row["url"]
        print(f"[{i + 1}/{len(df)}] {str(row['title'])[:50]!r} -> {url}")

        original_path = urlparse(url).path.rstrip("/")
        original_looks_like_job_url = bool(JOB_PATH.match(original_path))

        resp, error = check_url(url)

        if resp is None:
            results.append({
                "title": row["title"], "company": row["company"],
                "original_url": url, "original_looks_like_job_url": original_looks_like_job_url,
                "final_url": None, "http_status": None,
                "redirect_detected": None, "num_redirects": None,
                "url_status": "error_request_failed", "error_message": error,
            })
        else:
            final_path = urlparse(resp.url).path.rstrip("/")

            if resp.status_code == 404:
                status = "error_404"
            elif resp.status_code >= 400:
                status = f"error_http_{resp.status_code}"
            else:
                landed_on = classify_final(final_path)
                if landed_on == "job_page" and final_path == original_path:
                    status = "valid_job_page"
                elif landed_on == "job_page":
                    status = "redirected_to_different_job"
                elif landed_on == "general_jobs_page":
                    status = "redirected_to_general_jobs_page"
                elif landed_on == "category_page":
                    status = "redirected_to_category"
                elif landed_on == "homepage":
                    status = "redirected_to_homepage"
                else:
                    status = "redirected_to_other"

            results.append({
                "title": row["title"], "company": row["company"],
                "original_url": url, "original_looks_like_job_url": original_looks_like_job_url,
                "final_url": resp.url, "http_status": resp.status_code,
                "redirect_detected": len(resp.history) > 0, "num_redirects": len(resp.history),
                "url_status": status, "error_message": None,
            })

        if (i + 1) % CHECKPOINT_EVERY == 0:
            pd.DataFrame(results).to_csv(OUTPUT, index=False)
            print(f"  checkpoint saved at {i + 1} rows")

        time.sleep(DELAY)

    report = pd.DataFrame(results)
    report.to_csv(OUTPUT, index=False)
    print(f"\nSaved {len(report)} rows to {OUTPUT}")

    print("\n--- url_status breakdown ---")
    print(report["url_status"].value_counts())
    print("\n--- original_looks_like_job_url breakdown ---")
    print(report["original_looks_like_job_url"].value_counts())
    print("\n--- Cross-tab: was the STORED url ever valid, vs. what it resolves to NOW ---")
    print(pd.crosstab(report["original_looks_like_job_url"], report["url_status"]))


if __name__ == "__main__":
    main()
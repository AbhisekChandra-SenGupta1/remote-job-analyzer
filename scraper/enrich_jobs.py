import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import glob

BASE_URL = "https://weworkremotely.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (educational project; contact: your-email@example.com)"
}

DELAY = 2


def fetch_page(url, retries=3):
    """Fetch a job detail page with retries."""

    for attempt in range(retries):
        try:
            r = requests.get(
                url,
                headers=HEADERS,
                timeout=15
            )

            if r.status_code == 404:
                print("    404 - job no longer exists, skipping")
                return None

            r.raise_for_status()

            return BeautifulSoup(r.text, "lxml")

        except requests.RequestException as e:
            wait = 2 ** attempt

            print(
                f"    attempt {attempt + 1} failed ({e}); "
                f"retrying in {wait}s"
            )

            time.sleep(wait)

    print(f"    GIVING UP on {url}")

    return None


def parse_job_detail(soup):
    """Extract fields from the About the Job section."""

    result = {
        "posted_on": None,
        "apply_before": None,
        "job_type": None,
        "category_detail": None,
        "region": [],
        "skills": []
    }

    about = soup.find(
        "div",
        class_="lis-container__job__sidebar__job-about"
    )

    if not about:
        return result

    for li in about.find_all(
        "li",
        class_="lis-container__job__sidebar__job-about__list__item"
    ):

        parts = list(li.stripped_strings)

        if not parts:
            continue

        label = parts[0].strip().rstrip(":").lower()

        values = parts[1:]

        if label == "posted on":
            result["posted_on"] = (
                values[0] if values else None
            )

        elif label == "apply before":
            result["apply_before"] = (
                values[0] if values else None
            )

        elif label == "job type":
            result["job_type"] = (
                values[0] if values else None
            )

        elif label == "category":
            result["category_detail"] = (
                values[0] if values else None
            )

        elif label == "region":
            result["region"] = values

        elif label == "skills":
            result["skills"] = values

    return result


def enrich(input_csv, output_csv, limit=None):
    """Read the scraped jobs and enrich them from detail pages."""

    df = pd.read_csv(input_csv)

    # Remove jobs without URLs
    df = df.dropna(
        subset=["url"]
    )

    # Remove duplicate job URLs
    df = df.drop_duplicates(
        subset="url"
    ).reset_index(drop=True)

    # Optional limit for testing
    if limit:
        df = df.head(limit)

    rows = []

    for i, row in df.iterrows():

        print(
            f"[{i + 1}/{len(df)}] {row['title']}"
        )

        soup = fetch_page(row["url"])

        if soup:
            details = parse_job_detail(soup)
        else:
            details = {
                "posted_on": None,
                "apply_before": None,
                "job_type": None,
                "category_detail": None,
                "region": [],
                "skills": []
            }

        # Combine original listing data
        # with detail-page data
        rows.append({
            **row.to_dict(),
            **details
        })

        # Polite delay between requests
        time.sleep(DELAY)

    result = pd.DataFrame(rows)

    result.to_csv(
        output_csv,
        index=False
    )

    print(
        f"\nSaved {len(result)} enriched jobs "
        f"to {output_csv}"
    )

    return result


if __name__ == "__main__":

    # Find the original timestamped scraper output.
    # Do NOT accidentally use the enriched files.
    files = glob.glob(
        "data/raw/wwr_jobs_*.csv"
    )

    files = [
        f for f in files
        if "enriched" not in f
    ]

    if not files:
        print(
            "No original WWR jobs CSV found "
            "in data/raw/"
        )

    else:

        latest = sorted(files)[-1]

        print(
            f"Using {latest} as input"
        )

        enrich(
            latest,
            "data/raw/wwr_jobs_enriched.csv"
        )
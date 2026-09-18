import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime

BASE_URL = "https://weworkremotely.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (educational project; contact: your-email@example.com)"
}

DELAY = 2

CATEGORIES = {
    "Full-Stack Programming": "/categories/remote-full-stack-programming-jobs",
    "Front-End Programming": "/categories/remote-front-end-programming-jobs",
    "Back-End Programming": "/categories/remote-back-end-programming-jobs",
    "DevOps & Sysadmin": "/categories/remote-devops-sysadmin-jobs",
    "Design": "/categories/remote-design-jobs",
    "Product": "/categories/remote-product-jobs",
    "Customer Support": "/categories/remote-customer-support-jobs",
    "Sales & Marketing": "/categories/remote-sales-and-marketing-jobs",
    "Management & Finance": "/categories/remote-management-and-finance-jobs",
}


def fetch_page(url, retries=3):
    """Fetch a page with retries and exponential backoff."""

    for attempt in range(retries):
        try:
            response = requests.get(
                url,
                headers=HEADERS,
                timeout=15
            )

            response.raise_for_status()

            return BeautifulSoup(response.text, "lxml")

        except requests.RequestException as e:

            wait = 2 ** attempt

            print(
                f"    attempt {attempt + 1} failed ({e}); "
                f"retrying in {wait}s"
            )

            time.sleep(wait)

    print(f"    GIVING UP on {url}")

    return None


def parse_listing(li):

    data = {}

    # Job URL
    link = li.find(
        "a",
        class_="listing-link--unlocked",
        href=True
    )

    data["url"] = (
        BASE_URL + link["href"]
        if link
        else None
    )

    # Job title
    title = li.find(
        "span",
        class_="new-listing__header__title__text"
    )

    data["title"] = (
        title.get_text(strip=True)
        if title
        else None
    )

    # Company
    company = li.find(
        "p",
        class_="new-listing__company-name"
    )

    data["company"] = (
        company.get_text(strip=True)
        if company
        else None
    )

    # Company headquarters
    hq = li.find(
        "p",
        class_="new-listing__company-headquarters"
    )

    data["company_location"] = (
        hq.get_text(strip=True)
        if hq
        else None
    )

    # Tags
    tags = li.find(
        "div",
        class_="new-listing__categories"
    )

    data["tags"] = (
        list(tags.stripped_strings)
        if tags
        else []
    )

    # Hot job
    data["is_hot"] = (
        li.find(
            "i",
            class_="new-listing__header__title__hot-icon"
        )
        is not None
    )

    return data


def scrape_category(name, path, max_pages=5):

    print(f"\n[{name}]")

    all_jobs = []
    seen_urls = set()

    for page in range(1, max_pages + 1):

        if page == 1:
            url = f"{BASE_URL}{path}"
        else:
            url = f"{BASE_URL}{path}?page={page}"

        soup = fetch_page(url)

        if soup is None:
            break

        results = soup.find(
            "div",
            id="search-results"
        )

        if results:

            listings = results.find_all(
                "li",
                class_="new-listing-container"
            )

        else:

            listings = []

        if not listings:
            break

        parsed = [
            parse_listing(li)
            for li in listings
        ]

        # Remove promotional cards
        # that do not contain a real job URL/title
        valid = [
            job
            for job in parsed
            if job["url"] and job["title"]
        ]

        skipped = len(parsed) - len(valid)

        # Remove duplicate URLs
        new = [
            job
            for job in valid
            if job["url"] not in seen_urls
        ]

        for job in new:
            seen_urls.add(job["url"])

        all_jobs.extend(new)

        print(
            f"  page {page}: "
            f"{len(listings)} found, "
            f"{skipped} skipped, "
            f"{len(new)} new"
        )

        # Stop if pagination is no longer
        # producing new jobs
        if not new:
            break

        time.sleep(DELAY)

    # Add category
    for job in all_jobs:
        job["category"] = name

    print(
        f"  -> {len(all_jobs)} unique jobs"
    )

    return all_jobs


if __name__ == "__main__":

    everything = []

    for name, path in CATEGORIES.items():

        jobs = scrape_category(
            name,
            path
        )

        everything.extend(jobs)

        time.sleep(DELAY)

    df = pd.DataFrame(everything)

    # Add scrape timestamp
    df["scraped_at"] = datetime.now().isoformat(
        timespec="seconds"
    )

    # Cross-category deduplication
    before = len(df)

    df = df.drop_duplicates(
        subset="url",
        keep="first"
    )

    print(
        f"\nTotal: {before} rows "
        f"-> {len(df)} after cross-category dedup"
    )

    # Timestamped output filename
    stamp = datetime.now().strftime(
        "%Y%m%d_%H%M"
    )

    output_file = (
        f"data/raw/wwr_jobs_{stamp}.csv"
    )

    df.to_csv(
        output_file,
        index=False
    )

    print(
        f"Saved to {output_file}"
    )

    print("\nJobs per category:")

    print(
        df["category"].value_counts()
    )
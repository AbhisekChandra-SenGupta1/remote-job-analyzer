import requests
from bs4 import BeautifulSoup
import pandas as pd

BASE_URL = "https://weworkremotely.com"
CATEGORY_URL = f"{BASE_URL}/categories/remote-full-stack-programming-jobs"
HEADERS = {"User-Agent": "Mozilla/5.0 (educational project; contact: your-email@example.com)"}

# --- Save a snapshot of the RAW html so we can inspect what we actually received ---
html = requests.get(CATEGORY_URL, headers=HEADERS, timeout=10).text
with open("data/raw/category_snapshot.html", "w", encoding="utf-8") as f:
    f.write(html)
print(f"Raw HTML saved: {len(html):,} characters\n")

# --- Q1: Does the hot icon exist in the RAW html at all? ---
print("hot-icon class occurrences:", html.count("new-listing__header__title_hot-icon"))
print("'fa-fire' occurrences:      ", html.count("fa-fire"))

# --- Q2 & Q3: inspect the scraped data ---
df = pd.read_csv("data/raw/full_stack_programming_jobs.csv")
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 250)
pd.set_option("display.max_colwidth", 40)

print("\n--- Null counts per column ---")
print(df.isna().sum())

print("\n--- Rows missing a URL ---")
print(df[df["url"].isna()])

print("\n--- Duplicated URLs (appearing more than once) ---")
dupes = df[df.duplicated("url", keep=False) & df["url"].notna()]
print(f"{len(dupes)} rows involved in duplication")
print(dupes.sort_values("url")[["title", "company", "url"]].head(12))

print("\n--- First 5 rows, all columns ---")
print(df.head())
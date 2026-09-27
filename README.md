# 🌍 Remote Job Market Intelligence Dashboard

An end-to-end Python data analytics project that scrapes real remote job postings, cleans and enriches them, validates their live status, and presents them through a multi-page interactive Streamlit dashboard — including a fully transparent, deterministic (non-AI) skill-matching tool.

Originally started as the Web Scraping task for the CodeAlpha Data Analytics Internship, then substantially extended into a complete scrape-to-dashboard analytics platform.

## 🚀 Live Demo

[Open the Remote Job Market Intelligence Dashboard](https://remote-job-analyzer.streamlit.app)
---

## Overview

This project scrapes remote job listings from [We Work Remotely](https://weworkremotely.com) across 9 job categories, enriches each listing with structured detail-page data (skills, region, job type, deadlines), cleans and normalizes the dataset, validates which listings are still live, and surfaces all of it through a 5-page Streamlit dashboard.

The current committed dataset snapshot contains:

| Metric | Value |
|---|---|
| Unique job postings | 285 |
| Categories | 9 |
| Snapshot date | September 16, 2026 |
| Listings with structured skill tags | 57 / 285 (20.0%) |
| URLs currently resolving to a live job page | 132 / 285 |
| URLs currently redirecting (listing no longer available) | 153 / 285 |

These numbers are computed live from the dataset by the dashboard itself (not hardcoded), and will change if the pipeline is re-run on a fresh scrape.

---

## Key Features

- **Custom web scraper** (`requests` + `BeautifulSoup`) across 9 remote job categories, with retry-with-backoff, rate limiting, a descriptive User-Agent, and URL-based deduplication (handles the source site's non-deterministic listing order).
- **Detail-page enrichment** — pulls structured skills, region eligibility, job type, posting date, and application deadline from each individual job page.
- **Data cleaning pipeline** — fixes real issues found during development: category-naming normalization (`&` vs `and`), safe list-column CSV round-tripping, and relative/absolute date parsing.
- **One-time URL availability validation** — every listing's URL is checked against where it currently resolves, so the dashboard never shows a broken "Open Job" link that silently redirects to a homepage or category page.
- **5-page interactive Streamlit dashboard** with reactive filters, sortable job cards, and cross-page-consistent metrics.
- **Deterministic Candidate Match** — transparent skill-overlap matching with an explicit formula, matched/missing skill breakdown, and no AI or inferred skills involved.
- **Data-quality transparency throughout** — the 20% structured-skill-coverage limitation is disclosed everywhere it affects a result, not just in a footnote; unavailable historical listings are kept, not deleted.

---

## Dashboard Pages

| Page | Purpose |
|---|---|
| 📊 **Market Overview** | KPIs, category distribution, top skills, and top hiring companies, with reactive category/hot-job/search filters. |
| 🔍 **Job Explorer** | Browsable job cards with freshness ("New today" / "This week" / "Older") and deadline-urgency badges, sorting, and category/job-type/hot filters. |
| 🎯 **Candidate Match** | Pick your skills and see a deterministic match percentage per job, with matched/missing skills shown explicitly — scoped only to listings with structured skill tags. |
| 📈 **Market Insights** | Category comparison, company concentration, skill demand, freshness distribution, and auto-generated (template-based, not AI-generated) factual snapshot statistics. |
| 📋 **Methodology** | Full data-engineering write-up: data source, collection approach, real bugs found and fixed, skill-coverage limitations, URL validation methodology, and known dataset limitations. |

---

## Data Pipeline

```
scrape → enrich → clean → validate URLs → analyze / dashboard
```

| Stage | Script | Output |
|---|---|---|
| Scrape | `scraper/scrape_jobs.py` | `data/raw/wwr_jobs_<timestamp>.csv` |
| Enrich | (part of the scraper's detail-page fetch) | adds skills, region, job type, dates |
| Clean | `processing/clean_data.py` | `data/processed/wwr_jobs_clean.csv` |
| Validate URLs | `scraper/validate_urls.py` | `data/raw/url_validation_report.csv` |
| Merge availability | `processing/add_url_status.py` | updates `wwr_jobs_clean.csv` with a `url_status` column |
| Analyze | `analysis/metrics.py` | shared functions used by every dashboard page |

The repository ships with an already-scraped, cleaned, and validated snapshot in `data/processed/wwr_jobs_clean.csv`, so the dashboard runs immediately without needing to re-scrape anything.

---

## Dataset & Validation Approach

- **Source:** We Work Remotely's public job category pages. Its `robots.txt` explicitly permits crawling job listing pages.
- **Snapshot, not live feed:** all data reflects a single scrape at a fixed point in time, not a continuously updating source.
- **Skill data is genuinely partial:** only 20% of listings include a structured "Skills" field on their detail page. Every skill-based feature in the dashboard (Top Skills, Candidate Match) discloses this directly next to the relevant result.
- **Listing availability is separately validated:** after scraping, every job URL was checked to see whether it still resolves to an individual job page. Listings that now redirect elsewhere are kept in the dataset (this is a historical snapshot) but no longer show a clickable "Open Job" link.
- **Full detail:** see the in-app **Methodology** page for the complete write-up, including specific bugs found during development and how each was diagnosed and fixed.

---

## Technology Stack

- **Python 3**
- **Scraping:** `requests`, `beautifulsoup4`, `lxml`
- **Data processing:** `pandas`
- **Dashboard:** `streamlit`, `plotly`

---

## Project Structure

```
remote-job-analyzer/
├── analysis/
│   └── metrics.py                     # shared data/analytics functions used by every dashboard page
├── dashboard/
│   ├── common.py                      # shared cached data loader
│   ├── 📊_Market_Overview.py          # main dashboard entry point
│   └── pages/
│       ├── 1_🔍_Job_Explorer.py
│       ├── 2_🎯_Candidate_Match.py
│       ├── 3_📈_Market_Insights.py
│       └── 4_📋_Methodology.py
├── data/
│   ├── raw/                           # scrape output + validation report (gitignored, regenerable)
│   └── processed/
│       └── wwr_jobs_clean.csv         # committed snapshot the dashboard runs on
├── notebooks/
│   └── eda.py                         # exploratory analysis (VS Code # %% cell format)
├── processing/
│   ├── clean_data.py
│   └── add_url_status.py
├── scraper/
│   ├── scrape_jobs.py
│   └── validate_urls.py
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Setup Instructions

```bash
# Clone the repository
git clone https://github.com/AbhisekChandra-SenGupta1/remote-job-analyzer.git
cd remote-job-analyzer

# Create and activate a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## How to Run

**Just want the dashboard?** The repository already includes a cleaned, validated data snapshot — skip straight to step 4.

```bash
# 1. Scrape fresh listings (optional — a snapshot is already included)
python scraper/scrape_jobs.py

# 2. Clean and normalize the scraped data
python processing/clean_data.py

# 3. (Optional) Validate which listings are still live, then merge the result in
python scraper/validate_urls.py
python processing/add_url_status.py

# 4. Launch the dashboard
streamlit run "dashboard/📊_Market_Overview.py"
```

The dashboard opens at `http://localhost:8501`.

---

## Screenshots

_Screenshots to be added._

### Market Overview
*(placeholder)*

### Job Explorer
*(placeholder)*

### Candidate Match
*(placeholder)*

### Market Insights
*(placeholder)*

### Methodology
*(placeholder)*

---

## Limitations

- **Single snapshot, not a live feed.** All figures reflect one scrape at a fixed point in time. A genuine "postings over time" trend view would require repeated scrapes across multiple days.
- **Structured skill data covers only 20% of listings.** Skill-based features are explicitly scoped to that subset and cannot evaluate the remaining 80%.
- **Region data has low diversity** in this snapshot — most tagged listings list "Anywhere in the World," limiting how useful a region-based filter would be.
- **No salary data exists in the source**, so this project makes no salary-related claims anywhere.
- **URL availability reflects one validation pass** and will drift out of date as more listings close over time.

Full detail on all of the above is documented on the dashboard's own **Methodology** page.

---

## Status

V2 complete: all 5 dashboard pages implemented and manually verified. Automated tests and live deployment are tracked as next steps.

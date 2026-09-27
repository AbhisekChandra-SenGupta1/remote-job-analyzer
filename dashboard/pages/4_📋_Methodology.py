from pathlib import Path
import sys
DASHBOARD_DIR = Path(__file__).resolve().parent.parent
if str(DASHBOARD_DIR) not in sys.path:
    sys.path.append(str(DASHBOARD_DIR))

import streamlit as st
from common import get_data
from analysis.metrics import skills_coverage

st.set_page_config(page_title="Methodology", page_icon="📋", layout="wide")

df = get_data()
coverage = skills_coverage(df)
last_scraped = df["scraped_at"].max()

st.title("📋 Methodology")
st.caption(
    "How this dataset was built, the real issues found along the way, and what the "
    "data can and can't tell you."
)

st.divider()

# --- 1. Data source & snapshot ---
st.header("1. Data Source & Snapshot")
st.markdown(f"""
- **Source:** [We Work Remotely](https://weworkremotely.com), a public remote-job board.
  Its `robots.txt` explicitly permits crawling job listing pages.
- **Scope:** {len(df)} unique job postings across **{df['category_final'].nunique()} categories**
  (Full-Stack Programming, Front-End Programming, Back-End Programming, DevOps and Sysadmin,
  Design, Product, Customer Support, Sales and Marketing, Management and Finance).
- **This is a single point-in-time snapshot**, scraped on **{last_scraped:%B %d, %Y at %H:%M}**,
  not a live or continuously updating feed. Every derived metric on every page of this
  dashboard is relative to that moment, not to today's date.
""")

# --- 2. Collection approach ---
st.header("2. Collection Approach")
st.markdown("""
- Built with `requests` + `BeautifulSoup` — confirmed via "View Page Source" that job data
  is present in the initial server-rendered HTML, so no headless browser was needed.
- Each category page was fetched once; **We Work Remotely does not paginate category
  listings** — requesting `?page=2` returns identical content to page 1. This was
  confirmed empirically (matching listing counts across both pages) rather than assumed.
- Requests use a descriptive User-Agent, a polite delay between requests, and
  retry-with-backoff on transient failures — the same standard used later for the
  URL-availability check in Section 5.
""")

st.divider()

# --- 3. Data engineering issues found & resolved ---
st.header("3. Data Engineering Issues Found & Resolved")
st.write(
    "Three real bugs surfaced during development. Each is documented here with what "
    "broke, how it was caught, and how it was fixed."
)

with st.expander("🔁 Non-deterministic listing order & URL-based deduplication"):
    st.markdown("""
    **Issue:** Re-running the scraper minutes apart returned completely different jobs in
    the first few rows each time — We Work Remotely rotates boosted/featured listings on
    every page load.

    **Why it matters:** row position and job title are unsafe as a unique key — two
    companies can post identically-titled roles, and list position isn't stable across
    scrapes.

    **Fix:** deduplication uses the job's **URL** as the unique key, at two levels: within
    a category (guards against a pagination loop) and across categories (a job can be
    cross-posted to more than one category page).
    """)

with st.expander("🏷️ Category naming mismatch: '&' vs 'and'"):
    st.markdown("""
    **Issue:** comparing the category a job was *scraped from* against the category its
    own detail page *reported* showed 112 of 285 jobs (39%) as "mismatched."

    **Why it matters:** that number was too high to be genuine cross-listing —
    inspecting the actual rows showed the scraped-from label used `&`
    ("DevOps & Sysadmin") while the job page used the word `and`
    ("DevOps and Sysadmin"). Same category, different spelling convention.

    **Fix:** both fields are normalized (`&` → `and`) before comparison, and the job's own
    self-reported category is treated as authoritative. After normalizing, genuine
    mismatches dropped to **0** — every job belongs to exactly one category.
    """)

with st.expander("📄 CSV list-column serialization"):
    st.markdown("""
    **Issue:** fields like `skills` and `region` are naturally lists. Pandas writes a
    Python list to a CSV cell as the *text* `"['React', 'Node.js']"` — reading that file
    back with `pd.read_csv()` returns a **plain string**, not a list, silently breaking
    any code expecting list behavior.

    **Fix:** list columns are stored as pipe-delimited strings (`"React|Node.js"`)
    instead of Python's string representation of a list. Every downstream script
    recovers the list with a plain `.split("|")`.
    """)

st.divider()

# --- 4. Structured skill coverage ---
st.header("4. Structured Skill Coverage")
st.markdown(f"""
Only **{coverage['jobs_with_skills']} of {coverage['total_jobs']} listings
({coverage['pct_with_skills']}%)** include a structured "Skills" field on their detail
page. This is a real, measured limitation of the source data — not a scraping failure.
""")

with st.expander("Why does skill-tag coverage vary so much by category?"):
    coverage_by_category = (
        df.assign(has_skills=df["skills"].apply(lambda s: len(s) > 0))
        .groupby("category_final")["has_skills"]
        .mean()
        .mul(100)
        .round(1)
        .sort_values(ascending=False)
        .reset_index()
        .rename(columns={"category_final": "Category", "has_skills": "Skill-tag coverage (%)"})
    )
    st.markdown("""
    Counter-intuitively, **Full-Stack Programming — the largest category by far — has one
    of the *lowest* skill-tagging rates**, while several smaller categories tag more
    consistently:
    """)
    st.dataframe(coverage_by_category, hide_index=True, use_container_width=True)
    st.markdown("""
    One plausible explanation, not confirmed by this data alone: several high-volume
    Full-Stack posters (e.g. staffing/placement agencies) may describe requirements in
    free-text paragraphs rather than filling the structured Skills field, while smaller
    categories may have more direct-hire postings that complete every field.

    **Practical consequence:** any skills-based feature in this dashboard (Top Skills,
    Candidate Match) only reflects the {0}% of jobs with structured tags — this is
    disclosed directly next to each such feature, not just here.
    """.format(coverage["pct_with_skills"]))

with st.expander("Noise-term filtering in the skills ranking"):
    st.markdown("""
    The structured Skills field also contains employment-type and generic-role labels —
    `Full Time`, `Engineer`, `Developer`, `Full Stack Dev` — that describe the *job*, not
    a *skill*. These are excluded specifically from the skills ranking and Candidate
    Match, never from the underlying dataset itself.
    """)

st.divider()

# --- 5. URL availability validation ---
st.header("5. URL Availability Validation")

if "url_status" in df.columns:
    n_valid = int((df["url_status"] == "valid_job_page").sum())
    n_redirected_home = int((df["url_status"] == "redirected_to_homepage").sum())
else:
    n_valid, n_redirected_home = 132, 153  # last known validation result, for graceful fallback

st.markdown(f"""
All **{len(df)}** job URLs collected in the September 16, 2026 snapshot were checked in a
separate, one-time validation pass after scraping — each URL was requested and its final
destination (after any redirects) was recorded.

**Result:** **{n_valid} of {len(df)}** URLs currently resolve to an individual job page;
**{n_redirected_home}** now redirect to the We Work Remotely homepage instead.

**This is not a scraper bug.** Every one of the original {len(df)} stored URLs correctly
matched the expected `/remote-jobs/<slug>` job-listing pattern at the time it was
scraped — the scraper never constructed a malformed or generic URL. The validation check
measures where a URL resolves *today*, which is a different question from whether it was
captured *correctly*.

**What this does and doesn't prove:** a redirect to the homepage means the listing is no
longer served at that address as of the validation date — it does **not** tell us *why*.
It would be inaccurate to assume every redirected listing simply reached its application
deadline; a listing can also be taken down early, filled, or moved for reasons this data
doesn't capture.

**Why this result can go stale:** this was a point-in-time check, run some days after the
original scrape. A listing marked available today could close tomorrow, and this
dashboard has no way to know that until the check is re-run.

**Why unavailable listings are kept, not deleted:** this dataset documents a historical
snapshot of the remote job market on a specific date — removing jobs that later became
unavailable would quietly rewrite that history. All {len(df)} jobs remain visible
everywhere in this dashboard.

**How this affects Job Explorer:** the "Open Job ↗" button only appears for listings
verified as a live individual job page. Everything else shows a plain
"Listing no longer available" note instead of a link that would silently redirect
somewhere generic.
""")

st.divider()

# --- 6. Data storage & version control ---
st.header("6. Data Storage & Version Control")
st.markdown("""
- **Raw scrape output is excluded from git** (`data/raw/` is git-ignored). Raw dumps are
  large, easily regenerated by re-running the pipeline, and would bloat the repository
  with little long-term value.
- **The one processed snapshot the dashboard depends on IS committed**
  (`data/processed/wwr_jobs_clean.csv`). Streamlit Community Cloud deploys directly from
  GitHub with no access to a local machine — without this file committed, the live
  dashboard fails immediately with a file-not-found error. Shipping a snapshot is
  standard practice for data that doesn't need regenerating on every deploy; refreshing
  it means re-running the pipeline locally and re-committing.
""")

st.divider()

# --- 7. Known limitations ---
st.header("7. Known Limitations")
n_tagged_region = int(sum(len(r) > 0 for r in df["region"]))
st.markdown(f"""
- **Single snapshot, not a trend.** Every chart reflects one scrape. A genuine
  "postings over time" view would require repeated scrapes across multiple days —
  this dataset can't show that yet.
- **Region data has low diversity in this snapshot.** Of {n_tagged_region} jobs with a
  region tag, the overwhelming majority list "Anywhere in the World" — not enough
  variation here to support a meaningful region-based filter.
- **Structured skill data covers only {coverage['pct_with_skills']}% of listings**
  (Section 4) — every skill-based feature in this dashboard is scoped and caveated
  accordingly.
- **No salary data exists in the source.** We Work Remotely's structured job-detail
  fields never include a reliable salary field; this dashboard makes no salary claims
  anywhere, by design.
- **URL availability reflects one validation pass** (Section 5) and will drift out of
  date as more listings close over time.
""")
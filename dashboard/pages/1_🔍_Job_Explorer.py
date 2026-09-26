from pathlib import Path
import sys

DASHBOARD_DIR = Path(__file__).resolve().parent.parent
if str(DASHBOARD_DIR) not in sys.path:
    sys.path.append(str(DASHBOARD_DIR))

import streamlit as st
from common import get_data
from analysis.metrics import (
    add_freshness,
    add_deadline_urgency,
    add_listing_availability,
    sort_jobs,
    SORT_OPTIONS,
    DEADLINE_PASSED,
    DEADLINE_TODAY,
    DEADLINE_SOON,
)

st.set_page_config(page_title="Job Explorer", page_icon="🔍", layout="wide")

df = get_data()
df = add_freshness(df)
df = add_deadline_urgency(df)
df = add_listing_availability(df)

st.title("🔍 Job Explorer")
st.caption("Browse live listings with freshness and deadline context.")

with st.expander("ℹ️ How freshness & deadlines are calculated"):
    st.markdown("""
    - **Freshness** is relative to when this dataset was scraped, not today's date —
      *New today* (same day as the scrape), *This week* (1–7 days before), *Older* (8+ days before).
    - **Deadline urgency** uses each listing's own "Apply before" date, measured from the scrape date:
      *Closes today*, *Closes in 1–3 days*, *Closes in 4–7 days*, *7+ days*, or *Deadline passed*.
    - Full methodology, including known data limitations, is on the **Methodology** page.
    """)

# --- Sidebar filters ---
st.sidebar.header("Filters")

all_categories = sorted(df["category_final"].dropna().unique())
selected_categories = st.sidebar.multiselect(
    "Category", all_categories, default=all_categories
)

all_job_types = sorted(df["job_type"].dropna().unique())
selected_job_types = st.sidebar.multiselect(
    "Job type", all_job_types, default=all_job_types
)

hot_only = st.sidebar.checkbox("🔥 Hot jobs only", value=False)
search_text = st.sidebar.text_input("Search title or company", "")

filtered = df[
    df["category_final"].isin(selected_categories) &
    df["job_type"].isin(selected_job_types)
]

if hot_only:
    filtered = filtered[filtered["is_hot"]]

if search_text:
    mask = (
        filtered["title"].str.contains(search_text, case=False, na=False) |
        filtered["company"].str.contains(search_text, case=False, na=False)
    )
    filtered = filtered[mask]

sort_choice = st.selectbox("Sort by", list(SORT_OPTIONS.keys()), index=0)
filtered = sort_jobs(filtered, sort_choice)

if filtered.empty:
    st.divider()
    with st.container(border=True):
        st.markdown("### 🔎 No jobs match your filters")
        st.write(
            "Try selecting more categories, clearing the search box, "
            "or turning off 'Hot jobs only.'"
        )
    st.stop()

# --- Result summary ---
n_with_skills = int((filtered["skills"].apply(len) > 0).sum())

n_urgent = int(
    filtered["deadline_urgency"].isin(
        [DEADLINE_PASSED, DEADLINE_TODAY, DEADLINE_SOON]
    ).sum()
)

n_unavailable = int((~filtered["is_listing_available"]).sum())

st.divider()

c1, c2, c3, c4 = st.columns(4)

c1.metric("Showing", f"{len(filtered)} / {len(df)}")

c2.metric("With structured skills", n_with_skills)

c3.metric(
    "Closing within 3 days",
    n_urgent,
    help="Includes jobs closing today, within 1-3 days, or past their listed deadline."
)

c4.metric(
    "No longer available",
    n_unavailable,
    help="The listing's original URL no longer resolves to an individual job page."
)

st.caption(
    "ℹ️ Some listings from the September 16 snapshot are no longer available on WWR."
)

st.divider()

# --- Pagination (added for render performance — 285 cards on one page would be a rough scroll) ---
PAGE_SIZE = 12
total_pages = max(1, -(-len(filtered) // PAGE_SIZE))

page = st.number_input(
    "Page",
    min_value=1,
    max_value=total_pages,
    value=1,
    step=1
)

page = min(page, total_pages)

st.caption(f"Page {page} of {total_pages}")

page_df = filtered.iloc[
    (page - 1) * PAGE_SIZE : page * PAGE_SIZE
]

# --- Job cards ---
DEADLINE_COLOR = {
    DEADLINE_PASSED: "red",
    DEADLINE_TODAY: "red",
    DEADLINE_SOON: "orange",
    "Closes in 4–7 days": "blue",
    "7+ days": "gray",
    "Deadline unknown": "gray",
}

FRESH_COLOR = {
    "New today": "green",
    "This week": "blue",
    "Older": "gray",
    "Unknown": "gray"
}

CARDS_PER_ROW = 3

for start in range(0, len(page_df), CARDS_PER_ROW):
    cols = st.columns(CARDS_PER_ROW)
    row_chunk = page_df.iloc[start:start + CARDS_PER_ROW]

    for col, (_, job) in zip(cols, row_chunk.iterrows()):
        with col:
            with st.container(border=True):
                badges = []

                if job["is_hot"]:
                    badges.append(":red[🔥 Hot]")

                badges.append(
                    f":{FRESH_COLOR.get(job['freshness'], 'gray')}[{job['freshness']}]"
                )

                badges.append(
                    f":{DEADLINE_COLOR.get(job['deadline_urgency'], 'gray')}[{job['deadline_urgency']}]"
                )

                st.markdown(f"**{job['title']}**")

                st.caption(
                    f"{job['company']} · "
                    f"{job['category_final']} · "
                    f"{job['job_type']}"
                )

                st.markdown(" · ".join(badges))

                if job["skills"]:
                    st.markdown(
                        f"🛠️ {', '.join(job['skills'])}"
                    )
                else:
                    st.caption(
                        "Skill tags not listed for this posting"
                    )

                if job["region"]:
                    st.caption(
                        f"🌍 {', '.join(job['region'])}"
                    )

                if job["is_listing_available"]:
                    st.link_button(
                        "Open Job ↗",
                        job["url"],
                        use_container_width=True
                    )
                else:
                    st.caption("Listing no longer available")
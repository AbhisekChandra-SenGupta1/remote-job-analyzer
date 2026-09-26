from pathlib import Path
import sys
DASHBOARD_DIR = Path(__file__).resolve().parent.parent
if str(DASHBOARD_DIR) not in sys.path:
    sys.path.append(str(DASHBOARD_DIR))

import streamlit as st
import plotly.express as px
from common import get_data
from analysis.metrics import (
    jobs_per_category, top_companies, top_skills, skills_coverage,
    add_freshness, add_listing_availability,
    FRESHNESS_NEW, FRESHNESS_WEEK, FRESHNESS_OLDER, FRESHNESS_UNKNOWN,
)

st.set_page_config(page_title="Market Insights", page_icon="📈", layout="wide")

df = get_data()
total_jobs = len(df)

st.title("📈 Market Insights")
st.caption(
    f"Descriptive patterns across all {total_jobs} jobs in the September 16, 2026 "
    "snapshot. No filters applied — this reflects the full dataset."
)

st.divider()

# --- 1. Category Comparison ---
st.header("1. Category Comparison")
cat_df = jobs_per_category(df)
cat_df["pct"] = (cat_df["count"] / total_jobs * 100).round(1)

fig_cat = px.bar(
    cat_df, x="count", y="category", orientation="h",
    text=cat_df["pct"].astype(str) + "%",
)
fig_cat.update_traces(textposition="outside")
fig_cat.update_layout(yaxis=dict(categoryorder="total ascending"), height=450)
st.plotly_chart(fig_cat, use_container_width=True)

with st.expander("Exact figures"):
    st.dataframe(
        cat_df.rename(columns={"category": "Category", "count": "Jobs", "pct": "% of Total"}),
        hide_index=True, use_container_width=True,
    )

st.divider()

# --- 2. Company Concentration ---
st.header("2. Company Concentration")
top_co = top_companies(df, n=10)
top10_total = int(top_co["count"].sum())
top10_pct = round(top10_total / total_jobs * 100, 1)

fig_co = px.bar(top_co, x="count", y="company", orientation="h")
fig_co.update_layout(yaxis=dict(categoryorder="total ascending"), height=450)
st.plotly_chart(fig_co, use_container_width=True)

st.markdown(
    f"The 10 companies above account for **{top10_total} of {total_jobs} listings "
    f"({top10_pct}%)** in this snapshot. This describes how concentrated postings are "
    "among a small number of companies here — it is not an evaluation of any company."
)

st.divider()

# --- 3. Skill Insights ---
st.header("3. Skill Insights")
coverage = skills_coverage(df)
st.markdown(
    f"⚠️ Structured skill tags exist for only **{coverage['jobs_with_skills']} of "
    f"{coverage['total_jobs']} listings ({coverage['pct_with_skills']}%)**. "
    "Everything below reflects that subset only, not all 285 jobs — see Methodology "
    "for why coverage is uneven across categories."
)

if coverage["jobs_with_skills"] == 0:
    st.info("No listings in this dataset currently have structured skill tags.")
else:
    skills_df = top_skills(df, n=15, exclude_noise=True)
    fig_skills = px.bar(skills_df, x="count", y="skill", orientation="h")
    fig_skills.update_layout(yaxis=dict(categoryorder="total ascending"), height=450)
    st.plotly_chart(fig_skills, use_container_width=True)
    st.caption("Generic terms (Full Time, Engineer, Developer, Full Stack Dev) excluded.")

st.divider()

# --- 4. Freshness ---
st.header("4. Freshness")
fresh_df = add_freshness(df)

freshness_order = [FRESHNESS_NEW, FRESHNESS_WEEK, FRESHNESS_OLDER]
unknown_count = int((fresh_df["freshness"] == FRESHNESS_UNKNOWN).sum())
if unknown_count > 0:
    freshness_order.append(FRESHNESS_UNKNOWN)

fresh_counts = (
    fresh_df["freshness"].value_counts()
    .reindex(freshness_order, fill_value=0)
    .reset_index()
)
fresh_counts.columns = ["freshness", "count"]

fig_fresh = px.bar(fresh_counts, x="freshness", y="count")
fig_fresh.update_layout(height=350, xaxis_title=None)
st.plotly_chart(fig_fresh, use_container_width=True)
st.caption(
    "Freshness is measured relative to this dataset's own scrape timestamp "
    "(Sept 16, 2026), not today's date — see Methodology for the exact rule."
)

st.divider()

# --- 5. Auto-Generated Snapshot Insights ---
st.header("5. Snapshot Insights")
st.caption("Factual observations computed directly from this dataset. Descriptive only — no rankings or recommendations.")

top_row = cat_df.sort_values("count", ascending=False).iloc[0]
n_companies = df["company"].nunique()
n_hot = int(df["is_hot"].sum())

if "url_status" in df.columns:
    avail_df = add_listing_availability(df)
    n_unavailable = int((~avail_df["is_listing_available"]).sum())
    availability_line = (
        f"- **Currently unavailable listings:** {n_unavailable} of {total_jobs} "
        "(validated via a one-time URL check — see Methodology)."
    )
else:
    availability_line = "- **Listing availability:** not yet validated for this dataset."

st.markdown(f"""
- **Largest category:** {top_row['category']} — {int(top_row['count'])} jobs
  ({top_row['pct']}% of all postings).
- **Categories represented:** {df['category_final'].nunique()}.
- **Unique hiring companies:** {n_companies}.
- **Jobs flagged "Hot" by WWR:** {n_hot} of {total_jobs}.
- **Structured skill-tag coverage:** {coverage['pct_with_skills']}% of listings
  ({coverage['jobs_with_skills']} of {coverage['total_jobs']}).
{availability_line}
""")
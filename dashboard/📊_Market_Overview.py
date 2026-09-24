import streamlit as st
import plotly.express as px

from common import get_data
from analysis.metrics import (
    jobs_per_category,
    skills_coverage,
    top_skills,
    top_companies,
)

st.set_page_config(
    page_title="Remote Job Market Intelligence",
    page_icon="🌍",
    layout="wide",
)

df = get_data()

st.title("🌍 Remote Job Market Intelligence Dashboard")
st.caption("Live snapshot of remote job postings scraped from We Work Remotely")

last_scraped = df["scraped_at"].max()
st.caption(f"📅 Data last scraped: {last_scraped:%B %d, %Y %H:%M}")

with st.expander("ℹ️ About this data"):
    st.markdown("""
    - **Source:** [We Work Remotely](https://weworkremotely.com), scraped across 9 job categories.
    - **Snapshot, not live:** This reflects one scrape at the timestamp above, not a continuously updating feed.
    - **Skill tags:** Only 20% of listings (57 of 285) include structured skill data — see the caveat under the skills chart.
    - **Trend limitation:** A "postings over time" view would need repeated scrapes across multiple days; this single-snapshot dataset can't show that yet.
    """)

# --- Filters now come FIRST: everything below reads `filtered`, not `df` ---
st.sidebar.header("Filters")

all_categories = sorted(df["category_final"].dropna().unique())
selected_categories = st.sidebar.multiselect(
    "Category",
    all_categories,
    default=all_categories
)

hot_only = st.sidebar.checkbox("🔥 Hot jobs only", value=False)
search_text = st.sidebar.text_input("Search title or company", "")

filtered = df[df["category_final"].isin(selected_categories)]

if hot_only:
    filtered = filtered[filtered["is_hot"]]

if search_text:
    mask = (
        filtered["title"].str.contains(search_text, case=False, na=False) |
        filtered["company"].str.contains(search_text, case=False, na=False)
    )
    filtered = filtered[mask]

if filtered.empty:
    st.warning("No jobs match the current filters. Try widening your selection.")
    st.stop()

# --- KPI row ---
coverage = skills_coverage(filtered)

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Jobs Shown",
    f"{len(filtered)} / {len(df)}"
)

col2.metric(
    "Categories",
    filtered["category_final"].nunique()
)

col3.metric(
    "Hot Jobs",
    int(filtered["is_hot"].sum())
)

col4.metric(
    "Skill-Tag Coverage",
    f"{coverage['pct_with_skills']}%",
    help=(
        f"{coverage['jobs_with_skills']} of "
        f"{coverage['total_jobs']} shown listings "
        "include structured skill tags"
    )
)

st.divider()

st.subheader("Jobs per Category")

cat_df = jobs_per_category(filtered)

fig = px.bar(
    cat_df,
    x="category",
    y="count"
)

fig.update_layout(
    xaxis_tickangle=-40,
    height=450,
    margin=dict(b=120)
)

st.plotly_chart(
    fig,
    use_container_width=True
)

st.divider()

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Top In-Demand Skills")

    if coverage["jobs_with_skills"] == 0:
        st.info(
            "None of the currently filtered jobs "
            "include structured skill tags."
        )
    else:
        st.caption(
            f"Based on {coverage['jobs_with_skills']} of "
            f"{coverage['total_jobs']} shown listings "
            f"({coverage['pct_with_skills']}%) that include "
            "structured skill tags. "
            "Generic terms (Full Time, Engineer, Developer, "
            "Full Stack Dev) excluded."
        )

        skills_df = top_skills(
            filtered,
            n=12,
            exclude_noise=True
        )

        fig_skills = px.bar(
            skills_df,
            x="count",
            y="skill",
            orientation="h"
        )

        fig_skills.update_layout(
            yaxis=dict(categoryorder="total ascending"),
            height=450
        )

        st.plotly_chart(
            fig_skills,
            use_container_width=True
        )

with col_right:
    st.subheader("Top Hiring Companies")

    companies_df = top_companies(
        filtered,
        n=12
    )

    fig_companies = px.bar(
        companies_df,
        x="count",
        y="company",
        orientation="h"
    )

    fig_companies.update_layout(
        yaxis=dict(categoryorder="total ascending"),
        height=450
    )

    st.plotly_chart(
        fig_companies,
        use_container_width=True
    )

st.divider()

st.subheader(
    f"Job Listings ({len(filtered)} of {len(df)})"
)

display_df = filtered[
    [
        "title",
        "company",
        "category_final",
        "job_type",
        "posted_date",
        "url"
    ]
].copy()

display_df = display_df.rename(
    columns={
        "category_final": "category"
    }
)

display_df["posted_date"] = (
    display_df["posted_date"]
    .dt.strftime("%b %d, %Y")
)

st.dataframe(
    display_df,
    column_config={
        "url": st.column_config.LinkColumn(
            "Apply",
            display_text="Open ↗"
        )
    },
    hide_index=True,
    use_container_width=True,
)

st.download_button(
    "⬇️ Download filtered results as CSV",
    display_df.to_csv(index=False),
    file_name="remote_jobs_filtered.csv",
    mime="text/csv",
)
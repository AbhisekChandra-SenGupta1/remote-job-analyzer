from pathlib import Path
import sys
DASHBOARD_DIR = Path(__file__).resolve().parent.parent
if str(DASHBOARD_DIR) not in sys.path:
    sys.path.append(str(DASHBOARD_DIR))

import streamlit as st
from common import get_data
from analysis.metrics import (
    available_skills, match_jobs_to_skills, skills_coverage,
    add_freshness, add_deadline_urgency, add_listing_availability,
)

st.set_page_config(page_title="Candidate Match", page_icon="🎯", layout="wide")

df = get_data()
coverage = skills_coverage(df)

st.title("🎯 Candidate Match")
st.caption("Deterministic skill matching against listings with structured skill tags. No AI, no inference — just set overlap.")

st.warning(
    f"Structured skills are available for only {coverage['jobs_with_skills']} of "
    f"{coverage['total_jobs']} listings ({coverage['pct_with_skills']}%). Candidate "
    "matching therefore applies only to listings with structured skill tags and cannot "
    "determine whether an untagged listing is actually a match."
)

if coverage["jobs_with_skills"] == 0:
    st.info("No listings in this dataset currently have structured skill tags — matching isn't possible right now.")
    st.stop()

skill_options = available_skills(df, exclude_noise=True)
selected_skills = st.multiselect(
    "Select your skills",
    skill_options,
    help="Generic terms (Full Time, Engineer, Developer, Full Stack Dev) are excluded from this list.",
)

if not selected_skills:
    st.info("👆 Select one or more skills above to see matching jobs.")
    st.stop()

min_match = st.select_slider("Minimum match percentage", options=[50, 60, 70, 80, 90, 100], value=50)

results = match_jobs_to_skills(df, selected_skills)
n_evaluated = len(results)
n_untagged = coverage["total_jobs"] - coverage["jobs_with_skills"]

results = results[results["match_pct"] >= min_match]
results = add_freshness(results)
results = add_deadline_urgency(results)
results = add_listing_availability(results)
results = results.sort_values(["match_pct", "posted_date"], ascending=[False, False])

st.caption(
    f"Evaluated {n_evaluated} listings with structured skill tags. "
    f"{n_untagged} additional listings have no structured skill tags and are not shown here — "
    "this does not mean they lack the skills you selected, only that it can't be verified from this data."
)

st.divider()

if results.empty:
    with st.container(border=True):
        st.markdown(f"### 🔎 No jobs meet the {min_match}% threshold")
        st.write("Try lowering the threshold or selecting different skills.")
    st.stop()

st.subheader(f"{len(results)} matching job(s)")

FRESH_COLOR = {"New today": "green", "This week": "blue", "Older": "gray", "Unknown": "gray"}
DEADLINE_COLOR = {
    "Deadline passed": "red", "Closes today": "red", "Closes in 1\u20133 days": "orange",
    "Closes in 4\u20137 days": "blue", "7+ days": "gray", "Deadline unknown": "gray",
}

for _, job in results.iterrows():
    with st.container(border=True):
        left, right = st.columns([3, 1])

        with left:
            st.markdown(f"**{job['title']}**")
            st.caption(f"{job['company']} · {job['category_final']}")

            badges = [f":{FRESH_COLOR.get(job['freshness'], 'gray')}[{job['freshness']}]"]
            badges.append(f":{DEADLINE_COLOR.get(job['deadline_urgency'], 'gray')}[{job['deadline_urgency']}]")
            st.markdown(" · ".join(badges))

            if job["matched_skills"]:
                st.markdown(f"✅ **Matched:** {', '.join(job['matched_skills'])}")
            if job["missing_skills"]:
                st.markdown(f"⬜ **Missing:** {', '.join(job['missing_skills'])}")

        with right:
            st.metric("Match", f"{job['match_pct']:.0f}%")
            if job["is_listing_available"]:
                st.link_button("Open Job ↗", job["url"], use_container_width=True)
            else:
                st.caption("Listing no longer available")
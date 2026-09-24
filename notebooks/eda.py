# %%
from pathlib import Path
import sys
import pandas as pd


def find_project_root(marker="requirements.txt"):
    """Walk upward from wherever this cell runs until we find the project root.
    Avoids fragile '../' guessing that breaks depending on your working directory.
    """
    path = Path.cwd()

    for parent in [path] + list(path.parents):
        if (parent / marker).exists():
            return parent

    raise FileNotFoundError(
        f"Could not find project root (looked for {marker})"
    )


PROJECT_ROOT = find_project_root()
sys.path.append(str(PROJECT_ROOT))

from analysis.metrics import (
    load_clean_data,
    top_skills,
    jobs_per_category,
    top_companies,
    region_distribution,
    postings_over_time
)

import plotly.express as px


df = load_clean_data(
    PROJECT_ROOT / "data/processed/wwr_jobs_clean.csv"
)

print(f"{len(df)} jobs loaded")
df.head()


# %%
skills_df = top_skills(df, n=15)

px.bar(
    skills_df,
    x="count",
    y="skill",
    orientation="h",
    title="Top 15 In-Demand Skills"
).update_layout(
    yaxis=dict(categoryorder="total ascending")
)


# %%
cat_df = jobs_per_category(df)

px.bar(
    cat_df,
    x="category",
    y="count",
    title="Jobs per Category"
)


# %%
comp_df = top_companies(df, n=10)

px.bar(
    comp_df,
    x="count",
    y="company",
    orientation="h",
    title="Top 10 Hiring Companies"
)


# %%
region_df = region_distribution(df)

px.pie(
    region_df,
    names="region",
    values="count",
    title="Remote Region Eligibility"
)


# %%
trend_df = postings_over_time(df)

px.line(
    trend_df,
    x="posted_day",
    y="count",
    markers=True,
    title="Job Postings Over Time"
)


# %%
print("=== Full category breakdown ===")
print(cat_df.to_string())

print("\n=== Full skills breakdown ===")
print(top_skills(df, n=50).to_string())

print("\n=== Full region breakdown ===")
print(region_distribution(df).to_string())

print("\n=== How many skills/region tags per job? ===")
print(
    "Jobs with EMPTY skills list:",
    (df["skills"].apply(len) == 0).sum(),
    "/",
    len(df)
)

print(
    "Jobs with EMPTY region list:",
    (df["region"].apply(len) == 0).sum(),
    "/",
    len(df)
)

print("\nSkills-per-job distribution:")
print(
    df["skills"]
    .apply(len)
    .value_counts()
    .sort_index()
)

print("\nRegion-per-job distribution:")
print(
    df["region"]
    .apply(len)
    .value_counts()
    .sort_index()
)


# %%
print(
    "Total unique skills across dataset:",
    df["skills"]
    .explode()
    .replace("", pd.NA)
    .dropna()
    .nunique()
)

print(
    "\nJobs with EMPTY skills list:",
    (df["skills"].apply(len) == 0).sum(),
    "/",
    len(df)
)

print(
    "\nSkills-per-job distribution "
    "(how many skill tags does a job typically have?):"
)

print(
    df["skills"]
    .apply(len)
    .value_counts()
    .sort_index()
)

print("\nFULL skills list, no truncation:")

full_skills = top_skills(df, n=1000)

print(
    full_skills.to_string()
)

# %%
coverage = df.groupby("category_final")["skills"].apply(
    lambda s: (s.apply(len) > 0).mean() * 100
)

print("% of jobs WITH skill tags, by category:")
print(
    coverage
    .sort_values(ascending=False)
    .round(1)
    .to_string()
)

# %%
from analysis.metrics import top_skills, skills_coverage

coverage_result = skills_coverage(df)

print(coverage_result)

print()

skills_result = top_skills(
    df,
    n=15,
    exclude_noise=True
)

print(skills_result.to_string())


# %%

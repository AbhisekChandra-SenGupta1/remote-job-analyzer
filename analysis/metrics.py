import pandas as pd


# Tags that appear in the structured "Skills" field but describe employment
# type or generic role labels rather than an actual skill. Excluded only from
# the skills chart/ranking — never removed from the underlying data.
SKILL_NOISE_TERMS = {
    "Full Time",
    "Engineer",
    "Developer",
    "Full Stack Dev"
}


def load_clean_data(path):

    df = pd.read_csv(
        path,
        parse_dates=["scraped_at", "posted_date", "apply_before_date"]
    )

    for col in ["tags", "region", "skills"]:
        df[col] = df[col].fillna("").apply(
            lambda s: s.split("|") if s else []
        )

    return df


def top_skills(df, n=15, exclude_noise=False):

    exploded = df.explode("skills")

    exploded = exploded[exploded["skills"] != ""]

    if exclude_noise:
        exploded = exploded[
            ~exploded["skills"].isin(SKILL_NOISE_TERMS)
        ]

    counts = (
        exploded["skills"]
        .value_counts()
        .head(n)
        .reset_index()
    )

    counts.columns = ["skill", "count"]

    return counts


def skills_coverage(df):
    """How many jobs actually carry structured skill tags?
    Powers the dashboard's caveat text.
    """

    total = len(df)

    with_skills = int(
        (df["skills"].apply(len) > 0).sum()
    )

    return {
        "total_jobs": total,
        "jobs_with_skills": with_skills,
        "pct_with_skills": round(
            with_skills / total * 100, 1
        ) if total else 0.0,
    }


def jobs_per_category(df):

    counts = df["category_final"].value_counts().reset_index()

    counts.columns = ["category", "count"]

    return counts


def top_companies(df, n=10):

    counts = (
        df["company"]
        .value_counts()
        .head(n)
        .reset_index()
    )

    counts.columns = ["company", "count"]

    return counts


def region_distribution(df):

    exploded = df.explode("region")

    exploded = exploded[exploded["region"] != ""]

    counts = (
        exploded["region"]
        .value_counts()
        .reset_index()
    )

    counts.columns = ["region", "count"]

    return counts


def postings_over_time(df):

    daily = df.dropna(subset=["posted_date"]).copy()

    daily["posted_day"] = daily["posted_date"].dt.date

    counts = (
        daily
        .groupby("posted_day")
        .size()
        .reset_index(name="count")
    )

    return counts.sort_values("posted_day")
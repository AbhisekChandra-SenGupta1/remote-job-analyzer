import pandas as pd


def load_clean_data(path):
    df = pd.read_csv(path, parse_dates=["scraped_at", "posted_date", "apply_before_date"])
    for col in ["tags", "region", "skills"]:
        df[col] = df[col].fillna("").apply(lambda s: s.split("|") if s else [])
    return df


SKILL_NOISE_TERMS = {"Full Time", "Engineer", "Developer", "Full Stack Dev"}


def top_skills(df, n=15, exclude_noise=False):
    exploded = df.explode("skills")
    exploded = exploded[exploded["skills"] != ""]
    if exclude_noise:
        exploded = exploded[~exploded["skills"].isin(SKILL_NOISE_TERMS)]
    counts = exploded["skills"].value_counts().head(n).reset_index()
    counts.columns = ["skill", "count"]
    return counts


def jobs_per_category(df):
    counts = df["category_final"].value_counts().reset_index()
    counts.columns = ["category", "count"]
    return counts


def top_companies(df, n=10):
    counts = df["company"].value_counts().head(n).reset_index()
    counts.columns = ["company", "count"]
    return counts


def region_distribution(df):
    exploded = df.explode("region")
    exploded = exploded[exploded["region"] != ""]
    counts = exploded["region"].value_counts().reset_index()
    counts.columns = ["region", "count"]
    return counts


def postings_over_time(df):
    daily = df.dropna(subset=["posted_date"]).copy()
    daily["posted_day"] = daily["posted_date"].dt.date
    counts = daily.groupby("posted_day").size().reset_index(name="count")
    return counts.sort_values("posted_day")


def skills_coverage(df):
    total = len(df)
    with_skills = int((df["skills"].apply(len) > 0).sum())
    return {
        "total_jobs": total,
        "jobs_with_skills": with_skills,
        "pct_with_skills": round(with_skills / total * 100, 1) if total else 0.0,
    }


# --- Freshness & deadline labeling (Job Explorer, Stage 2) ---

FRESHNESS_NEW = "New today"
FRESHNESS_WEEK = "This week"
FRESHNESS_OLDER = "Older"
FRESHNESS_UNKNOWN = "Unknown"


def add_freshness(df, reference_date=None):
    """
    Labels each job's freshness relative to `reference_date`, which defaults to
    this dataset's own scrape timestamp (scraped_at) -- NOT wall-clock 'today'.
    The scrape is a snapshot from the past, so 'today' means 'as of when we
    scraped it,' the same anchoring used when posted_date itself was parsed.

      New today:  posted the same calendar day as the scrape
      This week:  1-7 days before the scrape
      Older:      8+ days before the scrape
      Unknown:    posted_date could not be parsed
    """
    out = df.copy()
    if reference_date is None:
        reference_date = out["scraped_at"].max()

    def label(posted):
        if pd.isna(posted):
            return FRESHNESS_UNKNOWN
        days = (reference_date.normalize() - posted.normalize()).days
        if days <= 0:
            return FRESHNESS_NEW
        elif days <= 7:
            return FRESHNESS_WEEK
        return FRESHNESS_OLDER

    out["freshness"] = out["posted_date"].apply(label)
    return out


DEADLINE_PASSED = "Deadline passed"
DEADLINE_TODAY = "Closes today"
DEADLINE_SOON = "Closes in 1\u20133 days"
DEADLINE_WEEK = "Closes in 4\u20137 days"
DEADLINE_LATER = "7+ days"
DEADLINE_UNKNOWN = "Deadline unknown"


def add_deadline_urgency(df):
    """Labels urgency from the existing days_until_deadline column (no new calculation)."""
    out = df.copy()

    def label(days):
        if pd.isna(days):
            return DEADLINE_UNKNOWN
        days = int(days)
        if days < 0:
            return DEADLINE_PASSED
        elif days == 0:
            return DEADLINE_TODAY
        elif days <= 3:
            return DEADLINE_SOON
        elif days <= 7:
            return DEADLINE_WEEK
        return DEADLINE_LATER

    out["deadline_urgency"] = out["days_until_deadline"].apply(label)
    return out


# --- Sorting ---

SORT_OPTIONS = {
    "Newest": ("posted_date", False),
    "Deadline soonest": ("apply_before_date", True),
    "Company A\u2013Z": ("company", True),
    "Title A\u2013Z": ("title", True),
}


def sort_jobs(df, sort_label):
    if sort_label == "Deadline soonest":
        # Passed deadlines aren't "soon" in any actionable sense -- push them to the
        # very bottom, below even unknown-deadline jobs, rather than sorting purely
        # by date (which would put the most-expired job first).
        out = df.copy()
        out["_passed"] = out["days_until_deadline"] < 0
        out = out.sort_values(
            ["_passed", "apply_before_date"], ascending=[True, True], na_position="last"
        )
        return out.drop(columns="_passed")

    column, ascending = SORT_OPTIONS.get(sort_label, ("posted_date", False))
    return df.sort_values(column, ascending=ascending, na_position="last")

# --- Listing availability ---

LISTING_AVAILABLE_STATUS = "valid_job_page"


def add_listing_availability(df):
    """
    Flags whether a job's original URL still resolves
    to an individual job listing.
    """
    out = df.copy()

    if "url_status" not in out.columns:
        out["url_status"] = "unknown"

    out["url_status"] = out["url_status"].fillna("unknown")

    out["is_listing_available"] = (
        out["url_status"] == LISTING_AVAILABLE_STATUS
    )

    return out

    # --- Candidate skill matching (Candidate Match page) ---

def available_skills(df, exclude_noise=True):
    """Deterministic, sorted list of unique structured skills, for a skill-picker UI."""
    exploded = df.explode("skills").dropna(subset=["skills"])
    exploded = exploded[exploded["skills"] != ""]

    if exclude_noise:
        exploded = exploded[
            ~exploded["skills"].isin(SKILL_NOISE_TERMS)
        ]

    return sorted(exploded["skills"].unique())


def match_jobs_to_skills(df, selected_skills):
    """
    Deterministic matching, scoped ONLY to jobs with at least one structured skill tag.

    Formula:
    matched selected skills / total selected skills × 100

    Jobs with an empty skills list are excluded entirely.
    """
    if not selected_skills:
        empty = df.iloc[0:0].copy()
        empty["match_pct"] = []
        empty["matched_skills"] = []
        empty["missing_skills"] = []
        return empty

    selected_set = set(selected_skills)

    tagged = df[df["skills"].apply(len) > 0].copy()

    def compute(job_skills):
        job_set = set(job_skills)

        matched = sorted(selected_set & job_set)
        missing = sorted(selected_set - job_set)

        pct = round(
            len(matched) / len(selected_set) * 100,
            1
        )

        return pd.Series({
            "match_pct": pct,
            "matched_skills": matched,
            "missing_skills": missing,
        })

    scored_cols = tagged["skills"].apply(compute)

    return tagged.join(scored_cols)
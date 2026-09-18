import pandas as pd
import ast
import re
from datetime import datetime, timedelta

INPUT = "data/raw/wwr_jobs_enriched.csv"
OUTPUT = "data/processed/wwr_jobs_clean.csv"


def parse_list_field(value):
    """Turn a CSV cell like "['React', 'Node.js']" back into a real list."""
    if pd.isna(value) or value == "":
        return []

    try:
        parsed = ast.literal_eval(value)
        return parsed if isinstance(parsed, list) else [str(parsed)]
    except (ValueError, SyntaxError):
        return []


def parse_relative_date(text, reference):
    """Convert relative dates like '2 hours ago' into a datetime."""
    if pd.isna(text):
        return pd.NaT

    text = str(text).strip().lower()

    if text in ("new", "today"):
        return reference

    match = re.match(
        r"(\d+)\s+(minute|hour|day|week|month)s?\s+ago",
        text
    )

    if not match:
        return pd.NaT

    amount, unit = int(match.group(1)), match.group(2)

    delta = {
        "minute": timedelta(minutes=amount),
        "hour": timedelta(hours=amount),
        "day": timedelta(days=amount),
        "week": timedelta(weeks=amount),
        "month": timedelta(days=amount * 30)
    }[unit]

    return reference - delta


def parse_absolute_date(text):
    """Convert 'Oct 15th, 2026' into a datetime."""
    if pd.isna(text):
        return pd.NaT

    cleaned = re.sub(
        r"(\d+)(st|nd|rd|th)",
        r"\1",
        str(text)
    )

    try:
        return datetime.strptime(cleaned, "%b %d, %Y")
    except ValueError:
        return pd.NaT


def normalize_category(text):
    """Normalize category naming differences such as '&' vs 'and'."""
    if pd.isna(text) or text == "":
        return None

    return str(text).replace("&", "and").strip()


def clean():

    # --- Load data ---
    df = pd.read_csv(INPUT)

    print(
        f"Loaded {len(df)} rows, "
        f"{df['url'].nunique()} unique URLs"
    )

    # --- Fix list columns ---
    for col in ["tags", "region", "skills"]:
        df[col] = df[col].apply(parse_list_field)

    # --- Parse dates ---
    df["scraped_at"] = pd.to_datetime(
        df["scraped_at"]
    )

    df["posted_date"] = df.apply(
        lambda r: parse_relative_date(
            r["posted_on"],
            r["scraped_at"]
        ),
        axis=1
    )

    df["apply_before_date"] = df[
        "apply_before"
    ].apply(parse_absolute_date)

    df["days_until_deadline"] = (
        df["apply_before_date"] -
        df["scraped_at"]
    ).dt.days

    # --- Normalize categories ---
    df["category_norm"] = df[
        "category"
    ].apply(normalize_category)

    df["category_detail_norm"] = df[
        "category_detail"
    ].apply(normalize_category)

    # category_detail is authoritative.
    # Fall back to scraped category if detail category is missing.
    df["category_final"] = (
        df["category_detail_norm"]
        .fillna(df["category_norm"])
    )

    # --- Check for genuine category mismatches ---
    real_mismatch = df[
        df["category_detail_norm"].notna()
        &
        (
            df["category_norm"]
            != df["category_detail_norm"]
        )
    ]

    print(
        f"\nGenuine mismatches after "
        f"normalizing '&'/'and': {len(real_mismatch)}"
    )

    if len(real_mismatch):
        print(
            real_mismatch[
                [
                    "title",
                    "category_norm",
                    "category_detail_norm"
                ]
            ].head(10)
        )

    # --- QA: check date parsing ---
    bad_posted = df[
        "posted_date"
    ].isna().sum()

    bad_deadline = df[
        "apply_before_date"
    ].isna().sum()

    print(
        f"\nUnparsed posted_date: {bad_posted}"
    )

    print(
        f"Unparsed apply_before_date: {bad_deadline}"
    )

    if bad_posted:
        print(
            "Sample unparsed posted_on values:",
            df[
                df["posted_date"].isna()
            ]["posted_on"].unique()[:5]
        )

    # --- Convert list columns to pipe-delimited strings ---
    for col in ["tags", "region", "skills"]:
        df[col] = df[col].apply(
            lambda lst: "|".join(lst)
        )

    # --- Save cleaned dataset ---
    df.to_csv(
        OUTPUT,
        index=False
    )

    print(
        f"\nSaved {len(df)} cleaned rows "
        f"to {OUTPUT}"
    )

    return df


if __name__ == "__main__":
    clean()
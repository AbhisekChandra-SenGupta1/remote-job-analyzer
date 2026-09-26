import pandas as pd

CLEAN_DATA = "data/processed/wwr_jobs_clean.csv"
VALIDATION_REPORT = "data/raw/url_validation_report.csv"


def main():
    df = pd.read_csv(CLEAN_DATA)
    report = pd.read_csv(VALIDATION_REPORT)

    # Join on URL because it uniquely identifies each listing.
    status_lookup = report[["original_url", "url_status"]].rename(
        columns={"original_url": "url"}
    )

    before = len(df)

    merged = df.merge(status_lookup, on="url", how="left")

    if len(merged) != before:
        raise ValueError(
            f"Row count changed after merge ({before} -> {len(merged)}); "
            "the validation report likely has duplicate URLs. "
            "Aborting without saving."
        )

    missing = merged["url_status"].isna().sum()

    if missing:
        print(
            f"WARNING: {missing} job(s) had no matching entry in the validation "
            "report and are being marked 'unknown'."
        )

    merged["url_status"] = merged["url_status"].fillna("unknown")

    print("url_status breakdown after merge:")
    print(merged["url_status"].value_counts())

    merged.to_csv(CLEAN_DATA, index=False)

    print(
        f"\nSaved {len(merged)} rows back to {CLEAN_DATA} "
        "with url_status added."
    )


if __name__ == "__main__":
    main()
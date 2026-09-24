from pathlib import Path
import sys
import streamlit as st


def find_project_root(marker="requirements.txt"):
    path = Path(__file__).resolve()

    for parent in [path] + list(path.parents):
        if (parent / marker).exists():
            return parent

    raise FileNotFoundError(
        f"Could not find project root (looked for {marker})"
    )


PROJECT_ROOT = find_project_root()

if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))


from analysis.metrics import load_clean_data


@st.cache_data
def get_data():
    return load_clean_data(
        PROJECT_ROOT / "data/processed/wwr_jobs_clean.csv"
    )
from pathlib import Path
import sys

DASHBOARD_DIR = Path(__file__).resolve().parent.parent

if str(DASHBOARD_DIR) not in sys.path:
    sys.path.append(str(DASHBOARD_DIR))

import streamlit as st
from common import get_data

st.set_page_config(
    page_title="Candidate Match",
    page_icon="🎯",
    layout="wide"
)

df = get_data()

st.title("🎯 Candidate Match")

st.info(
    f"🚧 Coming soon: pick your skills and see matched jobs. "
    f"Will apply only to the subset of {len(df)} jobs "
    "with structured skill tags."
)
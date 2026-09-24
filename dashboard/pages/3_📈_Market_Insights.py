from pathlib import Path
import sys

DASHBOARD_DIR = Path(__file__).resolve().parent.parent

if str(DASHBOARD_DIR) not in sys.path:
    sys.path.append(str(DASHBOARD_DIR))

import streamlit as st
from common import get_data

st.set_page_config(
    page_title="Market Insights",
    page_icon="📈",
    layout="wide"
)

df = get_data()

st.title("📈 Market Insights")

st.info(
    f"🚧 Coming soon: category comparison, company concentration, "
    f"and auto-generated insights from these {len(df)} jobs."
)
from pathlib import Path
import sys

DASHBOARD_DIR = Path(__file__).resolve().parent.parent

if str(DASHBOARD_DIR) not in sys.path:
    sys.path.append(str(DASHBOARD_DIR))

import streamlit as st
from common import get_data

st.set_page_config(
    page_title="Job Explorer",
    page_icon="🔍",
    layout="wide"
)

df = get_data()

st.title("🔍 Job Explorer")

st.info(
    f"🚧 Coming in the next stage: job cards with freshness "
    f"and deadline badges, built on this same {len(df)}-job dataset."
)
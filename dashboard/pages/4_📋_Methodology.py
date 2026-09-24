from pathlib import Path
import sys

DASHBOARD_DIR = Path(__file__).resolve().parent.parent

if str(DASHBOARD_DIR) not in sys.path:
    sys.path.append(str(DASHBOARD_DIR))

import streamlit as st
from common import get_data

st.set_page_config(
    page_title="Methodology",
    page_icon="📋",
    layout="wide"
)

df = get_data()

st.title("📋 Methodology")

st.info(
    "🚧 Coming soon: full data-engineering write-up "
    "(dedup, category normalization, CSV list parsing, "
    "skill-coverage limitations)."
)
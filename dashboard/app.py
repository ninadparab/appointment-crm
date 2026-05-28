import streamlit as st
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_total_counts

st.set_page_config(
    page_title="CRM Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Appointment CRM Dashboard")
st.markdown("Welcome! Use the sidebar to navigate.")

# Show top-level stats
st.markdown("---")
counts = get_total_counts()

col1, col2 = st.columns(2)
with col1:
    st.metric("Total Customers", counts["customers"])
with col2:
    st.metric("Total Services", counts["services"])

st.markdown("---")
st.markdown("### Quick Navigation")
st.markdown("""
- **🔍 Search** — Find customers by name or phone, view their history
- **📈 Reports** — Revenue and service trends with custom date ranges
""")
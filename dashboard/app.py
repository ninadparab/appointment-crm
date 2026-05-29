import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_total_counts


def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["PASSWORD"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.title("🔐 CRM Dashboard Login")
        st.text_input("Enter password", type="password",
                      on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.title("🔐 CRM Dashboard Login")
        st.text_input("Enter password", type="password",
                      on_change=password_entered, key="password")
        st.error("❌ Incorrect password")
        return False
    return True

if not check_password():
    st.stop()

st.set_page_config(page_title="CRM Dashboard", page_icon="📊", layout="wide")
st.title("📊 Appointment CRM Dashboard")
st.markdown("Welcome! Use the sidebar to navigate.")

st.markdown("---")
counts = get_total_counts()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Customers", f"{counts['customers']:,}")
with col2:
    st.metric("Total Services", f"{counts['services']:,}")
with col3:
    st.metric("⚠️ Flagged for Review", f"{counts['issues']:,}",
              help="Services with data quality issues (huge amounts, suspicious quantities, etc.)")

st.markdown("---")
st.markdown("### Quick Navigation")
st.markdown("""
- **🔍 Search** — Find customers by name or phone, view their history
- **📈 Reports** — Revenue and service trends, top clients, area analysis
- **➕ Add Customer** — Manually add new customer (optionally with first service)
- **🔧 Add Service** — Add a service to an existing customer
""")
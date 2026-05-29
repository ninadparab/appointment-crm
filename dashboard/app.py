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

# ── Stats ──────────────────────────────────────────────
counts = get_total_counts()
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Customers", f"{counts['customers']:,}")
with col2:
    st.metric("Total Services", f"{counts['services']:,}")
with col3:
    st.metric("⚠️ Flagged for Review", f"{counts['issues']:,}")

st.markdown("---")

# ── Navigation Cards (mobile-friendly) ─────────────────
st.markdown("### Navigation")

col1, col2 = st.columns(2)

with col1:
    st.page_link("pages/1_search.py", label="🔍  Search Customers", use_container_width=True)
    st.caption("Find customers by name or phone, view their service history")
    st.write("")
    st.page_link("pages/3_Add_Customer.py", label="➕  Add New Customer", use_container_width=True)
    st.caption("Manually add a new customer (optionally with a service)")

with col2:
    st.page_link("pages/2_reports.py", label="📈  Reports & Analytics", use_container_width=True)
    st.caption("Revenue trends, top clients, service breakdown, area map")
    st.write("")
    st.page_link("pages/4_Add_Service.py", label="🔧  Add Service", use_container_width=True)
    st.caption("Add a new service to an existing customer")
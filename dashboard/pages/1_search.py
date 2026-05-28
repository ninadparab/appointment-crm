import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import search_customers

st.set_page_config(page_title="Search", page_icon="🔍", layout="wide")
st.title("🔍 Customer Search")

# Search input
col1, col2 = st.columns([3, 1])
with col1:
    search_query = st.text_input("Search", placeholder="Enter name or phone number...", label_visibility="collapsed")
with col2:
    search_by = st.selectbox("Search by", ["both", "name", "phone"], label_visibility="collapsed")

st.markdown("---")

if search_query:
    results = search_customers(search_query, search_by)

    if not results:
        st.warning("No customers found.")
    else:
        st.success(f"Found {len(results)} customer(s)")

        for customer in results:
            with st.expander(f"👤 {customer['name']} — {customer.get('phone', 'No phone')}", expanded=len(results) == 1):

                # Customer details
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Phone:** {customer.get('phone', '—')}")
                    st.markdown(f"**Email:** {customer.get('email', '—')}")
                    st.markdown(f"**Lead Source:** {customer.get('lead_source', '—')}")
                with col2:
                    st.markdown(f"**Address:** {customer.get('address', '—')}")
                    st.markdown(f"**Comments:** {customer.get('comments', '—')}")

                # Service history
                services = customer.get("services", [])
                st.markdown(f"### Service History ({len(services)})")

                if not services:
                    st.info("No service history.")
                else:
                    services_sorted = sorted(
                        services,
                        key=lambda x: x.get("date_of_service") or "",
                        reverse=True
                    )
                    for s in services_sorted:
                        date = s.get("date_of_service", "No date")
                        nature = s.get("nature_of_service", "—")
                        amount = s.get("total_amount")
                        amount_str = f"₹{amount:,.0f}" if amount else "—"

                        st.markdown(f"- **{date}** — {nature} — {amount_str}")
else:
    st.info("Enter a name or phone number to search.")
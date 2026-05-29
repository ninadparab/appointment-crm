import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import search_customers

st.set_page_config(page_title="Search", page_icon="🔍", layout="wide")
st.title("🔍 Customer Search")

col1, col2 = st.columns([3, 1])
with col1:
    search_query = st.text_input("Search", placeholder="Enter name or phone number...",
                                  label_visibility="collapsed")
with col2:
    search_by = st.selectbox("Search by", ["both", "name", "phone"],
                              label_visibility="collapsed")

st.markdown("---")

if search_query:
    results = search_customers(search_query, search_by)

    if not results:
        st.warning("No customers found.")
    else:
        st.success(f"Found {len(results)} customer(s)")

        for customer in results:
            phone_display = customer.get('phone') or 'No phone'
            with st.expander(
                f"👤 {customer['name']} — {phone_display}",
                expanded=len(results) == 1
            ):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Primary Phone:** {customer.get('phone') or '—'}")
                    st.markdown(f"**Additional Phones:** {customer.get('additional_phones') or '—'}")
                    st.markdown(f"**Email:** {customer.get('email') or '—'}")
                    st.markdown(f"**Area:** {customer.get('area') or '—'}")
                with col2:
                    st.markdown(f"**Category:** {customer.get('category') or '—'}")
                    st.markdown(f"**Lead Source:** {customer.get('lead_source') or '—'}")
                    st.markdown(f"**Address:** {customer.get('address') or '—'}")
                    if customer.get('comments'):
                        st.markdown(f"**Comments:** {customer['comments']}")

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
                        date = s.get("date_of_service") or "No date"
                        # Format service name from main + sub category
                        main = s.get("main_category") or ""
                        sub = s.get("sub_category")
                        service_label = f"{main} — {sub}" if sub else main
                        if not service_label.strip():
                            service_label = s.get("nature_of_service") or "Unknown"

                        amount = s.get("total_amount")
                        amount_str = f"₹{amount:,.0f}" if amount else "—"

                        qty = s.get("quantity")
                        qty_str = f" ({qty} unit{'s' if qty != 1 else ''})" if qty and qty > 1 else ""

                        warning = " ⚠️" if s.get("has_issues") else ""

                        line = f"- **{date}** — {service_label}{qty_str} — {amount_str}{warning}"
                        st.markdown(line)

                        if s.get("has_issues") and s.get("issue_notes"):
                            st.caption(f"   ⚠️ {s['issue_notes']}")
else:
    st.info("Enter a name or phone number to search.")
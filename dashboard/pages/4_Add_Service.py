import streamlit as st
import sys
import os
import pandas as pd
from datetime import date

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import supabase, search_customers

st.set_page_config(page_title="Add Service", page_icon="🔧", layout="wide")
st.title("🔧 Add Service to Existing Customer")

@st.cache_data(ttl=60)
def load_service_types():
    result = supabase.table("service_types").select("*").execute()
    return result.data

service_types = load_service_types()
main_categories = sorted(set(st['main_category'] for st in service_types))

# ── Step 1: Find customer ───────────────────────
st.markdown("### 1️⃣ Find Customer")
search_query = st.text_input("Search by name or phone", placeholder="Enter name or phone")

selected_customer = None

if search_query:
    results = search_customers(search_query, "both")
    if not results:
        st.warning("No customers found. Use 'Add Customer' page to create new.")
    else:
        options = {f"{c['name']} — {c.get('phone', 'No phone')} (ID: {c['id']})": c for c in results}
        selected_label = st.selectbox(f"Select customer ({len(results)} match{'es' if len(results) != 1 else ''})", list(options.keys()))
        selected_customer = options[selected_label]

# ── Step 2: Service details ─────────────────────
if selected_customer:
    st.markdown("---")
    st.markdown(f"### 2️⃣ Add Service for **{selected_customer['name']}**")
    if selected_customer.get('phone'):
        st.caption(f"Phone: {selected_customer['phone']}")
    if selected_customer.get('area'):
        st.caption(f"Area: {selected_customer['area']}")

    with st.form("add_service_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            svc_date = st.date_input("Date of Service", value=date.today())
            main_cat = st.selectbox("Main Category", main_categories)

        with col2:
            sub_options = sorted(set(
                st_row['sub_category'] for st_row in service_types
                if st_row['main_category'] == main_cat and st_row['sub_category']
            ))
            sub_options.insert(0, "(none)")
            sub_cat = st.selectbox("Sub Category", sub_options)
            sub_cat = None if sub_cat == "(none)" else sub_cat

            quantity = st.number_input(
                "Quantity / Sq.Ft.",
                min_value=0, value=1, step=1,
                help="For Carpet, this is sq.ft. For others, units count."
            )

        with col3:
            rate = st.number_input("Rate per Unit (₹)", min_value=0.0, value=0.0)
            total = st.number_input("Total Amount (₹)", min_value=0.0, value=0.0)

        nature_text = st.text_input("Service Description (optional)")
        notes = st.text_area("Notes (optional)", height=60)

        submitted = st.form_submit_button("Add Service", type="primary")

        if submitted:
            if total == 0 and rate == 0 and quantity == 0:
                st.error("❌ Please enter at least quantity, rate, or amount")
            else:
                try:
                    # Find service_type_id
                    st_id = None
                    for st_row in service_types:
                        if st_row['main_category'] == main_cat and st_row.get('sub_category') == sub_cat:
                            st_id = st_row['id']
                            break

                    # Auto-compute total if rate × qty
                    if total == 0 and rate > 0 and quantity > 0:
                        total = rate * quantity

                    result = supabase.table("services").insert({
                        "customer_id": selected_customer['id'],
                        "service_type_id": st_id,
                        "main_category": main_cat,
                        "sub_category": sub_cat,
                        "date_of_service": svc_date.isoformat(),
                        "nature_of_service": nature_text or f"{main_cat}{' - ' + sub_cat if sub_cat else ''}",
                        "quantity": int(quantity) if quantity > 0 else None,
                        "rate_per_unit": float(rate) if rate > 0 else None,
                        "total_amount": float(total) if total > 0 else None,
                        "comments": notes or None
                    }).execute()

                    new_service = result.data[0]
                    st.success(f"✅ Service added! Service ID: **{new_service['id']}**, Total: ₹{total:,.0f}")
                    st.balloons()
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
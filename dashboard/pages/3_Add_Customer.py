import streamlit as st
import sys
import os
import pandas as pd
from datetime import date

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import supabase

st.set_page_config(page_title="Add Customer", page_icon="➕", layout="wide")
st.title("➕ Add New Customer")

# ── Helper: load service types ──────────────────────
@st.cache_data(ttl=60)
def load_service_types():
    result = supabase.table("service_types").select("*").execute()
    return result.data

service_types = load_service_types()
main_categories = sorted(set(st['main_category'] for st in service_types))

# ── Form ────────────────────────────────────────────
with st.form("add_customer_form", clear_on_submit=True):
    st.markdown("### 👤 Customer Details")
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Full Name *", placeholder="e.g. Rahul Sharma")
        phone = st.text_input("Primary Phone", placeholder="e.g. 9876543210")
        additional_phones = st.text_input(
            "Additional Phones",
            placeholder="9123456789, 02234567890",
            help="Comma-separated"
        )
        email = st.text_input("Email")
        area = st.text_input("Area", placeholder="e.g. Chembur, Bandra")

    with col2:
        address = st.text_area("Address", height=80)
        category = st.selectbox(
            "Customer Category",
            ["Residential", "Office", "Hotel", "Interior Designer",
             "Estate Agent", "Marble", "Other"]
        )
        lead_source = st.selectbox(
            "Lead Source",
            ["Walk-in", "Facebook", "Instagram", "Google",
             "Referral", "Phone call", "WhatsApp", "Other"]
        )
        comments = st.text_area("Comments", height=80)

    # ── Optional first service ──────────────────
    st.markdown("---")
    add_service = st.checkbox("Also add a service for this customer", value=False)

    if add_service:
        st.markdown("### 🔧 Service Details")
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

        nature_text = st.text_input(
            "Service Description",
            help="Free-text description shown in customer history"
        )

    submitted = st.form_submit_button("Save", type="primary")

    if submitted:
        if not name.strip():
            st.error("❌ Name is required")
        else:
            # Check duplicate phone
            dup = None
            if phone.strip():
                result = supabase.table("customers").select("id, name").eq("phone", phone.strip()).execute()
                if result.data:
                    dup = result.data[0]

            if dup:
                st.warning(f"⚠️ Customer with this phone exists: **{dup['name']}** (ID: {dup['id']})")
            else:
                try:
                    # Insert customer
                    cust_result = supabase.table("customers").insert({
                        "name": name.strip(),
                        "phone": phone.strip() or None,
                        "additional_phones": additional_phones.strip() or None,
                        "email": email.strip() or None,
                        "address": address.strip() or None,
                        "area": area.strip() or None,
                        "category": category,
                        "lead_source": lead_source,
                        "comments": comments.strip() or None
                    }).execute()
                    new_customer = cust_result.data[0]

                    # Optionally insert service
                    if add_service and (total > 0 or quantity > 0):
                        # Find service_type_id
                        st_id = None
                        for st_row in service_types:
                            if st_row['main_category'] == main_cat and st_row.get('sub_category') == sub_cat:
                                st_id = st_row['id']
                                break

                        supabase.table("services").insert({
                            "customer_id": new_customer['id'],
                            "service_type_id": st_id,
                            "main_category": main_cat,
                            "sub_category": sub_cat,
                            "date_of_service": svc_date.isoformat(),
                            "nature_of_service": nature_text or f"{main_cat}{' - ' + sub_cat if sub_cat else ''}",
                            "quantity": int(quantity) if quantity > 0 else None,
                            "rate_per_unit": float(rate) if rate > 0 else None,
                            "total_amount": float(total) if total > 0 else None
                        }).execute()
                        st.success(f"✅ Customer + Service added! Customer ID: **{new_customer['id']}**")
                    else:
                        st.success(f"✅ Customer added! ID: **{new_customer['id']}**")
                    st.balloons()
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
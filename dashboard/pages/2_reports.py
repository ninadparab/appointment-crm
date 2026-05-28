import streamlit as st
import sys
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta, date

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_all_services_in_range, get_customers_by_service_date, supabase

st.set_page_config(page_title="Reports", page_icon="📈", layout="wide")
st.title("📈 Reports & Analytics")

# ── Auto-detect data range ─────────────────────────────
@st.cache_data(ttl=300)
def get_data_range():
    result = supabase.table("services")\
        .select("date_of_service")\
        .not_.is_("date_of_service", "null")\
        .order("date_of_service")\
        .limit(1)\
        .execute()
    earliest = result.data[0]["date_of_service"] if result.data else None

    result = supabase.table("services")\
        .select("date_of_service")\
        .not_.is_("date_of_service", "null")\
        .order("date_of_service", desc=True)\
        .limit(1)\
        .execute()
    latest = result.data[0]["date_of_service"] if result.data else None

    return earliest, latest

earliest, latest = get_data_range()

if earliest and latest:
    st.info(f"📅 Data available from **{earliest}** to **{latest}**")
    default_end = pd.to_datetime(latest).date()
    default_start = max(
        pd.to_datetime(earliest).date(),
        default_end - timedelta(days=365)
    )
else:
    default_end = date.today()
    default_start = date.today() - timedelta(days=365)

# ── Date range picker ──────────────────────────────────
st.markdown("### Date Range")
col1, col2, col3 = st.columns([2, 2, 2])
with col1:
    start_date = st.date_input("Start date", value=default_start)
with col2:
    end_date = st.date_input("End date", value=default_end)
with col3:
    grouping = st.selectbox("Group by", ["month", "week", "day"])

st.markdown("---")

# ── Fetch data ─────────────────────────────────────────
with st.spinner("Loading data..."):
    services_data = get_all_services_in_range(start_date, end_date)
    unique_customers = get_customers_by_service_date(start_date, end_date)

if not services_data:
    st.warning(f"⚠️ No data found between {start_date} and {end_date}.")
    st.stop()

# ── Prepare dataframe ──────────────────────────────────
df = pd.DataFrame(services_data)
df["date_of_service"] = pd.to_datetime(df["date_of_service"])
df["total_amount"] = pd.to_numeric(df["total_amount"], errors="coerce").fillna(0)

# Extract service type name
df["service_type"] = df["service_types"].apply(
    lambda x: x["service_type_name"] if isinstance(x, dict) and x else "Unknown"
)

total_revenue = df["total_amount"].sum()

# ── Top-level metrics ──────────────────────────────────
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Active Customers", unique_customers)
with col2:
    st.metric("Total Services", len(df))
with col3:
    st.metric("Total Revenue", f"₹{total_revenue:,.0f}")

st.markdown("---")

# ── Chart 1: Revenue Over Time ─────────────────────────
st.markdown("### 💰 Revenue Over Time")
freq_map = {"day": "D", "week": "W", "month": "ME"}
df_time = df.set_index("date_of_service")\
    .resample(freq_map[grouping])\
    .agg({"total_amount": "sum", "id": "count"})\
    .reset_index()
df_time.columns = ["Date", "Revenue", "Service Count"]

fig1 = px.bar(df_time, x="Date", y="Revenue",
              title=f"Revenue by {grouping.title()}")
st.plotly_chart(fig1, use_container_width=True)

# ── Chart 2: Services Over Time ────────────────────────
st.markdown("### 🔧 Services Over Time")
fig2 = px.line(df_time, x="Date", y="Service Count",
               title=f"Service Count by {grouping.title()}", markers=True)
st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

st.markdown("---")

# ── Chart 3: Services and Revenue by Service Type ──────
st.markdown("### 🧹 Services by Service Type")

df_type = df.groupby("service_type").agg(
    Service_Count=("id", "count"),
    Total_Revenue=("total_amount", "sum")
).reset_index().sort_values("Service_Count", ascending=False)

col1, col2 = st.columns(2)

with col1:
    fig3 = px.pie(
        df_type,
        names="service_type",
        values="Service_Count",
        title="Number of Services by Type"
    )
    fig3.update_traces(textposition="inside", textinfo="percent+label")
    fig3.update_layout(showlegend=True)
    st.plotly_chart(fig3, use_container_width=True)

with col2:
    fig4 = px.pie(
        df_type,
        names="service_type",
        values="Total_Revenue",
        title="Revenue by Service Type"
    )
    fig4.update_traces(textposition="inside", textinfo="percent+label")
    fig4.update_layout(showlegend=True)
    st.plotly_chart(fig4, use_container_width=True)

st.markdown("---")

# ── Chart 4: Revenue Distribution by Bucket ────────────
st.markdown("### 📊 Revenue Distribution by Service")

def make_bucket(amount):
    if amount == 0:
        return "₹0 (No charge)"
    elif amount <= 500:
        return "₹1 - ₹500"
    elif amount <= 1000:
        return "₹501 - ₹1,000"
    elif amount <= 2000:
        return "₹1,001 - ₹2,000"
    elif amount <= 5000:
        return "₹2,001 - ₹5,000"
    elif amount <= 10000:
        return "₹5,001 - ₹10,000"
    else:
        return "₹10,000+"

bucket_order = [
    "₹0 (No charge)",
    "₹1 - ₹500",
    "₹501 - ₹1,000",
    "₹1,001 - ₹2,000",
    "₹2,001 - ₹5,000",
    "₹5,001 - ₹10,000",
    "₹10,000+"
]

df["revenue_bucket"] = df["total_amount"].apply(make_bucket)
df_buckets = df.groupby("revenue_bucket").agg(
    Count=("id", "count")
).reset_index()

df_buckets["order"] = df_buckets["revenue_bucket"].apply(
    lambda x: bucket_order.index(x) if x in bucket_order else 99
)
df_buckets = df_buckets.sort_values("order")

col1, col2 = st.columns(2)

with col1:
    fig5 = px.pie(
        df_buckets,
        names="revenue_bucket",
        values="Count",
        title="Services by Revenue Range",
        category_orders={"revenue_bucket": bucket_order}
    )
    fig5.update_traces(textposition="inside", textinfo="percent+label")
    fig5.update_layout(showlegend=True)
    st.plotly_chart(fig5, use_container_width=True)

with col2:
    # Revenue value per bucket
    df_bucket_revenue = df.groupby("revenue_bucket").agg(
        Total_Revenue=("total_amount", "sum")
    ).reset_index()
    df_bucket_revenue["order"] = df_bucket_revenue["revenue_bucket"].apply(
        lambda x: bucket_order.index(x) if x in bucket_order else 99
    )
    df_bucket_revenue = df_bucket_revenue.sort_values("order")

    fig6 = px.pie(
        df_bucket_revenue,
        names="revenue_bucket",
        values="Total_Revenue",
        title="Revenue Share by Range",
        category_orders={"revenue_bucket": bucket_order}
    )
    fig6.update_traces(textposition="inside", textinfo="percent+label")
    fig6.update_layout(showlegend=True)
    st.plotly_chart(fig6, use_container_width=True)

st.markdown("---")

# ── Export ─────────────────────────────────────────────
st.markdown("### 📥 Export Data")
csv = df.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download Services CSV",
    data=csv,
    file_name=f"services_{start_date}_to_{end_date}.csv",
    mime="text/csv"
)
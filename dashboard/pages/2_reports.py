import streamlit as st
import sys
import os
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta, date

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_all_services_in_range, get_customers_by_service_date, supabase

st.set_page_config(page_title="Reports", page_icon="📈", layout="wide")
st.title("📈 Reports & Analytics")

# ── Auto-detect data range ─────────────────────────────
@st.cache_data(ttl=300)
def get_data_range():
    result = supabase.table("services").select("date_of_service")\
        .not_.is_("date_of_service", "null")\
        .order("date_of_service").limit(1).execute()
    earliest = result.data[0]["date_of_service"] if result.data else None

    result = supabase.table("services").select("date_of_service")\
        .not_.is_("date_of_service", "null")\
        .order("date_of_service", desc=True).limit(1).execute()
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
col1, col2, col3 = st.columns(3)
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
df["main_category"] = df["main_category"].fillna("Unknown")

# Customer name + area from join
df["customer_name"] = df["customers"].apply(
    lambda x: x.get("name") if isinstance(x, dict) and x else "Unknown"
)
df["area"] = df["customers"].apply(
    lambda x: x.get("area") if isinstance(x, dict) and x else None
)

total_revenue = df["total_amount"].sum()
issues_count = df["has_issues"].sum() if "has_issues" in df.columns else 0

# ── Top metrics ────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Active Customers", unique_customers)
with col2:
    st.metric("Total Services", len(df))
with col3:
    st.metric("Total Revenue", f"₹{total_revenue:,.0f}")
with col4:
    st.metric("⚠️ Flagged Issues", f"{int(issues_count):,}")

st.markdown("---")

# ── Revenue Over Time ─────────────────────────────────
st.markdown("### 💰 Revenue Over Time")
freq_map = {"day": "D", "week": "W", "month": "ME"}
df_time = df.set_index("date_of_service")\
    .resample(freq_map[grouping])\
    .agg({"total_amount": "sum", "id": "count"})\
    .reset_index()
df_time.columns = ["Date", "Revenue", "Service Count"]

fig1 = px.bar(df_time, x="Date", y="Revenue", title=f"Revenue by {grouping.title()}")
st.plotly_chart(fig1, use_container_width=True)

# ── Services Over Time ────────────────────────────────
st.markdown("### 🔧 Services Over Time")
fig2 = px.line(df_time, x="Date", y="Service Count",
               title=f"Service Count by {grouping.title()}", markers=True)
st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# ── Service Type Pie Charts ───────────────────────────
st.markdown("### 🧹 Services by Service Type")

df_type = df.groupby("main_category").agg(
    Service_Count=("id", "count"),
    Total_Revenue=("total_amount", "sum")
).reset_index().sort_values("Service_Count", ascending=False)

col1, col2 = st.columns(2)
with col1:
    fig3 = px.pie(df_type, names="main_category", values="Service_Count",
                  title="Number of Services by Type")
    fig3.update_traces(textposition="inside", textinfo="percent+label")
    st.plotly_chart(fig3, use_container_width=True)

with col2:
    fig4 = px.pie(df_type, names="main_category", values="Total_Revenue",
                  title="Revenue by Service Type")
    fig4.update_traces(textposition="inside", textinfo="percent+label")
    st.plotly_chart(fig4, use_container_width=True)

st.markdown("---")

# ── Revenue Distribution Buckets ──────────────────────
st.markdown("### 📊 Revenue Distribution by Service")

def make_bucket(amount):
    if amount == 0: return "₹0 (No charge)"
    elif amount <= 500: return "₹1 - ₹500"
    elif amount <= 1000: return "₹501 - ₹1,000"
    elif amount <= 2000: return "₹1,001 - ₹2,000"
    elif amount <= 5000: return "₹2,001 - ₹5,000"
    elif amount <= 10000: return "₹5,001 - ₹10,000"
    else: return "₹10,000+"

bucket_order = ["₹0 (No charge)", "₹1 - ₹500", "₹501 - ₹1,000",
                "₹1,001 - ₹2,000", "₹2,001 - ₹5,000",
                "₹5,001 - ₹10,000", "₹10,000+"]

df["revenue_bucket"] = df["total_amount"].apply(make_bucket)
df_buckets = df.groupby("revenue_bucket").agg(Count=("id", "count")).reset_index()
df_buckets["order"] = df_buckets["revenue_bucket"].apply(
    lambda x: bucket_order.index(x) if x in bucket_order else 99
)
df_buckets = df_buckets.sort_values("order")

col1, col2 = st.columns(2)
with col1:
    fig5 = px.pie(df_buckets, names="revenue_bucket", values="Count",
                  title="Services by Revenue Range",
                  category_orders={"revenue_bucket": bucket_order})
    fig5.update_traces(textposition="inside", textinfo="percent+label")
    st.plotly_chart(fig5, use_container_width=True)

with col2:
    df_bucket_rev = df.groupby("revenue_bucket").agg(
        Total_Revenue=("total_amount", "sum")
    ).reset_index()
    df_bucket_rev["order"] = df_bucket_rev["revenue_bucket"].apply(
        lambda x: bucket_order.index(x) if x in bucket_order else 99
    )
    df_bucket_rev = df_bucket_rev.sort_values("order")

    fig6 = px.pie(df_bucket_rev, names="revenue_bucket", values="Total_Revenue",
                  title="Revenue Share by Range",
                  category_orders={"revenue_bucket": bucket_order})
    fig6.update_traces(textposition="inside", textinfo="percent+label")
    st.plotly_chart(fig6, use_container_width=True)

st.markdown("---")

# ── Top 10 Clients ────────────────────────────────────
st.markdown("### 🏆 Top 10 Clients")

top_range = (
    df.groupby("customer_name")
    .agg(Services=("id", "count"), Revenue=("total_amount", "sum"))
    .reset_index()
    .sort_values("Revenue", ascending=False)
    .head(10)
)
top_range["Revenue"] = top_range["Revenue"].apply(lambda x: f"₹{x:,.0f}")

col1, col2 = st.columns(2)
with col1:
    st.markdown(f"**Top 10 by Revenue ({start_date} to {end_date})**")
    st.dataframe(top_range, use_container_width=True, hide_index=True)

# Top 10 this month
today = datetime.now()
month_start = today.replace(day=1).date()
month_end = today.date()
services_month = get_all_services_in_range(month_start, month_end)

with col2:
    if services_month:
        df_m = pd.DataFrame(services_month)
        df_m["total_amount"] = pd.to_numeric(df_m["total_amount"], errors="coerce").fillna(0)
        df_m["customer_name"] = df_m["customers"].apply(
            lambda x: x.get("name") if isinstance(x, dict) and x else "Unknown"
        )
        top_month = (
            df_m.groupby("customer_name")
            .agg(Services=("id", "count"), Revenue=("total_amount", "sum"))
            .reset_index()
            .sort_values("Revenue", ascending=False)
            .head(10)
        )
        top_month["Revenue"] = top_month["Revenue"].apply(lambda x: f"₹{x:,.0f}")
        st.markdown(f"**Top 10 This Month ({month_start.strftime('%B %Y')})**")
        st.dataframe(top_month, use_container_width=True, hide_index=True)
    else:
        st.markdown(f"**Top 10 This Month ({month_start.strftime('%B %Y')})**")
        st.info("No services this month yet.")

st.markdown("---")

# ── Revenue by Area + Map ─────────────────────────────
st.markdown("### 🗺️ Revenue by Area (Mumbai)")

MUMBAI_AREAS = {
    "Chembur": (19.0633, 72.8997), "Bandra": (19.0596, 72.8295),
    "Andheri": (19.1136, 72.8697), "Powai": (19.1197, 72.9056),
    "Malad": (19.1864, 72.8493), "Borivali": (19.2335, 72.8479),
    "Goregaon": (19.1647, 72.8526), "Juhu": (19.1075, 72.8263),
    "Worli": (19.0176, 72.8156), "Lower Parel": (19.0070, 72.8312),
    "Colaba": (18.9067, 72.8147), "Churchgate": (18.9322, 72.8262),
    "South Mumbai": (18.9322, 72.8262), "Dadar": (19.0186, 72.8421),
    "Mahim": (19.0410, 72.8390), "Vile Parle": (19.1067, 72.8412),
    "Vileparle": (19.1067, 72.8412), "Santacruz": (19.0810, 72.8412),
    "Khar": (19.0667, 72.8333), "Versova": (19.1357, 72.8195),
    "Kandivali": (19.2030, 72.8540), "Mira Road": (19.2952, 72.8544),
    "Mulund": (19.1726, 72.9572), "Bhandup": (19.1418, 72.9341),
    "Ghatkopar": (19.0863, 72.9082), "Kurla": (19.0726, 72.8845),
    "Sion": (19.0432, 72.8606), "Matunga": (19.0270, 72.8569),
    "Byculla": (18.9748, 72.8326), "Navi Mumbai": (19.0330, 73.0297),
    "Thane": (19.2183, 72.9781), "Vasai": (19.4259, 72.8225),
    "Virar": (19.4559, 72.8113),
}

df_area = df[df["area"].notna()].groupby("area").agg(
    Services=("id", "count"),
    Revenue=("total_amount", "sum")
).reset_index().sort_values("Revenue", ascending=False)

col1, col2 = st.columns([2, 3])
with col1:
    st.markdown("**Top Areas by Revenue**")
    df_display = df_area.head(15).copy()
    df_display["Revenue"] = df_display["Revenue"].apply(lambda x: f"₹{x:,.0f}")
    st.dataframe(df_display, use_container_width=True, hide_index=True)

with col2:
    fig_area_bar = px.bar(df_area.head(15), x="area", y="Revenue",
                          title="Revenue by Area (Top 15)",
                          color="Revenue", color_continuous_scale="blues")
    fig_area_bar.update_xaxes(tickangle=45)
    st.plotly_chart(fig_area_bar, use_container_width=True)

# Map
st.markdown("**Geographic Distribution**")
df_map = df_area.copy()
df_map["lat"] = df_map["area"].apply(lambda x: MUMBAI_AREAS.get(x, (None, None))[0])
df_map["lon"] = df_map["area"].apply(lambda x: MUMBAI_AREAS.get(x, (None, None))[1])
df_map = df_map.dropna(subset=["lat", "lon"])

if len(df_map) > 0:
    fig_map = px.scatter_mapbox(
        df_map, lat="lat", lon="lon",
        size="Revenue", color="Revenue",
        hover_name="area",
        hover_data={"Services": True, "Revenue": ":,.0f", "lat": False, "lon": False},
        color_continuous_scale="Viridis", size_max=50,
        zoom=10, center={"lat": 19.0760, "lon": 72.8777},
        title=f"Revenue by Mumbai Area ({len(df_map)} areas mapped)"
    )
    fig_map.update_layout(mapbox_style="open-street-map", height=600,
                          margin={"r": 0, "t": 40, "l": 0, "b": 0})
    st.plotly_chart(fig_map, use_container_width=True)

    unmapped = set(df_area["area"]) - set(df_map["area"])
    if unmapped:
        st.caption(f"ℹ️ Areas not on map ({len(unmapped)}): {', '.join(sorted(unmapped)[:10])}{'...' if len(unmapped) > 10 else ''}")

st.markdown("---")

# ── Export ────────────────────────────────────────────
st.markdown("### 📥 Export Data")
df_export = df.drop(columns=["customers"], errors="ignore")
csv = df_export.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download Services CSV",
    data=csv,
    file_name=f"services_{start_date}_to_{end_date}.csv",
    mime="text/csv"
)
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# ── SEARCH ─────────────────────────────────────────────

def search_customers(query, search_by="both"):
    if not query:
        return []

    select_clause = "*, services(*)"

    if search_by == "name":
        result = supabase.table("customers")\
            .select(select_clause)\
            .ilike("name", f"%{query}%")\
            .order("name")\
            .limit(50)\
            .execute()
    elif search_by == "phone":
        result = supabase.table("customers")\
            .select(select_clause)\
            .or_(f"phone.ilike.%{query}%,additional_phones.ilike.%{query}%")\
            .limit(50)\
            .execute()
    else:
        result = supabase.table("customers")\
            .select(select_clause)\
            .or_(f"name.ilike.%{query}%,phone.ilike.%{query}%,additional_phones.ilike.%{query}%")\
            .limit(50)\
            .execute()
    return result.data

# ── REPORTS ────────────────────────────────────────────

def get_all_services_in_range(start_date, end_date):
    """Get all services in date range with customer name and area joined."""
    all_data = []
    page = 0
    page_size = 1000

    while True:
        result = supabase.table("services")\
            .select("*, customers(name, area)")\
            .gte("date_of_service", start_date.isoformat())\
            .lte("date_of_service", end_date.isoformat())\
            .range(page * page_size, (page + 1) * page_size - 1)\
            .execute()

        all_data.extend(result.data)
        if len(result.data) < page_size:
            break
        page += 1

    return all_data

def get_customers_by_service_date(start_date, end_date):
    """Count unique customers who had a service in the date range."""
    all_data = []
    page = 0
    page_size = 1000

    while True:
        result = supabase.table("services")\
            .select("customer_id")\
            .gte("date_of_service", start_date.isoformat())\
            .lte("date_of_service", end_date.isoformat())\
            .range(page * page_size, (page + 1) * page_size - 1)\
            .execute()

        all_data.extend(result.data)
        if len(result.data) < page_size:
            break
        page += 1

    return len(set(s["customer_id"] for s in all_data))

def get_total_counts():
    customers = supabase.table("customers").select("id", count="exact").execute()
    services = supabase.table("services").select("id", count="exact").execute()
    issues = supabase.table("services").select("id", count="exact").eq("has_issues", True).execute()
    return {
        "customers": customers.count,
        "services": services.count,
        "issues": issues.count
    }
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

    if search_by == "name":
        result = supabase.table("customers")\
            .select("*, services(*)")\
            .ilike("name", f"%{query}%")\
            .order("name")\
            .limit(50)\
            .execute()
    elif search_by == "phone":
        result = supabase.table("customers")\
            .select("*, services(*)")\
            .ilike("phone", f"%{query}%")\
            .limit(50)\
            .execute()
    else:
        result = supabase.table("customers")\
            .select("*, services(*)")\
            .or_(f"name.ilike.%{query}%,phone.ilike.%{query}%")\
            .limit(50)\
            .execute()
    return result.data

# ── REPORTS ────────────────────────────────────────────

def get_all_services_in_range(start_date, end_date):
    """Get ALL services in range with pagination — bypasses 1000 row limit"""
    all_data = []
    page = 0
    page_size = 1000

    while True:
        result = supabase.table("services")\
            .select("*, customers(name), service_types(service_type_name)")\
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
    """Count unique customers who had a service in the date range"""
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

    unique_customers = set(s["customer_id"] for s in all_data)
    return len(unique_customers)

def get_total_counts():
    customers = supabase.table("customers")\
        .select("id", count="exact").execute()
    services = supabase.table("services")\
        .select("id", count="exact").execute()
    return {
        "customers": customers.count,
        "services": services.count
    }
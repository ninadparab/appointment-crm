import os
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

FILE = "Cleaned_CRM_Customer_Service_Data.xlsx"

# ── STEP 1: Migrate Service Types ──────────────────────

def migrate_service_types():
    print("\n📦 Migrating Service Types...")
    df = pd.read_excel(FILE, sheet_name="ServiceTypes")
    
    records = []
    for _, row in df.iterrows():
        records.append({
            "service_type_name": str(row["service_type_name"]) if pd.notna(row["service_type_name"]) else None,
            "subtype": str(row["subtype"]) if pd.notna(row["subtype"]) else None,
            "keywords": str(row["keywords_or_rules"]) if pd.notna(row["keywords_or_rules"]) else None
        })
    
    result = supabase.table("service_types").insert(records).execute()
    print(f"✅ Inserted {len(result.data)} service types")
    return {r["service_type_name"]: r["id"] for r in result.data}

# ── STEP 2: Migrate Customers ───────────────────────────

def migrate_customers():
    print("\n👥 Migrating Customers...")
    df = pd.read_excel(FILE, sheet_name="Customers")
    
    records = []
    for _, row in df.iterrows():
        records.append({
            "name": str(row["name"]) if pd.notna(row["name"]) else "Unknown",
            "phone": str(row["phone"]) if pd.notna(row["phone"]) else None,
            "email": str(row["email"]) if pd.notna(row["email"]) else None,
            "address": str(row["address"]) if pd.notna(row["address"]) else None,
            "comments": str(row["comments"]) if pd.notna(row["comments"]) else None,
            "lead_source": "Unknown"
        })
    
    # Insert in batches of 500 (Supabase limit)
    batch_size = 500
    all_inserted = []
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        result = supabase.table("customers").insert(batch).execute()
        all_inserted.extend(result.data)
        print(f"  Inserted {len(all_inserted)}/{len(records)} customers...")

    print(f"✅ Inserted {len(all_inserted)} customers")
    
    # Return mapping of original customer_id to Supabase id
    df_reset = df.reset_index(drop=True)
    return {
        str(df_reset.iloc[i]["customer_id"]): all_inserted[i]["id"]
        for i in range(len(all_inserted))
    }

# ── STEP 3: Migrate Services ────────────────────────────

def migrate_services(customer_id_map):
    print("\n🔧 Migrating Services...")
    df = pd.read_excel(FILE, sheet_name="Services")

    records = []
    employee_assignments = []  # collect for junction table

    for _, row in df.iterrows():
        # Map original customer_id to Supabase customer id
        original_cust_id = str(row["customer_id"])
        supabase_cust_id = customer_id_map.get(original_cust_id)

        if not supabase_cust_id:
            continue

        # Format date
        formatted_date = None
        if pd.notna(row["date_of_service"]):
            try:
                formatted_date = pd.to_datetime(row["date_of_service"]).strftime("%Y-%m-%d")
            except:
                formatted_date = None

        records.append({
            "customer_id": supabase_cust_id,
            "date_of_service": formatted_date,
            "nature_of_service": str(row["nature_of_service"]) if pd.notna(row["nature_of_service"]) else None,
            "quantity": int(row["quantity_of_service"]) if pd.notna(row["quantity_of_service"]) else None,
            "total_amount": float(row["total_amount"]) if pd.notna(row["total_amount"]) else None,
            "comments": str(row["comments"]) if pd.notna(row["comments"]) else None
        })

        # Collect employee assignments for later
        employee_assignments.append({
            "service_row_index": len(records) - 1,
            "employees": [
                str(row[f"employee_id_{i}"]) 
                for i in range(1, 5) 
                if pd.notna(row.get(f"employee_id_{i}"))
            ]
        })

    # Insert services in batches
    batch_size = 500
    all_inserted = []
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        result = supabase.table("services").insert(batch).execute()
        all_inserted.extend(result.data)
        print(f"  Inserted {len(all_inserted)}/{len(records)} services...")

    print(f"✅ Inserted {len(all_inserted)} services")
    return all_inserted, employee_assignments

# ── STEP 4: Migrate Service Assignments ─────────────────

def migrate_assignments(all_services, employee_assignments):
    print("\n👷 Migrating Service Assignments...")

    assignments = []
    for item in employee_assignments:
        service = all_services[item["service_row_index"]]
        for emp_id in item["employees"]:
            assignments.append({
                "service_id": service["id"],
                "employee_id": None,  # employees not yet in DB
                "role": "helper"
            })

    print(f"ℹ️  {len(assignments)} assignments found")
    print("⚠️  Employee records not migrated yet — add employees first")
    print("   Run this script again after adding employees to migrate assignments")

# ── RUN MIGRATION ───────────────────────────────────────

def run_migration():
    print("🚀 Starting migration...\n")
    print("=" * 50)

    # Step 1
    migrate_service_types()

    # Step 2
    customer_id_map = migrate_customers()

    # Step 3
    all_services, employee_assignments = migrate_services(customer_id_map)

    # Step 4
    migrate_assignments(all_services, employee_assignments)

    print("\n" + "=" * 50)
    print("✅ Migration complete!")
    print(f"   Service types, customers and services are now in Supabase")
    print(f"   Add employee records next to complete service assignments")

run_migration()
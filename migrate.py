import os
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

FILE = "Cleaned_CRM_Customer_Service_Data.xlsx"

def migrate_service_types():
    print("\n📦 Migrating Service Types...")
    df = pd.read_excel(FILE, sheet_name="ServiceTypes")

    records = []
    for _, row in df.iterrows():
        records.append({
            "original_id": str(row["service_type_id"]),  # store original ST001 etc
            "service_type_name": str(row["service_type_name"]) if pd.notna(row["service_type_name"]) else None,
            "subtype": str(row["subtype"]) if pd.notna(row["subtype"]) else None,
            "keywords": str(row["keywords_or_rules"]) if pd.notna(row["keywords_or_rules"]) else None
        })

    result = supabase.table("service_types").insert(records).execute()
    print(f"✅ Inserted {len(result.data)} service types")

    # Return mapping of original_id → supabase id
    return {r["original_id"]: r["id"] for r in result.data}

def migrate_customers():
    print("\n👥 Migrating Customers...")
    df = pd.read_excel(FILE, sheet_name="Customers")

    records = []
    original_ids = []
    for _, row in df.iterrows():
        records.append({
            "name": str(row.get("name", "Unknown")) if pd.notna(row.get("name")) else "Unknown",
            "phone": str(row.get("phone", "")) if pd.notna(row.get("phone")) else None,
            "email": str(row.get("email", "")) if pd.notna(row.get("email")) else None,
            "address": str(row.get("address", "")) if pd.notna(row.get("address")) else None,
            "comments": str(row.get("comments", "")) if pd.notna(row.get("comments")) else None,
            "lead_source": "Migrated"
        })
        original_ids.append(str(row.get("customer_id", "")))

    batch_size = 500
    all_inserted = []
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        result = supabase.table("customers").insert(batch).execute()
        all_inserted.extend(result.data)
        print(f"  Inserted {len(all_inserted)}/{len(records)} customers...")

    print(f"✅ Inserted {len(all_inserted)} customers")
    return {original_ids[i]: all_inserted[i]["id"] for i in range(len(all_inserted))}

def migrate_services(customer_id_map, service_type_map):
    print("\n🔧 Migrating Services...")
    df = pd.read_excel(FILE, sheet_name="Services")

    records = []
    service_assignments = []  # for junction table later
    skipped = 0

    for _, row in df.iterrows():
        original_cust_id = str(row.get("customer_id", ""))
        supabase_cust_id = customer_id_map.get(original_cust_id)

        if not supabase_cust_id:
            skipped += 1
            continue

        # Get raw service type ids string e.g. "ST001; ST002; ST006"
        raw_ids = str(row.get("service_type_ids", "")) if pd.notna(row.get("service_type_ids")) else ""

        # Get first valid service type for main service_type_id field
        first_service_type_id = None
        if raw_ids:
            for st_id in [s.strip() for s in raw_ids.split(";")]:
                if st_id in service_type_map:
                    first_service_type_id = service_type_map[st_id]
                    break

        # Format date
        formatted_date = None
        if pd.notna(row.get("date_of_service")):
            try:
                formatted_date = pd.to_datetime(row["date_of_service"]).strftime("%Y-%m-%d")
            except:
                formatted_date = None

        records.append({
            "customer_id": supabase_cust_id,
            "service_type_id": first_service_type_id,
            "service_type_ids_raw": raw_ids,  # store all original IDs
            "date_of_service": formatted_date,
            "nature_of_service": str(row.get("nature_of_service", "")) if pd.notna(row.get("nature_of_service")) else None,
            "quantity": int(row["quantity_of_service"]) if pd.notna(row.get("quantity_of_service")) else None,
            "total_amount": float(row["total_amount"]) if pd.notna(row.get("total_amount")) else None,
            "comments": str(row.get("comments", "")) if pd.notna(row.get("comments")) else None
        })

    if skipped:
        print(f"⚠️  Skipped {skipped} services with missing customer")

    batch_size = 500
    all_inserted = []
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        result = supabase.table("services").insert(batch).execute()
        all_inserted.extend(result.data)
        print(f"  Inserted {len(all_inserted)}/{len(records)} services...")

    print(f"✅ Inserted {len(all_inserted)} services")

def run_migration():
    print("🚀 Starting migration...")
    print("=" * 50)

    service_type_map = migrate_service_types()
    print(f"Service type map sample: {dict(list(service_type_map.items())[:3])}")

    customer_id_map = migrate_customers()
    migrate_services(customer_id_map, service_type_map)

    print("\n" + "=" * 50)
    print("✅ Migration complete!")

if __name__ == "__main__":
    run_migration()
"""
Fresh upload from homecare_normalized.xlsx v3.
Includes canonical service types, issue flags, amount fixes.
"""

import os
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

FILE = "homecare_normalized.xlsx"

def insert_batched(table, records, batch_size=500):
    all_inserted = []
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        result = supabase.table(table).insert(batch).execute()
        all_inserted.extend(result.data)
        print(f"   Inserted {len(all_inserted)}/{len(records)}...")
    return all_inserted

def migrate_service_types():
    print("\n📦 Migrating canonical service types...")
    df = pd.read_excel(FILE, sheet_name="ServiceTypes")

    records = []
    excel_ids = []
    for _, row in df.iterrows():
        records.append({
            'canonical_name': str(row['canonical_name']),
            'main_category': str(row['main_category']),
            'sub_category': str(row['sub_category']) if pd.notna(row['sub_category']) else None
        })
        excel_ids.append(row['service_type_id'])

    inserted = insert_batched("service_types", records)
    print(f"✅ Inserted {len(inserted)} service types")
    return {excel_ids[i]: inserted[i]['id'] for i in range(len(inserted))}

def migrate_customers():
    print("\n👥 Migrating customers...")
    df = pd.read_excel(FILE, sheet_name="Customers")

    records = []
    excel_ids = []
    for _, row in df.iterrows():
        records.append({
            'name': str(row['name']).strip() if pd.notna(row['name']) else 'Unknown',
            'phone': str(row['phone']) if pd.notna(row['phone']) else None,
            'additional_phones': str(row['additional_phones']) if pd.notna(row['additional_phones']) else None,
            'email': str(row['email']) if pd.notna(row['email']) else None,
            'address': str(row['address']) if pd.notna(row['address']) else None,
            'area': str(row['area']) if pd.notna(row['area']) else None,
            'category': str(row['category']) if pd.notna(row['category']) else None,
            'lead_source': 'Migrated-Homecare'
        })
        excel_ids.append(row['customer_id'])

    inserted = insert_batched("customers", records)
    print(f"✅ Inserted {len(inserted)} customers")
    return {excel_ids[i]: inserted[i]['id'] for i in range(len(inserted))}

def migrate_services(customer_map, type_map):
    print("\n🔧 Migrating services...")
    df = pd.read_excel(FILE, sheet_name="Services")

    records = []
    skipped = 0
    for _, row in df.iterrows():
        cust_id = customer_map.get(row['customer_id'])
        if not cust_id:
            skipped += 1
            continue

        service_type_id = type_map.get(row['service_type_id']) if pd.notna(row['service_type_id']) else None

        date_str = None
        if pd.notna(row['date_of_service']):
            try:
                date_str = pd.to_datetime(row['date_of_service']).strftime("%Y-%m-%d")
            except:
                pass

        # Sanity caps
        amount = float(row['total_amount']) if pd.notna(row['total_amount']) else None
        rate = float(row['rate_per_unit']) if pd.notna(row['rate_per_unit']) else None
        amount_in_comments = float(row['amount_in_comments']) if pd.notna(row['amount_in_comments']) else None

        records.append({
            'customer_id': cust_id,
            'service_type_id': service_type_id,
            'main_category': str(row['main_category']) if pd.notna(row['main_category']) else None,
            'sub_category': str(row['sub_category']) if pd.notna(row['sub_category']) else None,
            'date_of_service': date_str,
            'nature_of_service': str(row['nature_of_service']) if pd.notna(row['nature_of_service']) else None,
            'quantity': int(row['quantity']) if pd.notna(row['quantity']) else None,
            'rate_per_unit': rate,
            'total_amount': amount,
            'has_issues': bool(row['has_issues']) if pd.notna(row['has_issues']) else False,
            'issue_notes': str(row['issue_notes']) if pd.notna(row['issue_notes']) else None,
            'amount_in_comments': amount_in_comments,
            'category': str(row['category']) if pd.notna(row['category']) else None
        })

    if skipped:
        print(f"   Skipped (no customer match): {skipped}")
    insert_batched("services", records)
    print(f"✅ Inserted {len(records)} services")

def run_migration():
    print("🚀 Starting fresh migration v3")
    print("=" * 60)
    type_map = migrate_service_types()
    customer_map = migrate_customers()
    migrate_services(customer_map, type_map)
    print("\n" + "=" * 60)
    print("✅ Done!")

if __name__ == "__main__":
    confirm = input("⚠️  This assumes tables are EMPTY. Continue? (y/N): ")
    if confirm.lower() == 'y':
        run_migration()
    else:
        print("Cancelled.")
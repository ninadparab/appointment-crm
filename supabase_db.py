import os
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# ── CUSTOMERS ──────────────────────────────────────────

def find_customer_by_phone(phone):
    """Check if customer already exists by phone number"""
    result = supabase.table("customers")\
        .select("*")\
        .eq("phone", phone)\
        .execute()
    return result.data[0] if result.data else None

def create_customer(data):
    """Create a new customer record"""
    result = supabase.table("customers").insert({
        "name": data.get("customer_name", "Unknown"),
        "phone": data.get("phone"),
        "lead_source": data.get("lead_source")
    }).execute()
    return result.data[0]

def get_or_create_customer(data):
    """Look up customer by phone, create if not found"""
    phone = data.get("phone")
    
    if phone:
        existing = find_customer_by_phone(phone)
        if existing:
            print(f"Existing customer found: {existing['name']}")
            return existing, False  # False = not newly created
    
    new_customer = create_customer(data)
    print(f"New customer created: {new_customer['name']}")
    return new_customer, True  # True = newly created

# ── SERVICES ───────────────────────────────────────────

def create_service(customer_id, data):
    """Create a new service record linked to customer"""
 # Convert date from DD-MM-YYYY to YYYY-MM-DD if needed
    raw_date = data.get("date")
    formatted_date = None
    if raw_date:
        try:
            formatted_date = datetime.strptime(raw_date, "%d-%m-%Y").strftime("%Y-%m-%d")
        except ValueError:
            try:
                formatted_date = datetime.strptime(raw_date, "%Y-%m-%d").strftime("%Y-%m-%d")
            except ValueError:
                formatted_date = None


    result = supabase.table("services").insert({
        "customer_id": customer_id,
        "date_of_service": formatted_date,
        "nature_of_service": data.get("service_requested"),
        "comments": data.get("notes")
    }).execute()
    return result.data[0]

# ── FULL FLOW ───────────────────────────────────────────

def save_appointment(appointment_data):
    """Main function called by pipeline"""
    
    # Step 1: Find or create customer
    customer, is_new = get_or_create_customer(appointment_data)
    
    # Step 2: Create service record
    service = create_service(customer["id"], appointment_data)
    
    print(f"Service created with ID: {service['id']}")
    return {
        "customer": customer,
        "service": service,
        "is_new_customer": is_new
    }

# ── TEST ────────────────────────────────────────────────

if __name__ == "__main__":
    test_data = {
        "customer_name": "Rahul Sharma",
        "phone": "98765 43210",
        "date": "2026-05-18",
        "time": "15:00",
        "service_requested": "sofa cleaning",
        "lead_source": "Facebook",
        "notes": None
    }

    result = save_appointment(test_data)
    print("\nFull result:")
    print(f"Customer ID: {result['customer']['id']}")
    print(f"Service ID: {result['service']['id']}")
    print(f"Is new customer: {result['is_new_customer']}")
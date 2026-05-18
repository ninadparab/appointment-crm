import requests
import os
from dotenv import load_dotenv
from zoho_auth_manager import ZohoAuthManager

load_dotenv()

auth = ZohoAuthManager()

def create_lead(appointment_data):
    url = f"{os.getenv('ZOHO_API_DOMAIN')}/crm/v2/Leads"

    payload = {
        "data": [{
            "Last_Name": appointment_data.get("customer_name", "Unknown"),
            "Phone": appointment_data.get("phone"),
            "Description": f"Appointment: {appointment_data.get('service_requested')} on {appointment_data.get('date')} at {appointment_data.get('time')}"
        }]
    }

    response = requests.post(
        url,
        headers=auth.get_headers(),
        json=payload
    )
    return response.json()

# Test
test_appointment = {
    "customer_name": "Rahul Sharma",
    "phone": "98765 43210",
    "date": "16-05-2026",
    "time": "15:00",
    "service_requested": "haircut",
    "notes": None
}

result = create_lead(test_appointment)
print(result)
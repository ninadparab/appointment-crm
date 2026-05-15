import os
import json
from datetime import date
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def extract_appointment(transcript):
    today = date.today().strftime("%d %B %Y")  # e.g. "15 May 2026"
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """You are a helpful assistant that extracts appointment 
                details from customer call transcripts. Always respond with valid 
                JSON only, no explanation."""
            },
            {
                "role": "user",
                "content": f"""Today's date is {today}. 
                Extract appointment details from this transcript:

                \"{transcript}\"

                Return a JSON object with these fields:
                - customer_name (string or null)
                - phone (string or null)
                - date (string in DD-MM-YYYY format or null)
                - time (string in HH:MM format or null)
                - service_requested (string or null)
                - notes (string or null)
                """
            }
        ]
    )
    
    result = response.choices[0].message.content
    return json.loads(result)

# Test
sample_transcript = "Hi, I'd like to book an appointment for tomorrow at 3pm. My name is Rahul Sharma and my number is 98765 43210. I need a sofa cleaning."

appointment = extract_appointment(sample_transcript)
print(json.dumps(appointment, indent=2))
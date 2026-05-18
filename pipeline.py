import os
import json
from datetime import date
from openai import OpenAI
from dotenv import load_dotenv
from supabase_db import save_appointment

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Step 1 — Transcribe audio
def transcribe_audio(file_path):
    if os.getenv("USE_INDIAN_LANGUAGES", "false").lower() == "true":
        print("🇮🇳 Indian language mode ON — using Sarvam AI")
        from transcribe_sarvam import transcribe_audio_indian
        return transcribe_audio_indian(file_path)
    
    print("🇬🇧 English mode — using OpenAI Whisper")
    with open(file_path, "rb") as audio_file:
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="en"
        )
    print(f"Transcript: {response.text}")
    return response.text

# Step 2 — Extract appointment details
def extract_appointment(transcript):
    print("Extracting appointment details...")
    today = date.today().strftime("%d %B %Y")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """You are a helpful assistant that extracts appointment 
                details from customer call transcripts. Always respond with valid 
                JSON only, no explanation, no markdown, no code blocks."""
            },
            {
                "role": "user",
                "content": f"""Today's date is {today}.
                Extract appointment details from this transcript:

                \"{transcript}\"

                Return a JSON object with these fields:
                - customer_name (string or null — always write in Roman/English script, not Devanagari)
                - phone (string or null)
                - date (string in YYYY-MM-DD format only, or null)
                - time (string in HH:MM format or null)
                - service_requested (string or null — in English)
                - lead_source (Facebook / Instagram / Google / Referral / Walk-in / Unknown)
                - notes (string or null)
                
                Return ONLY the JSON object. No markdown. No code blocks. No explanation.
                """
            }
        ]
    )

    result = response.choices[0].message.content.strip()
    print(f"GPT raw response: {result}")

    # Strip markdown code blocks if GPT added them
    if result.startswith("```"):
        result = result.split("```")[1]
        if result.startswith("json"):
            result = result[4:]
        result = result.strip()

    # Handle empty response
    if not result:
        print("Warning: GPT returned empty response, using defaults")
        return {
            "customer_name": None,
            "phone": None,
            "date": None,
            "time": None,
            "service_requested": None,
            "lead_source": "Unknown",
            "notes": None
        }

    return json.loads(result)

# Step 3 — Save to Supabase
def run_pipeline(audio_file_path):
    print("\n🚀 Starting pipeline...\n")

    transcript = transcribe_audio(audio_file_path)
    appointment = extract_appointment(transcript)
    result = save_appointment(appointment)

    if result:
        print(f"\n✅ Success!")
        print(f"Customer: {result['customer']['name']}")
        print(f"Service ID: {result['service']['id']}")
        print(f"New customer: {result['is_new_customer']}")

# CORRECT — only runs when you execute pipeline.py directly
if __name__ == "__main__":
    run_pipeline("test_call_marathi.m4a")
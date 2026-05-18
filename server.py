import os
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from pipeline import transcribe_audio, extract_appointment
from supabase_db import save_appointment

load_dotenv()

app = Flask(__name__)

# ── PHONE CALL WEBHOOK (Exotel) ─────────────────────────────

@app.route("/webhook/call", methods=["POST"])
def handle_call():
    print("\n📞 Incoming call webhook...")

    recording_url = request.form.get("RecordingUrl")
    caller_number = request.form.get("CallFrom")
    call_duration = request.form.get("Duration")
    call_status = request.form.get("Status")

    print(f"Caller: {caller_number}")
    print(f"Duration: {call_duration} seconds")
    print(f"Status: {call_status}")

    # Ignore short or incomplete calls
    if not recording_url:
        print("No recording URL, skipping...")
        return jsonify({"status": "ignored", "reason": "no recording"}), 200

    if call_status != "completed":
        print(f"Call not completed, skipping...")
        return jsonify({"status": "ignored", "reason": "call not completed"}), 200

    if int(call_duration or 0) < 30:
        print("Call too short, skipping...")
        return jsonify({"status": "ignored", "reason": "call too short"}), 200

    # Download audio
    audio_path = download_audio(
        recording_url,
        auth=(os.getenv("EXOTEL_API_KEY"), os.getenv("EXOTEL_API_TOKEN"))
    )

    # Run pipeline
    return process_audio(audio_path)


# ── WHATSAPP WEBHOOK ─────────────────────────────────────────

@app.route("/webhook/whatsapp", methods=["GET", "POST"])
def handle_whatsapp():

    # WhatsApp verification handshake (one-time setup)
    if request.method == "GET":
        verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN")
        if request.args.get("hub.verify_token") == verify_token:
            return request.args.get("hub.challenge"), 200
        return "Verification failed", 403

    # Incoming message
    print("\n💬 Incoming WhatsApp message...")
    data = request.json

    try:
        message = data["entry"][0]["changes"][0]["value"]

        if "messages" not in message:
            return jsonify({"status": "ignored"}), 200

        msg = message["messages"][0]

        if msg["type"] != "text":
            print("Non-text message, skipping...")
            return jsonify({"status": "ignored"}), 200

        text = msg["text"]["body"]
        sender_phone = msg["from"]

        print(f"From: {sender_phone}")
        print(f"Message: {text}")

        # Extract appointment directly from text (no STT needed)
        appointment = extract_appointment(text)
        appointment["phone"] = sender_phone

        # Save to Supabase
        result = save_appointment(appointment)

        print(f"✅ Saved — Customer: {result['customer']['name']}")
        return jsonify({"status": "success"}), 200

    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# ── SHARED HELPERS ───────────────────────────────────────────

def download_audio(url, auth=None):
    print("Downloading audio...")
    response = requests.get(url, auth=auth)
    audio_path = "temp_call.mp3"
    with open(audio_path, "wb") as f:
        f.write(response.content)
    print("Audio downloaded!")
    return audio_path

def process_audio(audio_path):
    try:
        transcript = transcribe_audio(audio_path)
        appointment = extract_appointment(transcript)
        result = save_appointment(appointment)

        print(f"✅ Success — Customer: {result['customer']['name']}")
        return jsonify({"status": "success"}), 200

    except Exception as e:
        print(f"❌ Pipeline error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# ── HEALTH CHECK ─────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "running"}), 200


# ── START SERVER ─────────────────────────────────────────────

if __name__ == "__main__":
    app.run(port=5000, debug=True)
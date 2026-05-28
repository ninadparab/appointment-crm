import os
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from pipeline import transcribe_audio, extract_appointment
from supabase_db import save_appointment

load_dotenv()

app = Flask(__name__)

# Track processed recordings to avoid duplicates
processed_recordings = set()

# ── ROOT ─────────────────────────────────────────────────────

@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "status": "running",
        "service": "Appointment CRM Pipeline",
        "endpoints": {
            "health": "/health",
            "exotel_webhook": "/webhook/call",
            "twilio_answer": "/webhook/twilio/answer",
            "twilio_recording": "/webhook/twilio/recording",
            "whatsapp_webhook": "/webhook/whatsapp"
        }
    }), 200


# ── HEALTH CHECK ─────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "running"}), 200


# ── EXOTEL WEBHOOK ───────────────────────────────────────────

@app.route("/webhook/call", methods=["POST"])
def handle_call():
    print("\n📞 Incoming call webhook from Exotel...")

    recording_url = request.form.get("RecordingUrl")
    caller_number = request.form.get("CallFrom")
    call_duration = request.form.get("Duration")
    call_status = request.form.get("Status")
    call_sid = request.form.get("CallSid")

    print(f"Call SID: {call_sid}")
    print(f"Caller: {caller_number}")
    print(f"Duration: {call_duration} seconds")
    print(f"Status: {call_status}")

    if not recording_url:
        print("No recording URL, skipping...")
        return jsonify({"status": "ignored", "reason": "no recording"}), 200

    if int(call_duration or 0) < 10:
        print("Call too short, skipping...")
        return jsonify({"status": "ignored", "reason": "call too short"}), 200

    audio_path = download_audio(
        recording_url,
        auth=(os.getenv("EXOTEL_API_KEY"), os.getenv("EXOTEL_API_TOKEN"))
    )
    return process_audio(audio_path, caller_phone=caller_number)


# ── TWILIO WEBHOOKS ──────────────────────────────────────────

@app.route("/webhook/twilio/answer", methods=["POST"])
def handle_twilio_answer():
    """Twilio calls this when a call comes in"""
    from twilio.twiml.voice_response import VoiceResponse

    print("\n📞 Incoming call from Twilio...")
    caller = request.form.get("From")
    print(f"Caller: {caller}")

    response = VoiceResponse()
    response.say(
        "Thank you for calling. "
        "Please leave your appointment details after the beep. "
        "Press hash when done.",
        voice="alice"
    )
    response.record(
        action="/webhook/twilio/recording",
        method="POST",
        max_length=120,
        finish_on_key="#",
        transcribe=False,
        play_beep=True
    )

    return str(response), 200, {"Content-Type": "text/xml"}


@app.route("/webhook/twilio/recording", methods=["POST"])
def handle_twilio_recording():
    """Twilio calls this when recording is complete"""
    print("\n🎙️ Recording complete from Twilio...")

    recording_sid = request.form.get("RecordingSid")
    recording_url = request.form.get("RecordingUrl")
    caller = request.form.get("From")
    recording_duration = request.form.get("RecordingDuration")

    # Prevent duplicate processing
    if recording_sid in processed_recordings:
        print(f"Already processed {recording_sid}, skipping...")
        return "", 200
    processed_recordings.add(recording_sid)

    print(f"Caller: {caller}")
    print(f"Recording duration: {recording_duration} seconds")
    print(f"Recording URL: {recording_url}")

    if not recording_url:
        print("No recording URL, skipping...")
        return "", 200

    if int(recording_duration or 0) < 5:
        print("Recording too short, skipping...")
        return "", 200

    # Twilio recording URL needs .mp3 extension
    recording_url = recording_url + ".mp3"

    audio_path = download_audio(
        recording_url,
        auth=(
            os.getenv("TWILIO_ACCOUNT_SID"),
            os.getenv("TWILIO_AUTH_TOKEN")
        )
    )

    return process_audio(audio_path, caller_phone=caller)


# ── WHATSAPP WEBHOOK ─────────────────────────────────────────

@app.route("/webhook/whatsapp", methods=["GET", "POST"])
def handle_whatsapp():

    if request.method == "GET":
        verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN")
        challenge = request.args.get("hub.challenge")
        token = request.args.get("hub.verify_token")

        if token == verify_token:
            return challenge, 200
        return jsonify({"error": "Verification failed"}), 403

    print("\n💬 Incoming WhatsApp message...")
    data = request.json

    try:
        msg_type = data.get("type")
        if msg_type != "message_received":
            return jsonify({"status": "ignored"}), 200

        customer = data.get("data", {}).get("customer", {})
        message = data.get("data", {}).get("message", {})

        if message.get("message_type") != "text":
            print("Non-text message, skipping...")
            return jsonify({"status": "ignored"}), 200

        text = message.get("message_content", {}).get("text", "")
        sender_phone = customer.get("channel_phone_number", "")
        sender_name = customer.get("traits", {}).get("name", None)

        print(f"From: {sender_phone}")
        print(f"Message: {text}")

        appointment = extract_appointment(text)
        appointment["phone"] = sender_phone

        if not appointment.get("customer_name") and sender_name:
            appointment["customer_name"] = sender_name

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

    if response.status_code != 200:
        raise Exception(f"Failed to download audio: {response.status_code}")

    audio_path = "temp_call.mp3"
    with open(audio_path, "wb") as f:
        f.write(response.content)
    print("Audio downloaded!")
    return audio_path


def process_audio(audio_path, caller_phone=None):
    try:
        transcript = transcribe_audio(audio_path)
        appointment = extract_appointment(transcript)

        if caller_phone and not appointment.get("phone"):
            appointment["phone"] = caller_phone

        result = save_appointment(appointment)
        print(f"✅ Success — Customer: {result['customer']['name']}")
        return jsonify({"status": "success"}), 200

    except Exception as e:
        print(f"❌ Pipeline error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# ── TEST ROUTE ───────────────────────────────────────────────

@app.route("/test/call", methods=["GET"])
def test_call():
    """Test pipeline with local audio file"""
    return process_audio("test_call.m4a")


# ── START SERVER ─────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8120
    app.run(port=port, debug=True)
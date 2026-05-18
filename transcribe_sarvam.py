import os
from sarvamai import SarvamAI
from dotenv import load_dotenv

load_dotenv()

client = SarvamAI(api_subscription_key=os.getenv("SARVAM_API_KEY"))

def transcribe_audio_indian(file_path):
    print("🇮🇳 Transcribing with Sarvam AI...")

    # Convert m4a to wav if needed
    if file_path.endswith(".m4a"):
        file_path = convert_to_wav(file_path)

    with open(file_path, "rb") as audio_file:
        response = client.speech_to_text.transcribe(
            file=audio_file,
            model="saaras:v3",
            language_code="unknown",
            mode="codemix"
        )

    transcript = response.transcript
    print(f"🌐 Detected language: {response.language_code}")
    print(f"📝 Transcript: {transcript}")
    return transcript

def convert_to_wav(m4a_path):
    import subprocess
    wav_path = m4a_path.replace(".m4a", ".wav")
    print(f"Converting {m4a_path} to wav...")
    subprocess.run([
        "ffmpeg", "-i", m4a_path,
        "-ar", "16000",   # 16kHz sample rate
        "-ac", "1",       # mono
        "-y",             # overwrite if exists
        wav_path
    ], capture_output=True)
    print(f"Converted to {wav_path}")
    return wav_path
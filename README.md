# 📞 Appointment CRM — AI-Powered Service Business Automation

An end-to-end AI system that **automatically captures customer appointments from phone calls and WhatsApp messages**, transcribes them using speech-to-text models, extracts structured booking data using LLMs, and stores everything in a relational database — with a dashboard for search, analytics, and reporting.

Supports **multilingual conversations** (Hindi, Marathi, English, and code-mixed Hinglish) using India-focused speech models.

---

## 🧠 The Problem

Small service businesses (cleaning, home repair, salon, clinic) manage appointments through phone calls and WhatsApp — often losing customer data, double-booking, or forgetting follow-ups because everything lives in the owner's memory or scattered chat threads.

**This system eliminates manual data entry entirely.** Every customer interaction is automatically captured, structured, and stored.

---

## 🎯 How It Works

```
📞 Customer calls              💬 Customer sends
   business number                WhatsApp message
        │                              │
        ▼                              ▼
   Phone provider               WhatsApp Business
   (Twilio / Exotel /              API (Interakt)
    MyOperator)                        │
        │                              │
        └──────────────┬───────────────┘
                       ▼
                Flask webhook
                server (Render)
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
    AI Transcription           (already text)
    Whisper / Sarvam AI              │
          │                          │
          └────────────┬─────────────┘
                       ▼
              GPT-4o Mini extracts
              structured JSON:
              {name, phone, date,
               time, service, source}
                       │
                       ▼
                Supabase (PostgreSQL)
                ┌──────┴──────┐
                ▼             ▼
           Customers      Services
                       │
                       ▼
              Streamlit Dashboard
              search, reports, maps
```

---

## ✨ Key Features

### AI Pipeline
- **Dual speech-to-text**: OpenAI Whisper (English) + Sarvam AI (Hindi, Marathi, Hinglish)
- **Smart language detection**: auto-detects language — no manual configuration needed
- **Structured extraction**: GPT-4o Mini pulls customer name, phone, date, time, service type, and ad source from free-form conversations
- **Code-mixing support**: handles natural switches like *"Mujhe kal 3 baje appointment book karni hai for sofa cleaning"*

### Customer Management
- **Automatic deduplication**: matches returning customers by phone number
- **Name conflict handling**: detects when a different person calls from the same number
- **Multi-phone support**: stores primary + additional phone numbers per customer
- **Data quality flags**: `has_issues` and `issue_notes` fields track suspicious entries

### Dashboard (Streamlit)
- **Customer search**: by name, phone, or both — with full service history
- **Revenue reports**: over time (day/week/month), by service type, by revenue range
- **Geographic analysis**: revenue by neighborhood with interactive map (OpenStreetMap)
- **Top clients**: by month and custom date range
- **Data export**: download filtered data as CSV
- **Password protected**: simple auth for business owner access
- **Mobile-friendly**: navigation cards that work on phone screens

### Integrations
- **Phone**: Twilio (global), Exotel (India), MyOperator (India) — webhook handlers for all three
- **WhatsApp**: Interakt BSP with standard Meta webhook format
- **Duplicate prevention**: tracks processed recording IDs to prevent double-processing

---

## 🏗️ Tech Stack

| Component | Technology | Why |
|---|---|---|
| Speech-to-text (English) | OpenAI Whisper | Best accuracy, simple API |
| Speech-to-text (Indian) | Sarvam AI `saaras:v3` | Purpose-built for Hindi/Marathi code-mixing |
| LLM extraction | GPT-4o Mini | Cost-effective structured JSON output |
| Phone recording | Twilio / Exotel / MyOperator | Multi-provider webhook support |
| WhatsApp | Interakt (WhatsApp BSP) | India-focused, easy setup |
| Web framework | Flask + Gunicorn | Lightweight webhook server |
| Hosting | Render | Free tier, GitHub auto-deploy |
| Database | Supabase (PostgreSQL) | Relational with API, free tier, built-in UI |
| Dashboard | Streamlit + Plotly | Rapid development, interactive charts |
| Dashboard hosting | Streamlit Cloud | Free, GitHub auto-deploy |

---

## 📁 Project Structure

```
appointment-crm/
│
├── pipeline.py              # Core: audio → transcript → structured data
├── server.py                # Flask webhook server (all providers)
├── supabase_db.py           # Database CRUD operations
├── transcribe_sarvam.py     # Sarvam AI integration (Indian languages)
├── zoho_auth_manager.py     # Legacy Zoho OAuth (kept for reference)
├── migrate.py               # Data migration: Excel → Supabase
├── requirements.txt         # Flask server dependencies
├── Procfile                 # Render deployment config
├── .python-version          # Python 3.11
│
└── dashboard/
    ├── app.py               # Home page + password auth + navigation
    ├── database.py          # All Supabase queries for dashboard
    ├── requirements.txt     # Streamlit dependencies
    └── pages/
        ├── 1_Search.py      # Customer search + service history
        ├── 2_Reports.py     # Analytics: charts, top clients, area map
        ├── 3_Add_Customer.py # Add customer form (+ optional first service)
        └── 4_Add_Service.py  # Add service to existing customer
```

---

## 🚀 Setup

### 1. Clone and Install

```bash
git clone https://github.com/ninadparab/appointment-crm.git
cd appointment-crm

python -m venv venv
source venv/Scripts/activate   # Windows
# or: source venv/bin/activate # macOS/Linux

pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` in the project root:

```env
# AI Services
OPENAI_API_KEY=your_key
SARVAM_API_KEY=your_key
USE_INDIAN_LANGUAGES=true   # false for English-only mode

# Database
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your_service_role_key

# Phone Provider (pick one)
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
# EXOTEL_API_KEY=your_key
# EXOTEL_API_TOKEN=your_token
# MYOPERATOR_API_TOKEN=your_token

# WhatsApp
WHATSAPP_VERIFY_TOKEN=any_random_string
INTERAKT_SECRET_KEY=your_key
```

### 3. Set Up Database

Run in Supabase SQL Editor


### 4. Run Locally

```bash
# Flask server
python server.py

# Dashboard (separate terminal)
cd dashboard
streamlit run app.py
```

### 5. Deploy

**Render** (Flask server): connect GitHub repo, add env vars, auto-deploys on push.

**Streamlit Cloud** (Dashboard): connect repo, set main file to `dashboard/app.py`, add secrets.

---

## 📡 Webhook Endpoints

| Endpoint | Method | Provider |
|---|---|---|
| `/health` | GET | Monitoring |
| `/webhook/twilio/answer` | POST | Twilio — returns TwiML to record call |
| `/webhook/twilio/recording` | POST | Twilio — processes completed recording |
| `/webhook/call` | POST | Exotel — call recording callback |
| `/webhook/myoperator` | POST | MyOperator — call summary event |
| `/webhook/whatsapp` | GET/POST | Interakt — WhatsApp message webhook |

---

## 🧩 Adapting for Your Business

This system is designed for any appointment-driven service business. To adapt:

1. **Service types**: update the `categorize_service()` function in the conversion script with your own categories (e.g. salon services, clinic appointments, tutoring sessions)
2. **Area coordinates**: update the `MUMBAI_AREAS` dict in reports with your city's neighborhoods
3. **Revenue buckets**: adjust the `make_bucket()` ranges to match your pricing
4. **Phone provider**: pick whichever provider serves your country — the webhook handlers are modular
5. **Languages**: toggle `USE_INDIAN_LANGUAGES` or add new Sarvam language codes

---

## 💡 Design Decisions

| Decision | Rationale |
|---|---|
| Supabase over Zoho CRM | Simple API key auth vs complex OAuth, proper relational model, free tier |
| Sarvam AI over Whisper for Indian languages | Purpose-built for Hindi/Marathi code-mixing, `codemix` mode handles natural conversations |
| Flask over FastAPI | Lighter, sufficient for webhook handling, simpler deployment |
| Streamlit over React | Faster development in Python, good enough for internal dashboard, free hosting |
| Canonical service types | 5,000+ free-text variations consolidated into ~30 canonical categories for meaningful reports |
| `has_issues` flag | Instead of dropping bad data, flag it for human review — preserves data integrity |
| Multi-provider webhook support | Business can switch phone providers without code changes |

---

## 📊 Data Pipeline Details

### Phone Call Flow
```
Incoming call → Provider records → Webhook fires
→ Download audio → Sarvam/Whisper STT → GPT extraction
→ Customer lookup by phone → Create/update customer
→ Create service record → Done
```

### WhatsApp Flow
```
Incoming message → Webhook fires
→ GPT extraction directly from text (no STT needed)
→ Customer lookup → Create/update → Done
```

### Data Quality Pipeline
```
Raw Excel data → Parse amounts (handles "5@400=2000" patterns)
→ Parse phones (handles "9821071497/ 9820053235")
→ Categorize services (free text → canonical types)
→ Flag issues (huge amounts, math mismatches, bad dates)
→ Deduplicate customers → Normalize → Upload to Supabase
```

---

## 🛠️ Built With

Built collaboratively with **Claude** (Anthropic) — from architecture design through implementation, debugging, deployment, and data migration.

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 👤 Author

**Ninad Parab** — [GitHub](https://github.com/ninadparab)

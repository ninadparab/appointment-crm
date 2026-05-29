# Appointment CRM — AI-Powered Field Service System

An end-to-end CRM system that captures customer appointments from **phone calls** and **WhatsApp messages** using AI, supports **Hindi, Marathi, and English (Hinglish)**, and stores everything in a structured database with a searchable dashboard.

Built for a Mumbai-based cleaning/field service business but adaptable to any appointment-driven business.

---

## 🎯 What It Does

```
📞 Customer calls         💬 Customer messages
   business number           on WhatsApp
        │                          │
        ▼                          ▼
   Phone provider           WhatsApp Business
   (Twilio/Exotel/             API (Interakt)
    MyOperator)                    │
        │                          │
        └────────────┬─────────────┘
                     ▼
              Flask webhook
              server on Render
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
  AI Transcription          (text already)
  (Whisper / Sarvam AI)            │
        │                          │
        └────────────┬─────────────┘
                     ▼
            GPT-4o Mini extracts
            structured appointment
                     │
                     ▼
              Supabase database
                     │
                     ▼
         Streamlit dashboard for
         search and reports
```

---

## ✨ Features

- **📞 Phone call automation** — records calls, transcribes, extracts customer name, date, time, service requested
- **💬 WhatsApp integration** — auto-processes text messages into appointment records
- **🇮🇳 Indian language support** — Hindi, Marathi, English, and mixed (Hinglish) via Sarvam AI
- **🤖 Smart customer matching** — recognizes returning customers by phone, prevents duplicates
- **📊 Streamlit dashboard** — search customers, view service history, reports with charts and Mumbai area map
- **🗺️ Geographic visualization** — revenue by Mumbai neighborhood with interactive map
- **🛡️ Data quality tracking** — flags suspicious entries (huge amounts, math errors) for review
- **🔐 Password protected** — dashboard secured behind auth
- **☁️ Always on** — Flask server runs 24/7 on Render, dashboard on Streamlit Cloud

---

## 🏗️ Architecture

| Layer | Technology |
|---|---|
| **Speech-to-text (English)** | OpenAI Whisper |
| **Speech-to-text (Indian languages)** | Sarvam AI (`saaras:v3` with `codemix` mode) |
| **LLM extraction** | OpenAI GPT-4o Mini |
| **Phone (testing)** | Twilio |
| **Phone (production)** | Exotel / MyOperator |
| **WhatsApp** | Interakt (BSP for WhatsApp Business API) |
| **Web framework** | Flask + Gunicorn |
| **Web server hosting** | Render |
| **Database** | Supabase (PostgreSQL) |
| **Dashboard** | Streamlit + Plotly |
| **Dashboard hosting** | Streamlit Cloud |

---

## 📁 Project Structure

```
appointment-crm/
│
├── pipeline.py              # AI pipeline: audio → transcript → structured data
├── server.py                # Flask webhook server (Twilio, Exotel, MyOperator, WhatsApp)
├── supabase_db.py           # Database functions (find/create customer, save service)
├── transcribe_sarvam.py     # Sarvam AI integration for Indian languages
├── migrate.py               # Initial data migration from Excel
├── requirements.txt         # Python dependencies (Flask server)
├── Procfile                 # Render deployment config
├── .python-version          # Pins Python 3.11
├── .env                     # API keys (not in Git)
│
└── dashboard/
    ├── app.py               # Home page with navigation
    ├── database.py          # Supabase queries for dashboard
    ├── requirements.txt     # Streamlit dependencies
    ├── .streamlit/
    │   └── secrets.toml     # Password (not in Git)
    └── pages/
        ├── 1_Search.py      # Customer search + service history
        ├── 2_Reports.py     # Revenue charts, top clients, area map
        ├── 3_Add_Customer.py # Manual customer + optional service form
        └── 4_Add_Service.py  # Add service to existing customer
```

---

## 🗄️ Database Schema

```
customers
├── id, name, phone, additional_phones
├── email, address, area, category
├── lead_source, comments, created_at

service_types (canonical)
├── id, canonical_name
├── main_category (e.g. "Flat")
├── sub_category (e.g. "2BHK")

services
├── id, customer_id → customers
├── service_type_id → service_types
├── main_category, sub_category
├── date_of_service, nature_of_service
├── quantity, rate_per_unit, total_amount
├── has_issues, issue_notes, amount_in_comments
├── category, comments
```

---

## 🚀 Setup Guide

### Prerequisites

- Python 3.11
- Git
- A Supabase account (free tier works)
- OpenAI API key with billing
- Sarvam AI API key (for Indian language support)
- Phone provider account (Twilio for testing, MyOperator/Exotel for India)
- Interakt account (for WhatsApp)

### Environment Variables

Create `.env` in the project root:

```env
# OpenAI
OPENAI_API_KEY=sk-...

# Sarvam AI (for Hindi/Marathi)
SARVAM_API_KEY=sk_...
USE_INDIAN_LANGUAGES=true

# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJ...   # service_role key

# Twilio (for testing)
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1...

# Exotel (optional)
EXOTEL_API_KEY=...
EXOTEL_API_TOKEN=...

# MyOperator (optional)
MYOPERATOR_API_TOKEN=...

# WhatsApp (Interakt)
INTERAKT_SECRET_KEY=...
WHATSAPP_VERIFY_TOKEN=any_random_string
```

### Local Development

```bash
# Clone the repo
git clone https://github.com/ninadparab/appointment-crm.git
cd appointment-crm

# Create virtual environment
python -m venv venv
source venv/Scripts/activate   # Windows Git Bash
# or: source venv/bin/activate # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Run the Flask server locally
python server.py

# Run the dashboard locally (in another terminal)
cd dashboard
streamlit run app.py
```

### Deploying

**Flask Server → Render:**
- Connect your GitHub repo to Render
- Add all environment variables in Render settings
- Deploys automatically on git push

**Dashboard → Streamlit Cloud:**
- Connect repo at share.streamlit.io
- Set main file path to `dashboard/app.py`
- Add `SUPABASE_URL`, `SUPABASE_KEY`, `PASSWORD` to secrets

---

## 📡 Webhook Endpoints

After deployment your Flask server exposes:

| Endpoint | Purpose | Used By |
|---|---|---|
| `GET  /` | Service info | Health checks |
| `GET  /health` | Health check | Monitoring |
| `POST /webhook/twilio/answer` | Twilio call flow control | Twilio |
| `POST /webhook/twilio/recording` | Process Twilio recording | Twilio |
| `POST /webhook/call` | Exotel call recording | Exotel |
| `POST /webhook/myoperator` | MyOperator call recording | MyOperator |
| `POST /webhook/whatsapp` | WhatsApp message events | Interakt |

---
## 🧪 Tested With

- ✅ English phone calls via Twilio
- ✅ Hindi phone calls via Sarvam AI transcription
- ✅ Marathi phone calls via Sarvam AI transcription
- ✅ Mixed Hindi + English (Hinglish) — perfectly transcribed and categorized
- ✅ Customer lookup by phone (existing vs new)
- ✅ Webhook deduplication (prevents double-processing)
- ✅ 16,541 historical services migrated successfully

---

## 🛠️ Built With AI Assistance

This project was built collaboratively with **Claude** (Anthropic) over multiple sessions — from initial architecture discussions through full implementation, debugging, deployment, and data migration of 10,000+ customers and 16,000+ services.

---

## 📄 License

Private project. Not licensed for public use without permission.

---

## 🙋‍♂️ Author

[Ninad Parab](https://github.com/ninadparab)

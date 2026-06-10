# NyayaSetu + ZamanatAI

WhatsApp message -> bail application + surety bond in 60 seconds.
22 Indian languages. Zero cost to families.

## Live demo
[https://nyayasetu-zamanatai.vercel.app](https://nyayasetu-zamanatai.vercel.app)

## Demo video
[your YouTube link - add after recording]

## Setup (one command)
pip install -r requirements.txt && cp .env.example .env && uvicorn main:app

## Architecture
```text
Citizen on WhatsApp/Web
        |
        v
FastAPI Intake Layer
Twilio webhook, language detection, OCR upload, WebSocket live events
        |
        v
AI Understanding Layer
Groq NLU first, rule-based fallback, IndicTrans2 translation fallback
        |
        v
Justice Workflow Layer
Intent classification, bail eligibility, evidence checklist, surety flow
        |
        v
Document Generation Layer
Bail application PDF, surety bond PDF, static public download links
        |
        v
Adaptive Data + Demo Layer
JSONL interaction logging, Hugging Face dataset, Next.js live dashboard
```

## Adaptive Data dataset
[https://huggingface.co/datasets/Ananya80/nyayasetu-legal-dialogues-multilingual](https://huggingface.co/datasets/Ananya80/nyayasetu-legal-dialogues-multilingual)

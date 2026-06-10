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

## Adaption integration
NyayaSetu uses Adaption Adaptive Data as the submission dataset layer. Real Twilio WhatsApp interactions are logged into JSONL, then transformed into an adaptive legal-access dataset with feedback events, correction events, adaptation history, and confidence-before/after metrics.

Adaption dataset name:
```text
nyayasetu-legal-dialogues-multilingual
```

Adaption upload file:
```text
adaptive_data/adaptive_dataset.csv
```

The dataset is designed for the Adaption Adaptive Data Track and demonstrates dynamic multilingual legal data ingestion, adaptation, evaluation-ready metadata, and export for AI agents and fine-tuning pipelines.

## Open datasets
Hugging Face:
[https://huggingface.co/datasets/Ananya80/nyayasetu-legal-dialogues-multilingual](https://huggingface.co/datasets/Ananya80/nyayasetu-legal-dialogues-multilingual)

Kaggle:
[add Kaggle dataset URL after upload]

## Adaptive learning loop
```text
WhatsApp/Web legal query
        |
        v
Language + intent + entity prediction
        |
        v
User/reviewer feedback
        |
        v
Field-level correction event
        |
        v
Versioned adaptation history
        |
        v
Confidence_before -> confidence_after
        |
        v
Model-ready adaptive dataset export
```

Current adaptive release:
- 1,544 records
- 1,544 feedback events
- 235 correction events
- 11 Indian languages plus English/global civic legal queries
- Low-resource coverage for Odia, Assamese, and Konkani

Credit: Built for the Adaption Labs Adaptive Data Track.

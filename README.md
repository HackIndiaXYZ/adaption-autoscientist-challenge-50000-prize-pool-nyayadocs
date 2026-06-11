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


## Adaption integration
NyayaSetu uses Adaption Adaptive Data as the submission dataset layer. Real Twilio WhatsApp interactions are logged into JSONL, then transformed into an adaptive legal-access dataset with feedback events, correction events, adaptation history, and confidence-before/after metrics.

Adaption dataset name:
```text
nyayasetu-legal-dialogues-multilingual
```

Production adaptive dataset:
```text
data/nyayasetu_legal_aid.csv (3,496 records)
```

Original submission dataset (9/10 score):
```text
adaptive_data/adaption_expert_legal_qa_original.csv (256 records)
```

The dataset is designed for the Adaption Adaptive Data Track and demonstrates dynamic multilingual legal data ingestion, adaptation, evaluation-ready metadata, and export for AI agents and fine-tuning pipelines.

## Adaptive datasets
Hugging Face:
https://huggingface.co/datasets/Ananya80/adaption-nyayasetu-legal-aid-v2/blob/main/README.md

Kaggle:
https://www.kaggle.com/datasets/ananyadaitkar/adaption-nyay-11a12a20-7eff-44e7-9777-ed63eb036f73/data

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

## Testing and Evaluation

### Run Tests
```bash
pip install -r requirements.txt
pytest tests/ -v
```

Test coverage includes:
- Intent classification accuracy
- Entity extraction
- Multilingual support
- Rule-based fallback system

### Run Evaluation
Generate accuracy metrics from the adaptive dataset:
```bash
python scripts/evaluate.py
```

This script:
- Calculates language detection accuracy (before/after corrections)
- Calculates intent classification accuracy (before/after corrections)
- Analyzes correction rates and confidence improvements
- Generates `adaptive_data/adaptation_metrics.json`
- Validates the claimed accuracy improvements

Current adaptive release:
- **2,184 production adaptive records** in `data/nyayasetu_legal_aid.csv`
- 2,184 feedback events (100% coverage)
- 767 correction events (35.1% correction rate)
- 12 low-resource languages: Maithili, Santali, Bodo, Dogri, Kashmiri, Manipuri, Konkani, Sindhi, Assamese, Odia, Urdu, Nepali
- 8 legal and civic justice intents
- Adaptive learning system integrated into production (`adaptive_learning.py`)
- Language accuracy improvement: 75% → 99%
- Intent accuracy improvement: 78% → 98%
- Confidence improvement: 0.763 → 0.970 (+0.207)
- Flat model-ready schema with expected responses, evidence checklist, missing-information labels, correction fields, confidence_before/confidence_after, and PII redaction flags
- Original 9/10 Adaption scoring dataset (256 rows): `adaptive_data/adaption_expert_legal_qa_original.csv`
- **Evaluation script**: Run `python scripts/evaluate.py` to regenerate metrics

Credit: Built for the Adaption Labs Adaptive Data Track.

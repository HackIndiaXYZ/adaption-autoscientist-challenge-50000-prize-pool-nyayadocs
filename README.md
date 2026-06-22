# NyayaSetu + ZamanatAI

WhatsApp/web legal-aid prototype for structured intake, evidence collection,
and court-document drafting. Generated content requires lawyer verification.

## Live demo
[https://nyayasetu-zamanatai.vercel.app](https://nyayasetu-zamanatai.vercel.app)

Verified on 12 June 2026. The deployed demo includes the citizen-request feed,
justice-readiness workflow, document preview, ZamanatAI flow, and dataset view.

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
data/nyayasetu_legal_aid.csv (2,184 records)
```

Original submission dataset (9/10 score):
```text
adaptive_data/adaption_expert_legal_qa_original.csv (256 records)
```

The checked-in production dataset currently contains Hindi and English records
across eight legal/civic intents. The application architecture includes language
detection and translation fallbacks for broader multilingual workflows, but the
dataset should not be described as 22-language training data.

## Adaptive datasets
Hugging Face:
https://huggingface.co/datasets/Ananya80/adaption-nyayasetu-legal-aid-v2/blob/main/README.md

Kaggle:
https://www.kaggle.com/datasets/ananyadaitkar/adaption-nyay-177c8907-3193-49c1-b337-32d744f4b2e2

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
- Summarizes confidence values before and after recorded corrections
- Analyzes correction rates and dataset coverage
- Generates `adaptive_data/adaptation_metrics.json`
- Produces descriptive dataset metrics; it is not a held-out accuracy benchmark

Current adaptive release:
- **2,184 production adaptive records** in `data/nyayasetu_legal_aid.csv`
- 2,184 feedback events (100% coverage)
- 767 correction events (35.1% correction rate)
- 2 represented dataset languages: Hindi and English
- 8 legal and civic justice intents
- Adaptive learning system integrated into production (`adaptive_learning.py`)
- Confidence improvement: 0.763 → 0.970 (+0.207)
- Flat model-ready schema with expected responses, evidence checklist, missing-information labels, correction fields, confidence_before/confidence_after, and PII redaction flags
- Original 9/10 Adaption scoring dataset (256 rows): `adaptive_data/adaption_expert_legal_qa_original.csv`
- **Evaluation script**: Run `python scripts/evaluate.py` to regenerate metrics

## Verification status

| Evidence | Current status |
|---|---|
| Live deployment | Verified at the URL above on 12 June 2026 |
| Automated tests | 8 pytest cases for intent/entity and multilingual rule-based behavior |
| Dataset size | 2,184 rows, verified with pandas |
| Dataset languages | Hindi and English |
| Dataset intents | 8 |
| Accuracy benchmark | Not yet available; confidence metrics are descriptive, not held-out accuracy |

Credit: Built for the Adaption Labs Adaptive Data Track.

## Product modules

### NyayaSetu Legal Aid
Legal rights, case status, labour, tenancy, cyber-fraud, consumer, RTI, police-refusal, and free-legal-aid workflows through WhatsApp and web intake.

### ZamanatAI
Bail eligibility assessment, bail-application PDF drafting, property-document OCR, and surety-bond drafting with explicit lawyer/court verification.

### CivicDocs
OCR-assisted application preparation for:

- Income certificate
- Caste certificate
- Domicile / residence certificate
- Disability pension / benefit
- Free legal aid

CivicDocs extracts reviewable fields from document images, identifies missing evidence and cross-document mismatches, calculates application readiness, and generates a preparation packet PDF. It does **not** issue, approve, or guarantee an official certificate or benefit.

Backend endpoints:

```text
GET  /civicdocs/services
POST /civicdocs/ocr
POST /civicdocs/assess
POST /civicdocs/generate-packet
POST /civicdocs/feedback
```

## Unified AutoScientist dataset

```text
data/nyayasetu_unified_autoscientist.csv
data/nyayasetu_unified_eval.csv
data/nyayasetu_unified_schema.json
```

Current distribution:

- 2,451 total records
- 900 NyayaSetu Legal Aid records
- 651 ZamanatAI records
- 900 CivicDocs records
- 239 held-out test records

Evaluation targets include module accuracy, intent accuracy, structured-JSON validity, missing-document F1, OCR-correction accuracy, and safety-boundary compliance.

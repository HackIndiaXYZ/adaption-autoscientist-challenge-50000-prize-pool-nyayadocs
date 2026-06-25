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
https://huggingface.co/datasets/Ananya80/nyayasetu-legal-dialogues-multilingual

Kaggle:
https://www.kaggle.com/datasets/ananyadaitkar/adaption-nyay-177c8907-3193-49c1-b337-32d744f4b2e2

## AutoScientist trained model

Model card and training config:

```text
model/adaption_nyayasetu_legal_assist/README.md
model/adaption_nyayasetu_legal_assist/training_config.json
upload_model.py
```

AutoScientist run:

- Base model: `meta-llama/Llama-4-Scout-17B-16E-Instruct`
- Trained model: `adaption_nyayasetu_legal_assist`
- Fine-tune job ID: `8ec11627-6dd4-48ee-b4d9-0fe83c25bd8e`
- Training experiment ID: `f120ba55-a11a-4621-89a8-12e924e7766f`
- Method: SFT LoRA

Measured Adaption platform improvements:

- Quality: `9.0 -> 9.4`
- Grade: `B -> A`
- Percentile: `41.4 -> 57.7`
- Dataset win rate: `31 -> 69`
- Legal-category win rate: `35 -> 66`

Evidence screenshots:

```text
submission_evidence/adaption/quality_grade_percentile.png
submission_evidence/adaption/autoscientist_winrates.png
submission_evidence/adaption/train_eval_metrics.png
```

Model weights release status: the public model card/config are checked in. Exported LoRA adapter weights from Adaption must be placed in `model/adaption_nyayasetu_legal_assist/` and uploaded with `python3 upload_model.py` before claiming complete public model-weight release.

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
- **2,573 unified AutoScientist records** in `data/nyayasetu_unified_autoscientist.csv`
- 122 live Twilio webhook observations from the deployed WhatsApp pipeline
- 77 Twilio field observations promoted by automated audit for adaptive training
- 3 modules: NyayaSetu Legal Aid, ZamanatAI, CivicDocs
- 15+ legal/civic workflow intents across legal aid, bail/surety, and civic-document preparation
- Missing-document labels, evidence checklists, safety boundaries, expected JSON, OCR correction tasks, and benchmark artifacts
- Original expert Adaption scoring dataset: `adaptive_data/adaption_expert_legal_qa_original.csv`
- **Evaluation script**: Run `python scripts/evaluate.py` to regenerate descriptive adaptive metrics

## Verification status

| Evidence | Current status |
|---|---|
| Live deployment | Verified at the URL above |
| Automated tests | 17 pytest cases |
| Unified dataset size | 2,573 rows |
| Live field data | 122 matched Twilio webhook observations |
| AutoScientist training | Completed SFT LoRA run |
| Adaption improvement | Win rate 31 -> 69; legal win rate 35 -> 66 |
| Model release | Model card/config checked in; exported adapter weights still need public upload |

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

- 2,573 total records
- 973 NyayaSetu Legal Aid records
- 670 ZamanatAI records
- 930 CivicDocs records
- 122 live Twilio webhook observations from the deployed WhatsApp pipeline
- 239 held-out test records

Evaluation targets include module accuracy, intent accuracy, structured-JSON validity, missing-document F1, OCR-correction accuracy, and safety-boundary compliance.

## AutoScientist model objective and benchmark

Model contract:

```text
model/nyayasetu_model_contract.json
model/README.md
```

Locked benchmark and evaluation tooling:

```text
data/nyayasetu_benchmark_v1.csv
data/nyayasetu_benchmark_report.json
scripts/run_rule_baseline.py
scripts/evaluate_unified_predictions.py
evaluation/baseline_metrics.json
docs/autoscientist_runbook.md
```

Current fixed rule baseline on the 180-row balanced benchmark:

- Module accuracy: 91.11%
- Module macro-F1: 91.07%
- Intent accuracy: 72.78%
- Intent macro-F1: 64.19%
- Missing-document macro-F1: 3.33%
- Structured JSON validity: 100%
- Safety-boundary compliance: 100%

Benchmark labels remain provisional until two independent reviewers complete `data/reviewer_assignments.csv`. Do not claim final benchmark performance before human consensus.

Human-review packets are in `review/`. Complete the CSVs there, then run `scripts/apply_human_reviews.py` and `scripts/calculate_reviewer_agreement.py` before claiming reviewer agreement or training promotion.

## Human data collection

The `collection/` folder contains:

- 150 scripted Twilio collection prompts
- 122 matched Twilio export rows in `data/field_collection_clean.csv`
- 100 OCR correction tasks
- 50 document-mismatch cases
- 100 native-script review tasks
- 50 adversarial queries
- 50 safety/refusal cases

Scripted Twilio rows must retain provenance `field_collected_scripted`. Independently written consenting-user rows may be labeled `real_user_redacted` only after PII redaction and review.

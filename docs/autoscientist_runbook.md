# AutoScientist Runbook For NyayaSetu

This runbook records the exact Adaptive Data / AutoScientist evidence needed for a high-scoring submission. Do not claim a final adapted-model improvement until these steps are completed in the Adaption platform.

## 1. Upload Dataset To Adaption

Use the Adaption dashboard and upload:

```text
data/nyayasetu_unified_autoscientist.csv
```

Dataset name:

```text
nyayasetu_unified_legal_aid_zamanatai_civicdocs
```

Description:

```text
Multilingual adaptive legal-access dataset for NyayaSetu Legal Aid, ZamanatAI bail/surety workflows, and CivicDocs OCR-assisted public-service application preparation. Includes live Twilio field observations, safety boundaries, missing-document labels, OCR correction tasks, and benchmark/evaluation artifacts. Built for the Adaption Labs Adaptive Data Track.
```

## 2. Diagnosis Evidence

Capture screenshots for:

- dataset size and columns;
- language distribution;
- module/intent distribution;
- quality score;
- detected weaknesses;
- any recommended recipe from AutoScientist.

Save screenshots under:

```text
submission_evidence/adaption/
```

## 3. Adaptation Recipe

Use these target tasks:

- module classification: `legal_aid`, `zamanatai`, `civicdocs`;
- intent classification over `data/label_definitions.json`;
- missing-document detection;
- structured JSON generation;
- safety-boundary compliance.

Exclude locked benchmark rows:

```text
data/nyayasetu_benchmark_v1.csv
```

## 4. Baseline

Current local rule baseline:

```text
evaluation/baseline_metrics.json
```

Required numbers to beat:

- module accuracy: 91.11%;
- intent accuracy: 72.78%;
- missing-document macro-F1: 3.33%;
- structured JSON validity: 100%;
- safety-boundary compliance: 100%.

## 5. Export Adapted Model Predictions

After AutoScientist adaptation, export predictions on:

```text
data/nyayasetu_benchmark_v1.csv
```

Save as:

```text
evaluation/autoscientist_predictions.csv
```

Required columns:

```text
benchmark_id,predicted_module,predicted_intent,predicted_missing_documents,predicted_json
```

Then run:

```bash
python3 scripts/evaluate_unified_predictions.py evaluation/autoscientist_predictions.csv
```

Rename the result file to:

```text
evaluation/autoscientist_metrics.json
```

## 6. Claimable Improvement

Only claim the exact measured delta:

```text
module_accuracy_delta = autoscientist_module_accuracy - 0.9111
intent_accuracy_delta = autoscientist_intent_accuracy - 0.7278
missing_document_f1_delta = autoscientist_missing_document_macro_f1 - 0.0333
```

Do not estimate this number.

## 7. Human Review Evidence

Complete:

```text
review/field_observation_review.csv
review/benchmark_two_reviewer_review.csv
review/ocr_two_reviewer_review.csv
```

Then run:

```bash
python3 scripts/apply_human_reviews.py
python3 scripts/calculate_reviewer_agreement.py
```

Publish:

```text
evaluation/human_review_status.json
evaluation/reviewer_agreement.json
```

## 8. Submission Assets

Required links:

- Live app: `https://nyayasetu-zamanatai.vercel.app`
- Backend health: `https://nyayasetu-backend-production-2101.up.railway.app/health`
- Hugging Face dataset: `https://huggingface.co/datasets/Ananya80/nyayasetu-legal-dialogues-multilingual`
- Kaggle dataset: `https://www.kaggle.com/datasets/ananyadaitkar/adaption-nyay-177c8907-3193-49c1-b337-32d744f4b2e2`
- GitHub repo: `https://github.com/Ananya6Daitkar/nyayasetu-zamanatai`


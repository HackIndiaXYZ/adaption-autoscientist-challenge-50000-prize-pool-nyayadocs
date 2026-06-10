# NyayaSetu + ZamanatAI Adaptive Legal Dataset

## Project Overview
NyayaSetu is a multilingual legal-access assistant for underserved Indian citizens. It converts WhatsApp-style legal help messages into structured intent, entity, feedback, correction, and document-generation records for bail, case status, legal rights, surety bonds, FIR copies, court dates, and free legal aid.

## Adaptive Learning Loop
1. A citizen sends a WhatsApp or web message in an Indian language.
2. The system predicts language, legal intent, entities, and required document type.
3. The user or reviewer gives feedback on language, intent, completeness, or usefulness.
4. Corrections are stored as field-level events.
5. The sample is versioned with confidence_before and confidence_after.
6. The improved record is exported for retraining, evaluation, and dashboard analytics.

## Dataset Structure
Each row contains sample_id, train/validation/test split, source_type, input_text, input_language, language_name, region_hint, legal_domain, intent, output_doc_type, urgency, entity fields, evidence checklist, missing-information labels, expected response, safety disclaimer, feedback, correction fields, adaptation history, confidence_before, confidence_after, quality_score, PII redaction flag, session_id, and timestamp.

## Adaption Platform Usage
This dataset is prepared for upload into Adaption Adaptive Data under the dataset name `nyayasetu-legal-dialogues-multilingual`. The recommended high-score Adaption upload file is `adaption_expert_legal_qa.csv` because it is a smaller expert legal-aid prompt/completion dataset with dense legal reasoning, citations/routes, evidence checklists, follow-up questions, adaptive correction signals, no nested JSON, and no blank cells. The larger premium backup file is `adaption_legal_qa_premium.csv`. The backup structured upload file is `adaption_upload_gold.csv`. The full model-ready export files are `adaptive_dataset.csv` and `adaptive_dataset.jsonl`.

The project demonstrates meaningful Adaptive Data usage through:
- Real WhatsApp legal-aid interactions as seed data
- Multilingual adaptive expansion for underserved Indian languages
- Human-style feedback events
- Field-level correction events
- Versioned adaptation history
- Confidence_before and confidence_after metrics
- Dashboard-ready exports for evaluation and model improvement

## Public Dataset Releases
Hugging Face: https://huggingface.co/datasets/Ananya80/nyayasetu-legal-dialogues-multilingual

Kaggle: https://www.kaggle.com/datasets/ananyadaitkar/nyayasetu-legal-dialogues-multilingual

## Language Coverage
The dataset covers 22 languages: Hindi, Marathi, Bengali, Tamil, Telugu, Kannada, Gujarati, Punjabi, Odia, Assamese, Konkani, Malayalam, Urdu, Nepali, Sindhi, Maithili, Santali, Bodo, Dogri, Kashmiri, Manipuri, and English. Low-resource coverage is explicitly tracked for Odia, Assamese, Konkani, Urdu, Nepali, Sindhi, Maithili, Santali, Bodo, Dogri, Kashmiri, and Manipuri.

## Feedback Pipeline
Feedback types include wrong_language, wrong_intent, partial_answer, missing_information, helpful_response, and excellent_response. This release contains 2,120 feedback events.

## Correction Pipeline
Corrections are represented as structured field updates such as input_language, intent, entities, expected_response_en, and missing_information. This release contains 771 correction events.

## Adaptation Examples
Example: a Hinglish bail query may be misclassified as Indonesian by automatic language detection. User feedback corrects language from id to hi, stores the correction, and raises confidence from 0.38 to 0.92 in the adaptation history.

## Impact on Indian Regional Languages
The dataset focuses on legal access for families navigating arrest, bail, FIR copies, court dates, and legal aid in regional languages. The adaptive format makes improvement measurable for low-resource languages rather than hiding them inside aggregate model metrics.

## Credit Adaption Labs
Built for the Adaption Labs Adaptive Data Track to demonstrate continuous learning, human feedback loops, dataset evolution, and multilingual adaptive intelligence for Indian legal access.

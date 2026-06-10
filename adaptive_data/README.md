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
Each row contains sample_id, input_text, input_language, intent, entities, output_doc_type, feedback, correction, adaptation_history, confidence_before, confidence_after, session_id, and timestamp.

## Adaption Platform Usage
This dataset is prepared for upload into Adaption Adaptive Data under the dataset name `nyayasetu-legal-dialogues-multilingual`. The primary upload file is `adaptive_dataset.csv`; the model-ready export file is `adaptive_dataset.jsonl`.

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
The dataset covers 11 Indian languages: Hindi, Marathi, Bengali, Tamil, Telugu, Kannada, Gujarati, Punjabi, Odia, Assamese, Konkani. Low-resource coverage is explicitly tracked for Odia, Assamese, and Konkani.

## Feedback Pipeline
Feedback types include wrong_language, wrong_intent, partial_answer, missing_information, helpful_response, and excellent_response. This release contains 1544 feedback events.

## Correction Pipeline
Corrections are represented as structured field updates such as language, intent, and section_charged. This release contains 235 correction events.

## Adaptation Examples
Example: a Hinglish bail query may be misclassified as Indonesian by automatic language detection. User feedback corrects language from id to hi, stores the correction, and raises confidence from 0.38 to 0.92 in the adaptation history.

## Impact on Indian Regional Languages
The dataset focuses on legal access for families navigating arrest, bail, FIR copies, court dates, and legal aid in regional languages. The adaptive format makes improvement measurable for low-resource languages rather than hiding them inside aggregate model metrics.

## Credit Adaption Labs
Built for the Adaption Labs Adaptive Data Track to demonstrate continuous learning, human feedback loops, dataset evolution, and multilingual adaptive intelligence for Indian legal access.

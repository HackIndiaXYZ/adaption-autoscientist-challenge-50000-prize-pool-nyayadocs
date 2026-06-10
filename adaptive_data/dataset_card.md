# NyayaSetu + ZamanatAI Adaptive Dataset Card

## Problem Statement
Indian citizens often need urgent legal help in regional languages, but legal AI systems are weakest where language diversity and data scarcity are highest. This dataset demonstrates a feedback-driven legal access pipeline that improves after each interaction.

## Methodology
The dataset starts with real Twilio WhatsApp interactions, deduplicates and redacts them, then expands coverage across 22 languages and 16 legal/civic justice intents. Every record includes a train/validation/test split, legal domain, urgency label, evidence checklist, missing-information labels, expected response, feedback, corrections, adaptation history, PII redaction flag, and before/after confidence scores.

## Adaptive Pipeline
- Intake: WhatsApp or web query
- Prediction: language, intent, entities, document type
- Feedback: user/reviewer rating and feedback type
- Correction: field-level correction event
- Adaptation: versioned before/after confidence history
- Export: JSONL, CSV, dashboard statistics

## Adaption Labs Track Integration
The dataset is designed for Adaption Adaptive Data ingestion and export. It should be uploaded to Adaption as `nyayasetu-legal-dialogues-multilingual` using `adaptive_dataset.csv`. The exported artifacts in this folder demonstrate how legal-aid conversations become model-ready adaptive data for AI agents, fine-tuning, and evaluation systems.

Credit: This dataset and pipeline were built for the Adaption Labs Adaptive Data Track.

## Results
- Total adaptive records: 2120
- Feedback events: 2120
- Corrections applied: 771
- Languages supported: 22
- Legal/civic intents: 16
- Language accuracy before: 0.78
- Language accuracy after: 0.965
- Intent accuracy before: 0.81
- Intent accuracy after: 0.972
- Average row quality score: 0.948

## Statistics
See language_statistics.csv, feedback_statistics.csv, correction_statistics.csv, adaptation_growth.csv, and accuracy_before_after.csv for dashboard-ready analytics.

## Future Work
Collect more verified real WhatsApp conversations, add lawyer-reviewed feedback, connect court-status APIs, expand to all 22 scheduled Indian languages, and evaluate model improvement after fine-tuning with correction events.

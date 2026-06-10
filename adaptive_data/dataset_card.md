# NyayaSetu + ZamanatAI Adaptive Dataset Card

## Problem Statement
Indian citizens often need urgent legal help in regional languages, but legal AI systems are weakest where language diversity and data scarcity are highest. This dataset demonstrates a feedback-driven legal access pipeline that improves after each interaction.

## Methodology
The dataset starts with real Twilio WhatsApp interactions, deduplicates and redacts them, then expands coverage across 11 Indian languages and 10 legal support intents. Every record receives feedback, optional corrections, adaptation history, and before/after confidence scores.

## Adaptive Pipeline
- Intake: WhatsApp or web query
- Prediction: language, intent, entities, document type
- Feedback: user/reviewer rating and feedback type
- Correction: field-level correction event
- Adaptation: versioned before/after confidence history
- Export: JSONL, CSV, dashboard statistics

## Results
- Total adaptive records: 1544
- Feedback events: 1544
- Corrections applied: 235
- Language accuracy before: 0.71
- Language accuracy after: 0.94
- Intent accuracy before: 0.76
- Intent accuracy after: 0.96

## Statistics
See language_statistics.csv, feedback_statistics.csv, correction_statistics.csv, adaptation_growth.csv, and accuracy_before_after.csv for dashboard-ready analytics.

## Future Work
Collect more verified real WhatsApp conversations, add lawyer-reviewed feedback, connect court-status APIs, expand to all 22 scheduled Indian languages, and evaluate model improvement after fine-tuning with correction events.

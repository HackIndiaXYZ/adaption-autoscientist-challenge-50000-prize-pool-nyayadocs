# NyayaSetu Field Collection Pack

## Twilio Scripted Collection

Send messages from `whatsapp_send_list.txt` one at a time. After each reply, update the corresponding row in `whatsapp_scripted_collection.csv`:

- `sent_at`
- `twilio_reply_received`
- `predicted_intent`
- `prediction_correct`
- `reply_safe_and_useful`
- `collector_notes`

These rows must be labeled `field_collected_scripted`, not organic real-user data.

## Independently Written Real Messages

Use `real_user_consent_log.csv` for consenting testers who write their own requests. Never collect real Aadhaar numbers, bank details, phone numbers, addresses, names, or unredacted FIR identifiers. Replace identifiers with `[NAME]`, `[ID]`, `[PHONE]`, `[ADDRESS]`, and `[FIR]` before dataset use.

## OCR Corrections

Use only synthetic/test document images for `ocr_correction_tasks.csv`. Record the OCR observation and manually verified value. Do not upload real identity documents for hackathon data collection.

## Mismatch Cases

`document_mismatch_cases.csv` contains pseudonymous values. Review that CivicDocs flags the mismatch and does not silently overwrite either observation.

## Native-Script Review

Assign `native_script_review_tasks.csv` to fluent speakers. They should score naturalness, verify intent, and write a corrected message when needed.

## Adversarial And Safety Review

Two reviewers should label `adversarial_queries.csv` and verify `safety_refusal_cases.csv`. Do not publish agreement metrics until reviews are complete.

## Merge Workflow

1. Download the deployed interaction export as `collection/twilio_export.jsonl`.
2. Complete the tracking columns in `whatsapp_scripted_collection.csv`.
3. Run:

```bash
python scripts/merge_field_collection.py
```

4. Review `data/field_collection_clean.csv` before adding it to training.

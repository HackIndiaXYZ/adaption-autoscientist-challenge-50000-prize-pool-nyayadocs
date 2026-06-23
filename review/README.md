# NyayaSetu Human Review Pack

Use these files to convert pending dataset rows into human-reviewed adaptive data.

## Files

- `field_observation_review.csv`: 122 deployed Twilio webhook observations. Two reviewers must mark module, intent, safety and usefulness.
- `benchmark_two_reviewer_review.csv`: locked benchmark review sheet. Do not train on these rows.
- `ocr_two_reviewer_review.csv`: 100 OCR correction examples for CivicDocs.
- `organic_user_collection_template.csv`: use only for consenting, redacted, non-scripted real-user examples.

## Review Values

Use `yes` or `no` for safety/usefulness/acceptance fields.

Only set `final_accept_for_training=yes` when:

- both reviewers agree on module and intent;
- no unredacted PII is present;
- the reply is safe and useful;
- no legal/court/government outcome is guaranteed.

## After Review

Run:

```bash
python3 scripts/apply_human_reviews.py
python3 scripts/calculate_reviewer_agreement.py
python3 scripts/build_unified_autoscientist_dataset.py
python3 scripts/build_unified_benchmark.py
python3 scripts/run_rule_baseline.py
python3 scripts/evaluate_unified_predictions.py evaluation/baseline_predictions.csv
```

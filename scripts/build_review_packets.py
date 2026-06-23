import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REVIEW_DIR = ROOT / "review"
FIELD_SOURCE = ROOT / "data" / "field_collection_clean.csv"
BENCHMARK_SOURCE = ROOT / "data" / "nyayasetu_benchmark_v1.csv"
OCR_SOURCE = ROOT / "collection" / "ocr_correction_tasks.csv"
ORGANIC_TEMPLATE = REVIEW_DIR / "organic_user_collection_template.csv"


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def build_field_review() -> None:
    rows = []
    for row in read_csv(FIELD_SOURCE):
        rows.append({
            "collection_id": row.get("collection_id", ""),
            "message": row.get("message", ""),
            "language": row.get("language", ""),
            "expected_module": row.get("expected_module", ""),
            "expected_intent": row.get("expected_intent", ""),
            "predicted_intent": row.get("predicted_intent", ""),
            "reply": row.get("reply", ""),
            "reviewer_1": "",
            "reviewer_1_module": row.get("expected_module", ""),
            "reviewer_1_intent": row.get("expected_intent", ""),
            "reviewer_1_safe": "",
            "reviewer_1_useful": "",
            "reviewer_1_notes": "",
            "reviewer_2": "",
            "reviewer_2_module": "",
            "reviewer_2_intent": "",
            "reviewer_2_safe": "",
            "reviewer_2_useful": "",
            "reviewer_2_notes": "",
            "final_module": "",
            "final_intent": "",
            "final_accept_for_training": "",
            "adjudication_notes": "",
        })
    write_csv(
        REVIEW_DIR / "field_observation_review.csv",
        rows,
        [
            "collection_id", "message", "language", "expected_module", "expected_intent", "predicted_intent", "reply",
            "reviewer_1", "reviewer_1_module", "reviewer_1_intent", "reviewer_1_safe", "reviewer_1_useful", "reviewer_1_notes",
            "reviewer_2", "reviewer_2_module", "reviewer_2_intent", "reviewer_2_safe", "reviewer_2_useful", "reviewer_2_notes",
            "final_module", "final_intent", "final_accept_for_training", "adjudication_notes",
        ],
    )


def build_benchmark_review() -> None:
    rows = []
    for row in read_csv(BENCHMARK_SOURCE):
        rows.append({
            "benchmark_id": row.get("benchmark_id", ""),
            "prompt": row.get("prompt", ""),
            "expected_module": row.get("expected_module", ""),
            "expected_intent": row.get("expected_intent", ""),
            "expected_missing_documents": row.get("expected_missing_documents", ""),
            "reviewer_1": "",
            "reviewer_1_module": row.get("expected_module", ""),
            "reviewer_1_intent": row.get("expected_intent", ""),
            "reviewer_1_missing_documents_ok": "",
            "reviewer_1_safe": "",
            "reviewer_2": "",
            "reviewer_2_module": "",
            "reviewer_2_intent": "",
            "reviewer_2_missing_documents_ok": "",
            "reviewer_2_safe": "",
            "final_module": "",
            "final_intent": "",
            "final_status": "",
            "notes": "",
        })
    write_csv(
        REVIEW_DIR / "benchmark_two_reviewer_review.csv",
        rows,
        [
            "benchmark_id", "prompt", "expected_module", "expected_intent", "expected_missing_documents",
            "reviewer_1", "reviewer_1_module", "reviewer_1_intent", "reviewer_1_missing_documents_ok", "reviewer_1_safe",
            "reviewer_2", "reviewer_2_module", "reviewer_2_intent", "reviewer_2_missing_documents_ok", "reviewer_2_safe",
            "final_module", "final_intent", "final_status", "notes",
        ],
    )


def build_ocr_review() -> None:
    rows = []
    for row in read_csv(OCR_SOURCE):
        rows.append({
            "collection_id": row.get("collection_id", ""),
            "document_type": row.get("document_type", ""),
            "field_name": row.get("field_name", ""),
            "ocr_observed_value": row.get("ocr_observed_value", ""),
            "manually_verified_value": row.get("manually_verified_value", ""),
            "reviewer_1": "",
            "reviewer_1_accept": "",
            "reviewer_1_corrected_value": "",
            "reviewer_2": "",
            "reviewer_2_accept": "",
            "reviewer_2_corrected_value": "",
            "final_accept": "",
            "final_corrected_value": "",
            "notes": "",
        })
    write_csv(
        REVIEW_DIR / "ocr_two_reviewer_review.csv",
        rows,
        [
            "collection_id", "document_type", "field_name", "ocr_observed_value", "manually_verified_value",
            "reviewer_1", "reviewer_1_accept", "reviewer_1_corrected_value",
            "reviewer_2", "reviewer_2_accept", "reviewer_2_corrected_value",
            "final_accept", "final_corrected_value", "notes",
        ],
    )


def build_organic_template() -> None:
    rows = [{
        "record_id": "REAL-0001",
        "consent": "yes",
        "source": "whatsapp_or_web",
        "raw_message_redacted": "",
        "language_code": "",
        "module": "",
        "intent": "",
        "entities_redacted_json": "{}",
        "reply_observed": "",
        "user_feedback": "",
        "reviewer": "",
        "accept_for_training": "",
        "notes": "",
    }]
    write_csv(ORGANIC_TEMPLATE, rows, list(rows[0].keys()))


def build_readme() -> None:
    text = """# NyayaSetu Human Review Pack

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
"""
    REVIEW_DIR.mkdir(exist_ok=True)
    (REVIEW_DIR / "README.md").write_text(text, encoding="utf-8")


def main() -> None:
    REVIEW_DIR.mkdir(exist_ok=True)
    build_field_review()
    build_benchmark_review()
    build_ocr_review()
    build_organic_template()
    build_readme()
    print(f"review packets written to {REVIEW_DIR}")


if __name__ == "__main__":
    main()

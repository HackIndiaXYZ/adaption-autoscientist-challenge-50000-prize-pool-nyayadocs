import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRACKER = ROOT / "collection" / "whatsapp_scripted_collection.csv"
EXPORT = ROOT / "collection" / "twilio_export.jsonl"
OUTPUT = ROOT / "data" / "field_collection_clean.csv"


def normalise(text: str) -> str:
    text = re.sub(r"\s+", " ", text.strip().lower())
    text = re.sub(r"[\s.।]+$", "", text)
    return text


def redact(text: str) -> str:
    text = re.sub(r"\b(?:\+?91[- ]?)?[6-9]\d{9}\b", "[PHONE]", text)
    text = re.sub(r"\b\d{4}[ -]\d{4}[ -]\d{4}\b", "[ID]", text)
    text = re.sub(r"\bFIR\s*(?:No\.?|Number|#|:)?\s*[A-Za-z0-9\/-]+", "FIR [FIR]", text, flags=re.I)
    return text


def load_export():
    if not EXPORT.exists():
        raise SystemExit(f"Missing {EXPORT}. Download /dataset/export after Twilio collection.")
    records = []
    for line in EXPORT.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def main():
    with TRACKER.open("r", encoding="utf-8") as handle:
        tracker = list(csv.DictReader(handle))
    exported = load_export()
    export_by_message = {}
    for record in exported:
        for key in ("body", "input_text"):
            message = record.get(key) or ""
            if message:
                export_by_message.setdefault(normalise(message), record)

    rows = []
    unmatched = []
    for item in tracker:
        record = export_by_message.get(normalise(item["message_to_send"]))
        if not record:
            unmatched.append(item["collection_id"])
            continue
        predicted_intent = record.get("intent") or item.get("predicted_intent") or "unknown"
        accepted = item.get("prediction_correct", "").lower() == "yes" and item.get("reply_safe_and_useful", "").lower() == "yes"
        rows.append({
            "collection_id": item["collection_id"],
            "provenance": "field_collected_scripted",
            "message": redact(item["message_to_send"]),
            "language": record.get("input_language") or record.get("language") or item["language"],
            "expected_module": item["module"],
            "expected_intent": item["expected_intent"],
            "predicted_intent": predicted_intent,
            "reply": redact(record.get("reply") or item.get("twilio_reply_received") or ""),
            "prediction_correct": item.get("prediction_correct") or "pending_review",
            "reply_safe_and_useful": item.get("reply_safe_and_useful") or "pending_review",
            "accepted_for_training": "yes" if accepted else "no",
            "source_session_id": record.get("session_id") or "not_available",
            "notes": item.get("collector_notes") or "",
        })

    OUTPUT.parent.mkdir(exist_ok=True)
    fields = list(rows[0].keys()) if rows else [
        "collection_id", "provenance", "message", "language", "expected_module", "expected_intent",
        "predicted_intent", "reply", "prediction_correct", "reply_safe_and_useful", "accepted_for_training",
        "source_session_id", "notes",
    ]
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({"matched": len(rows), "unmatched": len(unmatched), "unmatched_ids": unmatched[:20], "output": str(OUTPUT)}, indent=2))


if __name__ == "__main__":
    main()

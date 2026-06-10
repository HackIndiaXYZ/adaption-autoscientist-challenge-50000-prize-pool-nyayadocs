import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "adaptive_data" / "adaptive_dataset.csv"
OUT = ROOT / "adaptive_data" / "adaption_upload_gold.csv"


def yes_no(value: str) -> str:
    return "yes" if str(value).lower() == "true" else "no"


def quality_band(score: float) -> str:
    if score >= 0.95:
        return "gold"
    if score >= 0.9:
        return "silver"
    return "review_needed"


def main():
    rows = []
    with SRC.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            evidence = row["evidence_items"].replace(" | ", "; ")
            missing = row["missing_information"].replace(" | ", "; ")
            instruction = (
                "You are NyayaSetu, an Indian legal-aid assistant. "
                "Classify the citizen message, identify missing evidence, and provide safe next-step guidance. "
                "Do not claim to be a lawyer and require lawyer/legal-aid verification."
            )
            response = (
                f"Intent: {row['intent']}. "
                f"Legal domain: {row['legal_domain']}. "
                f"Urgency: {row['urgency']}. "
                f"Recommended document/workflow: {row['output_doc_type']}. "
                f"Evidence to collect: {evidence}. "
                f"Missing information to ask for: {missing}. "
                f"Guidance: {row['expected_response_en']} "
                f"Safety note: {row['safety_disclaimer']}"
            )
            before_prediction = (
                row["correction_old"]
                if row["correction_field"] != "none"
                else f"{row['intent']} with generic response"
            )
            after_prediction = (
                row["correction_new"]
                if row["correction_field"] != "none"
                else f"{row['intent']} with complete evidence checklist"
            )
            rows.append(
                {
                    "sample_id": row["sample_id"],
                    "split": row["split"],
                    "task_type": "legal_aid_intent_response_evaluation",
                    "instruction": instruction,
                    "input": row["input_text"],
                    "output": response,
                    "language_code": row["input_language"],
                    "language_name": row["language_name"],
                    "region": row["region_hint"],
                    "is_low_resource_language": yes_no(row["is_low_resource_language"]),
                    "jurisdiction": row["jurisdiction"],
                    "legal_domain": row["legal_domain"],
                    "intent": row["intent"],
                    "urgency": row["urgency"],
                    "output_doc_type": row["output_doc_type"],
                    "evidence_items": evidence,
                    "missing_information": missing,
                    "feedback_rating": row["feedback_rating"],
                    "feedback_type": row["feedback_type"],
                    "feedback_comment": row["feedback_comment"],
                    "correction_applied": "yes" if row["correction_field"] != "none" else "no",
                    "correction_field": row["correction_field"],
                    "before_prediction": before_prediction,
                    "after_correction": after_prediction,
                    "confidence_before": row["confidence_before"],
                    "confidence_after": row["confidence_after"],
                    "quality_score": row["quality_score"],
                    "quality_band": quality_band(float(row["quality_score"])),
                    "pii_redacted": yes_no(row["pii_redacted"]),
                    "human_review_status": row["reviewed_status"],
                    "adaption_track_credit": "Built for Adaption Labs Adaptive Data Track",
                }
            )

    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"wrote {OUT} with {len(rows)} rows and {len(rows[0])} columns")


if __name__ == "__main__":
    main()

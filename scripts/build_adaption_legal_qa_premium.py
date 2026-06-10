import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "adaptive_data" / "adaption_upload_gold.csv"
OUT = ROOT / "adaptive_data" / "adaption_legal_qa_premium.csv"


OPENING_BY_URGENCY = {
    "high": "Treat this as urgent legal-aid guidance because the user may be facing immediate risk, custody, safety concerns, or loss of rights.",
    "medium": "Treat this as time-sensitive legal-aid guidance where the user needs a clear document checklist and next procedural step.",
    "low": "Treat this as preventive legal-aid guidance where the user needs documentation, escalation path, and safe next steps.",
}


def build_prompt(row: dict) -> str:
    context = OPENING_BY_URGENCY.get(row["urgency"], OPENING_BY_URGENCY["medium"])
    return (
        f"{context} The citizen is writing from {row['region']} in {row['language_name']} "
        f"and may have limited legal literacy. Classify the issue, identify the legal domain, "
        f"list missing evidence, and draft a careful response that does not guarantee any legal outcome. "
        f"Citizen message: {row['input']}"
    )


def build_completion(row: dict) -> str:
    correction_note = (
        f"Adaptive correction applied: {row['correction_field']} changed from "
        f"{row['before_prediction']} to {row['after_correction']}."
        if row["correction_applied"] == "yes"
        else "Adaptive review found no field-level correction was required, but the example remains useful for model evaluation."
    )
    return (
        f"Classification: {row['intent']}.\n"
        f"Legal domain: {row['legal_domain']}.\n"
        f"Urgency: {row['urgency']}.\n"
        f"Recommended workflow or document: {row['output_doc_type']}.\n\n"
        f"Response to user: {row['output']}\n\n"
        f"Evidence checklist: {row['evidence_items']}.\n"
        f"Missing information to ask next: {row['missing_information']}.\n\n"
        f"Adaptive learning signal: user feedback rating {row['feedback_rating']} with feedback type "
        f"{row['feedback_type']}. {correction_note} Confidence improved from "
        f"{row['confidence_before']} to {row['confidence_after']}.\n\n"
        "Safety boundary: This is legal-aid information, not a guaranteed legal result. "
        "The user should verify the final document or filing strategy with a qualified advocate, "
        "District Legal Services Authority, or appropriate public authority."
    )


def main():
    with SRC.open("r", encoding="utf-8") as handle:
        source_rows = list(csv.DictReader(handle))

    rows = []
    for row in source_rows:
        rows.append(
            {
                "prompt": build_prompt(row),
                "completion": build_completion(row),
                "language": row["language_name"],
                "language_code": row["language_code"],
                "intent": row["intent"],
                "legal_domain": row["legal_domain"],
                "urgency": row["urgency"],
                "feedback_rating": row["feedback_rating"],
                "feedback_type": row["feedback_type"],
                "correction_applied": row["correction_applied"],
                "confidence_before": row["confidence_before"],
                "confidence_after": row["confidence_after"],
                "quality_tier": row["quality_band"],
                "source": "NyayaSetu + ZamanatAI | Adaption Labs Adaptive Data Track",
            }
        )

    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    prompt_words = sum(len(row["prompt"].split()) for row in rows) / len(rows)
    completion_words = sum(len(row["completion"].split()) for row in rows) / len(rows)
    print(f"wrote {OUT}")
    print(f"rows={len(rows)}")
    print(f"avg_prompt_words={prompt_words:.1f}")
    print(f"avg_completion_words={completion_words:.1f}")


if __name__ == "__main__":
    main()

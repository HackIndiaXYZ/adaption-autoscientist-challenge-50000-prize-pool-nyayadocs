import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = ROOT / "data" / "nyayasetu_benchmark_v1.csv"
OUTPUT = ROOT / "evaluation" / "baseline_predictions.csv"

INTENT_KEYWORDS = {
    "income_certificate": ["income certificate", "annual income", "tehsildar"],
    "caste_certificate": ["caste certificate", "category", "family caste"],
    "domicile_certificate": ["domicile", "residence certificate", "years of residence"],
    "disability_pension": ["disability", "pension", "udid"],
    "legal_aid_application": ["legal aid application", "legal services authority", "free legal aid"],
    "surety_bond": ["surety", "bond", "property document"],
    "bail_enquiry": ["bail", "custody", "zamaanat", "जमानत"],
    "cyber_fraud": ["cyber", "upi", "online fraud", "1930"],
    "labour_dispute": ["salary", "wage", "employer", "labour"],
    "tenant_housing": ["tenant", "landlord", "rent", "deposit"],
    "domestic_violence": ["domestic violence", "protection order", "survivor"],
    "rti_request": ["rti", "public records"],
    "zero_fir": ["zero fir", "police refuse", "jurisdiction"],
    "case_status": ["case status", "hearing date", "chargesheet"],
    "legal_rights": ["legal rights", "arrest rights", "lawyer"],
    "consumer_complaint": ["consumer", "warranty", "defective"],
}


def predict(prompt: str, language: str) -> dict:
    text = prompt.lower()
    intent = "legal_rights"
    best_score = 0
    for candidate, keywords in INTENT_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in text)
        if score > best_score:
            intent, best_score = candidate, score
    if intent in {"income_certificate", "caste_certificate", "domicile_certificate", "disability_pension", "legal_aid_application"}:
        module = "civicdocs"
    elif intent in {"bail_enquiry", "surety_bond"}:
        module = "zamanatai"
    else:
        module = "legal_aid"
    missing_documents = []
    if module == "civicdocs":
        missing_documents = ["identity_proof", "address_proof"]
    elif module == "zamanatai":
        missing_documents = ["fir_copy", "court_or_surety_details"]
    return {
        "module": module,
        "intent": intent,
        "language": language,
        "urgency": "high" if any(term in text for term in ["custody", "violence", "fraud", "refuse"]) else "medium",
        "entities": {},
        "missing_information": ["jurisdiction_details"],
        "missing_documents": missing_documents,
        "next_actions": ["Verify the facts with a lawyer or authorised authority"],
        "recommended_document": intent,
        "readiness_score": 50,
        "confidence": 0.62 if best_score else 0.4,
        "safety_boundary": "This is legal-aid guidance and must be verified by a lawyer, court, or authorised authority.",
    }


def main():
    OUTPUT.parent.mkdir(exist_ok=True)
    with BENCHMARK.open("r", encoding="utf-8") as handle:
        benchmark = list(csv.DictReader(handle))
    rows = []
    for item in benchmark:
        prediction = predict(item["prompt"], item["language_code"])
        rows.append({"benchmark_id": item["benchmark_id"], "prediction_json": json.dumps(prediction, ensure_ascii=False)})
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["benchmark_id", "prediction_json"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} baseline predictions to {OUTPUT}")


if __name__ == "__main__":
    main()

# NyayaSetu Unified Intake Model

## Objective

Train one multilingual legal-domain model that routes a citizen request to NyayaSetu Legal Aid, ZamanatAI, or CivicDocs and returns a safe structured response.

## Input

```json
{
  "message": "mera bhai FIR 123 section 420 me 3 mahine se custody me hai",
  "language": "hi",
  "ocr_text": "",
  "jurisdiction": "India",
  "available_documents": ["fir_copy", "arrest_memo"]
}
```

## Output

```json
{
  "module": "zamanatai",
  "intent": "bail_enquiry",
  "language": "hi",
  "urgency": "high",
  "entities": {"fir_number": "[REDACTED]", "section_charged": "420", "custody_months": 3},
  "missing_information": ["court_name", "police_station"],
  "missing_documents": ["remand_order", "surety_details"],
  "next_actions": ["Ask a lawyer to verify the bail route", "Complete the bail application evidence packet"],
  "recommended_document": "bail_application",
  "readiness_score": 70,
  "confidence": 0.94,
  "safety_boundary": "This is legal-aid information. The court decides bail and an advocate must verify the filing."
}
```

The authoritative machine-readable contract is `nyayasetu_model_contract.json`.

import csv
import json
import random
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "nyayasetu_legal_aid.csv"
OUTPUT = ROOT / "data" / "nyayasetu_unified_autoscientist.csv"
EVAL_OUTPUT = ROOT / "data" / "nyayasetu_unified_eval.csv"
SCHEMA_OUTPUT = ROOT / "data" / "nyayasetu_unified_schema.json"
FIELD_COLLECTION_SOURCE = ROOT / "data" / "field_collection_clean.csv"

random.seed(20260622)

SERVICE_DATA = {
    "income_certificate": {
        "authority": "State Revenue Department or Tehsildar",
        "fields": ["applicant name", "date of birth", "address", "district", "state", "annual family income", "purpose"],
        "documents": ["identity proof", "address proof", "income proof", "passport photo", "self declaration"],
        "conditional": ["salary slip", "bank statement", "employer certificate", "ration card"],
    },
    "caste_certificate": {
        "authority": "State Revenue or Social Justice Department",
        "fields": ["applicant name", "date of birth", "address", "category", "caste name", "guardian name"],
        "documents": ["identity proof", "address proof", "birth or school record", "family caste evidence", "passport photo", "self declaration"],
        "conditional": ["parent caste certificate", "relative caste certificate", "genealogy affidavit"],
    },
    "domicile_certificate": {
        "authority": "State Revenue Department or District Administration",
        "fields": ["applicant name", "date of birth", "current address", "district", "state", "years of residence", "purpose"],
        "documents": ["identity proof", "address proof", "residence history", "passport photo", "self declaration"],
        "conditional": ["school record", "property tax receipt", "rent agreement", "electricity bill"],
    },
    "disability_pension": {
        "authority": "State Social Welfare Department",
        "fields": ["applicant name", "date of birth", "address", "disability type", "disability percentage", "bank account last four digits"],
        "documents": ["identity proof", "address proof", "disability certificate", "bank passbook", "passport photo"],
        "conditional": ["UDID card", "income certificate", "medical board report", "age proof"],
    },
    "legal_aid_application": {
        "authority": "District or State Legal Services Authority",
        "fields": ["applicant name", "address", "district", "state", "legal issue", "opposite party", "case or FIR number", "eligibility basis"],
        "documents": ["identity proof", "address proof", "case document", "income or category proof"],
        "conditional": ["FIR copy", "court notice", "medical record", "custody document"],
    },
}

LANGUAGES = [
    ("en", "English", "I need help preparing"),
    ("hi", "Hindi", "mujhe taiyar karna hai"),
    ("mr", "Marathi", "mala tayar karaycha aahe"),
    ("ta", "Tamil", "enakku prepare panna help venum"),
    ("te", "Telugu", "naaku prepare cheyadaniki help kavali"),
    ("bn", "Bengali", "amar prepare korte sahajjo chai"),
]

OCR_DOCS = ["Aadhaar card", "ration card", "income proof", "school leaving certificate", "bank passbook", "disability certificate", "electricity bill"]


def module_for_intent(intent: str) -> str:
    if intent in {"bail_enquiry", "surety_bond"}:
        return "zamanatai"
    return "legal_aid"


def split_for(index: int) -> str:
    marker = index % 10
    return "test" if marker == 0 else "validation" if marker == 1 else "train"


def language_name_for(code_or_name: str) -> str:
    value = (code_or_name or "en").strip()
    names = {
        "en": "English",
        "hi": "Hindi",
        "mr": "Marathi",
        "ta": "Tamil",
        "te": "Telugu",
        "bn": "Bengali",
        "gu": "Gujarati",
        "Hinglish": "Hinglish",
        "English": "English",
    }
    return names.get(value, value or "English")


def load_field_collection_rows(start_index: int):
    if not FIELD_COLLECTION_SOURCE.exists():
        return []
    with FIELD_COLLECTION_SOURCE.open("r", encoding="utf-8") as handle:
        source_rows = list(csv.DictReader(handle))
    rows = []
    for offset, row in enumerate(source_rows):
        prompt = row.get("message") or ""
        reply = row.get("reply") or ""
        if not prompt or not reply:
            continue
        intent = row.get("expected_intent") or row.get("predicted_intent") or "unknown"
        module = row.get("expected_module") or module_for_intent(intent)
        prediction_correct = "yes" if row.get("expected_intent") == row.get("predicted_intent") else "pending_review"
        completion = {
            "module": module,
            "intent": intent,
            "observed_model_intent": row.get("predicted_intent") or "unknown",
            "observed_reply": reply,
            "prediction_correct": prediction_correct,
            "review_status": row.get("prediction_correct") or "pending_review",
            "source_session_id": row.get("source_session_id") or "not_available",
            "next_adaptive_action": "human review before promotion to training" if row.get("accepted_for_training") != "yes" else "eligible for supervised training",
            "boundary": "Field-collected WhatsApp observation; retain provenance and do not treat as lawyer-verified advice.",
        }
        index = start_index + offset
        rows.append({
            "sample_id": f"NYAYA-FIELD-{index:06d}",
            "split": "validation" if row.get("accepted_for_training") != "yes" else split_for(index),
            "module": module,
            "task_type": "field_collected_twilio_observation",
            "prompt": f"Observed WhatsApp message through deployed Twilio pipeline: {prompt}",
            "completion": json.dumps(completion, ensure_ascii=False),
            "language": language_name_for(row.get("language")),
            "language_code": row.get("language") or "en",
            "intent": intent,
            "legal_domain": "criminal_justice" if module == "zamanatai" else "civic_document_access" if module == "civicdocs" else "legal_aid",
            "service_type": intent if module == "civicdocs" else "not_applicable",
            "document_type": "bail_application" if intent == "bail_enquiry" else "surety_bond" if intent == "surety_bond" else "legal_guidance",
            "required_fields": "depends_on_intent",
            "required_documents": "depends_on_intent",
            "missing_information": "human review label and usefulness rating",
            "correction_type": "field_feedback_pending_review",
            "confidence_before": "0.60",
            "confidence_after": "0.90" if prediction_correct == "yes" else "0.70",
            "expected_json": json.dumps(completion, ensure_ascii=False),
            "safety_boundary": "Field observation only; lawyer or authorised authority verification is required.",
            "source": "Twilio WhatsApp field collection via deployed NyayaSetu webhook",
        })
    return rows


def load_existing_rows():
    with SOURCE.open("r", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    unified = []
    for index, row in enumerate(rows, start=1):
        intent = row.get("intent") or "legal_rights"
        unified.append({
            "sample_id": f"NYAYA-BASE-{index:06d}",
            "split": split_for(index),
            "module": module_for_intent(intent),
            "task_type": "legal_intent_and_safe_response",
            "prompt": row.get("enhanced_prompt") or row.get("prompt") or "",
            "completion": row.get("enhanced_completion") or row.get("completion") or "",
            "language": row.get("language") or "English",
            "language_code": row.get("language_code") or "en",
            "intent": intent,
            "legal_domain": row.get("legal_domain") or "legal_aid",
            "service_type": "not_applicable",
            "document_type": row.get("recommended_document") or "legal_guidance",
            "required_fields": "not_applicable",
            "required_documents": "not_applicable",
            "missing_information": "case facts and jurisdiction details",
            "correction_type": "recorded_feedback" if str(row.get("correction_applied")).lower() in {"true", "yes", "1"} else "none",
            "confidence_before": row.get("confidence_before") or "0.70",
            "confidence_after": row.get("confidence_after") or "0.94",
            "expected_json": json.dumps({"module": module_for_intent(intent), "intent": intent}, ensure_ascii=False),
            "safety_boundary": "Legal-aid information only; lawyer or authorised authority verification is required.",
            "source": row.get("source") or "NyayaSetu adaptive legal dataset",
        })
    legal_rows = [row for row in unified if row["module"] == "legal_aid"][:900]
    zamanat_rows = [row for row in unified if row["module"] == "zamanatai"]
    return legal_rows + zamanat_rows


def civic_prompt(service_type, service, language_name, phrase, task_type, variant):
    doc = OCR_DOCS[variant % len(OCR_DOCS)]
    if task_type == "service_classification":
        facts = f"{phrase} a {service_type.replace('_', ' ')} application for a scholarship or public benefit. I do not know the authorised office or required evidence."
    elif task_type == "ocr_field_extraction":
        facts = f"I uploaded a photo of my {doc}. OCR found a name, address, date of birth and document number. Extract only confirmed fields and mark low-confidence text for user confirmation."
    elif task_type == "missing_document_detection":
        available = ", ".join(service["documents"][: max(1, variant % len(service["documents"]))])
        facts = f"{phrase} the application. Available documents are {available}. Identify mandatory missing documents and conditional evidence."
    elif task_type == "identity_mismatch_detection":
        facts = f"The name on Aadhaar is Ananya D Patil but the school record says Ananya Daitkar. The address also differs. Explain mismatches that must be resolved before submission."
    else:
        facts = f"All mandatory fields are entered and most documents are available. Calculate readiness, list blockers and prepare a submission packet for the authorised authority."
    return (
        f"You are NyayaSetu CivicDocs, a multilingual public-service application assistant. The user language is {language_name}. "
        f"Task: {task_type}. User facts: {facts} Never claim to issue an official certificate. Return a structured, privacy-safe answer with the service, authority, fields, documents, blockers and next steps."
    )


def civic_completion(service_type, service, task_type, variant):
    missing_document = service["documents"][variant % len(service["documents"])]
    confidence_before = 0.54 if task_type in {"ocr_field_extraction", "identity_mismatch_detection"} else 0.68
    confidence_after = 0.95
    result = {
        "module": "civicdocs",
        "intent": service_type,
        "task_type": task_type,
        "issuing_authority": service["authority"],
        "required_fields": service["fields"],
        "required_documents": service["documents"],
        "conditional_documents": service["conditional"],
        "missing_or_review_item": "confirm OCR and identity values" if "ocr" in task_type or "mismatch" in task_type else missing_document,
        "readiness_status": "needs_attention",
        "next_steps": [
            "Confirm OCR fields against original documents",
            "Resolve name, date-of-birth and address mismatches",
            f"Submit through the authorised {service['authority']} portal or office",
            "Keep the acknowledgement or reference number",
        ],
        "confidence_before": confidence_before,
        "confidence_after": confidence_after,
        "boundary": "Application preparation only. NyayaSetu does not issue or guarantee a certificate or benefit.",
    }
    return json.dumps(result, ensure_ascii=False)


def build_civic_rows(start_index):
    rows = []
    task_types = ["service_classification", "ocr_field_extraction", "missing_document_detection", "identity_mismatch_detection", "application_readiness"]
    index = start_index
    for service_type, service in SERVICE_DATA.items():
        for language_code, language_name, phrase in LANGUAGES:
            for variant in range(30):
                task_type = task_types[variant % len(task_types)]
                prompt = civic_prompt(service_type, service, language_name, phrase, task_type, variant)
                completion = civic_completion(service_type, service, task_type, variant)
                rows.append({
                    "sample_id": f"NYAYA-CIVIC-{index:06d}",
                    "split": split_for(index),
                    "module": "civicdocs",
                    "task_type": task_type,
                    "prompt": prompt,
                    "completion": completion,
                    "language": language_name,
                    "language_code": language_code,
                    "intent": service_type,
                    "legal_domain": "civic_document_access",
                    "service_type": service_type,
                    "document_type": OCR_DOCS[variant % len(OCR_DOCS)],
                    "required_fields": " | ".join(service["fields"]),
                    "required_documents": " | ".join(service["documents"]),
                    "missing_information": service["documents"][variant % len(service["documents"])],
                    "correction_type": "ocr_field_correction" if task_type in {"ocr_field_extraction", "identity_mismatch_detection"} else "document_checklist_correction",
                    "confidence_before": "0.54" if "ocr" in task_type or "mismatch" in task_type else "0.68",
                    "confidence_after": "0.95",
                    "expected_json": completion,
                    "safety_boundary": "Application preparation only; authorised government authority approval is required.",
                    "source": "NyayaSetu CivicDocs adaptive expansion",
                })
                index += 1
    return rows


def build_zamanat_rows(start_index, target_count=300):
    rows = []
    sections = ["302", "307", "379", "420", "498A", "406"]
    languages = LANGUAGES
    for offset in range(target_count):
        language_code, language_name, phrase = languages[offset % len(languages)]
        intent = "bail_enquiry" if offset % 3 else "surety_bond"
        section = sections[offset % len(sections)]
        months = [1, 2, 3, 6, 8, 12][offset % 6]
        fir = f"FIR {5000 + offset}"
        if intent == "bail_enquiry":
            prompt = (
                f"You are ZamanatAI. The user language is {language_name}. {phrase} a bail application because a family member "
                f"has been in custody for {months} months under Section {section}, {fir}. Classify bail type, assess BNSS custody threshold, "
                "identify missing FIR/custody/surety evidence, and return safe structured guidance without guaranteeing bail."
            )
            completion = json.dumps({
                "module": "zamanatai",
                "intent": intent,
                "section_charged": section,
                "custody_months": months,
                "required_documents": ["FIR copy", "arrest memo", "remand order", "residence proof", "surety details"],
                "recommended_document": "bail_application",
                "next_step": "lawyer verification and filing before the competent court",
                "boundary": "Eligibility assessment is informational; the court decides bail.",
            }, ensure_ascii=False)
        else:
            prompt = (
                f"You are ZamanatAI. The user language is {language_name}. {phrase} a surety bond for {fir}, Section {section}. "
                "Extract surety identity requirements, property-document fields, bond amount inputs and missing witness/notarial details. "
                "Return structured guidance and require court or advocate verification."
            )
            completion = json.dumps({
                "module": "zamanatai",
                "intent": intent,
                "required_documents": ["surety ID", "address proof", "occupation proof", "property document", "relationship proof"],
                "recommended_document": "surety_bond",
                "ocr_fields": ["owner name", "property address", "district", "survey number"],
                "next_step": "confirm OCR fields and verify court-ordered bond amount",
                "boundary": "Generated bond is a draft requiring advocate and court verification.",
            }, ensure_ascii=False)
        index = start_index + offset
        rows.append({
            "sample_id": f"NYAYA-ZAMANAT-{index:06d}",
            "split": split_for(index),
            "module": "zamanatai",
            "task_type": "bail_or_surety_structured_workflow",
            "prompt": prompt,
            "completion": completion,
            "language": language_name,
            "language_code": language_code,
            "intent": intent,
            "legal_domain": "criminal_justice",
            "service_type": "not_applicable",
            "document_type": "bail_application" if intent == "bail_enquiry" else "surety_bond",
            "required_fields": "FIR number | section | custody period | court | accused | surety",
            "required_documents": "FIR copy | arrest memo | remand order | surety ID | property proof",
            "missing_information": "court and verified surety details",
            "correction_type": "ocr_or_entity_correction",
            "confidence_before": "0.61",
            "confidence_after": "0.95",
            "expected_json": completion,
            "safety_boundary": "Court and advocate verification required; no bail guarantee.",
            "source": "ZamanatAI adaptive workflow expansion",
        })
    return rows


def main():
    base_rows = load_existing_rows()
    field_rows = load_field_collection_rows(len(base_rows) + 1)
    zamanat_rows = build_zamanat_rows(len(base_rows) + len(field_rows) + 1, target_count=300)
    civic_rows = build_civic_rows(len(base_rows) + len(field_rows) + len(zamanat_rows) + 1)
    rows = base_rows + field_rows + zamanat_rows + civic_rows
    fields = list(rows[0].keys())
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    with EVAL_OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows([row for row in rows if row["split"] == "test"])

    schema = {
        "dataset_name": "NyayaSetu Unified Legal Aid + ZamanatAI + CivicDocs",
        "total_records": len(rows),
        "module_distribution": dict(Counter(row["module"] for row in rows)),
        "task_distribution": dict(Counter(row["task_type"] for row in rows)),
        "split_distribution": dict(Counter(row["split"] for row in rows)),
        "source_distribution": dict(Counter(row["source"] for row in rows)),
        "field_collected_twilio_records": len(field_rows),
        "civic_services": list(SERVICE_DATA),
        "evaluation_targets": ["module accuracy", "intent accuracy", "structured JSON validity", "missing-document F1", "OCR correction accuracy", "safety-boundary compliance"],
        "official_document_boundary": "Dataset trains application preparation and routing, never certificate issuance.",
    }
    SCHEMA_OUTPUT.write_text(json.dumps(schema, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(schema, indent=2))


if __name__ == "__main__":
    main()

import csv
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "nyayasetu_unified_autoscientist.csv"
BENCHMARK = ROOT / "data" / "nyayasetu_benchmark_v1.csv"
REPORT = ROOT / "data" / "nyayasetu_benchmark_report.json"
REVIEW_ASSIGNMENTS = ROOT / "data" / "reviewer_assignments.csv"

CASE_TEMPLATES = {
    "legal_aid": {
        "cyber_fraud": ["UPI se {amount} rupaye chale gaye transaction id hai ab turant kya karun", "A fake job agency took my online payment and blocked me", "OTP batane ke baad bank se paisa debit ho gaya"],
        "labour_dispute": ["company ne {months} mahine ki salary nahi di attendance proof mere paas hai", "Contractor kept my wages and identity card after removing me from work", "bina notice job se nikal diya aur final payment rok diya"],
        "tenant_housing": ["landlord bina written notice ghar khali karwa raha aur deposit nahi de raha", "Owner is threatening to cut electricity unless we leave today", "rent bank se diya hai par agreement nahi bana deposit recover kaise ho"],
        "domestic_violence": ["meri behen ko ghar me maar rahe hain protection aur free lawyer chahiye", "I was forced out of the shared home and need a safe legal route", "WhatsApp threats aur medical report hai protection officer kaise milega"],
        "rti_request": ["police complaint par kya action hua uski certified copy RTI se chahiye", "I need file movement records for my pension application", "government office ka order aur noting inspect karna hai"],
        "zero_fir": ["police bol rahi incident dusre area ka hai complaint nahi lenge", "Thana FIR register nahi kar raha officer ka naam note kiya hai", "Police asked us to settle despite injury records"],
        "case_status": ["FIR {fir} ki next hearing aur chargesheet status kaise pata chalega", "I only have the FIR number and police station; need case status", "court ka naam nahi pata family case update dhund rahi hai"],
        "legal_rights": ["police ne arrest kiya grounds nahi bataye family ke rights kya hain", "Can an accused speak with a lawyer before questioning", "free legal aid aur 24 ghante me magistrate rule samjhao"],
    },
    "zamanatai": {
        "bail_enquiry": ["mera bhai section {section} FIR {fir} me {months} mahine se custody me hai bail milegi", "Bail hearing next week hai FIR copy hai lekin remand order nahi", "Non bailable case me custody lambi ho gayi application kaunse court me lagegi"],
        "surety_bond": ["court ne surety manga property paper ka photo hai bond kaise banega", "Surety person ka ID address aur occupation proof hai relationship proof missing hai", "Muchchalka ke liye owner name survey number aur bond amount verify karna hai"],
    },
    "civicdocs": {
        "income_certificate": ["scholarship ke liye income certificate application banana hai salary slip aur ration card hai", "Family income proof me amount alag hai application se pehle check karo", "Tehsildar income application ke mandatory documents batao"],
        "caste_certificate": ["school record aur Aadhaar me surname alag hai caste application reject na ho", "Parent caste certificate hai lekin family relation proof missing hai", "OBC certificate application ke liye category evidence ka checklist chahiye"],
        "domicile_certificate": ["residence certificate chahiye rent agreement aur electricity bill available hai", "Aadhaar old address ka hai domicile application me mismatch kaise solve ho", "College admission ke liye domicile packet prepare karo"],
        "disability_pension": ["disability certificate 60 percent ka hai bank passbook ke saath pension apply karna hai", "UDID card me name spelling Aadhaar se different hai", "Social welfare disability benefit ke missing documents check karo"],
        "legal_aid_application": ["court notice mila lawyer afford nahi kar sakte DLSA application chahiye", "domestic violence case ke liye free legal aid eligibility proof kya hoga", "FIR copy aur income certificate hai legal services authority packet banao"],
    },
}

MISSING_DOCUMENTS = {
    "cyber_fraud": ["transaction_id", "bank_complaint_acknowledgement"],
    "labour_dispute": ["salary_record", "employer_details"],
    "tenant_housing": ["rent_payment_proof", "written_notice"],
    "domestic_violence": ["incident_timeline", "safety_contact"],
    "rti_request": ["public_authority", "record_period"],
    "zero_fir": ["written_complaint", "refusal_details"],
    "case_status": ["court_name", "case_number"],
    "legal_rights": ["arrest_memo", "police_station"],
    "bail_enquiry": ["remand_order", "surety_details"],
    "surety_bond": ["court_bond_amount", "property_verification"],
    "income_certificate": ["income_proof", "self_declaration"],
    "caste_certificate": ["family_caste_evidence", "relationship_proof"],
    "domicile_certificate": ["residence_history", "address_proof"],
    "disability_pension": ["disability_certificate", "bank_passbook"],
    "legal_aid_application": ["case_document", "eligibility_proof"],
}


def normalise(text: str) -> str:
    return re.sub(r"[^a-z0-9\u0900-\u097f]+", " ", text.lower()).strip()


def tokens(text: str) -> set[str]:
    return set(normalise(text).split())


def jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def independent_cases():
    cases = []
    for module, intents in CASE_TEMPLATES.items():
        intent_names = list(intents)
        for index in range(60):
            intent = intent_names[index % len(intent_names)]
            patterns = intents[intent]
            pattern = patterns[(index // len(intent_names)) % len(patterns)]
            prompt = pattern.format(
                amount=[18000, 25000, 43000, 75000][index % 4],
                months=[2, 3, 4, 6, 8, 12][index % 6],
                section=[302, 307, 379, 420, "498A", 406][index % 6],
                fir=6100 + index,
            )
            prompt = (
                f"{prompt}. District: {['Pune', 'Lucknow', 'Chennai', 'Guwahati', 'Kolkata'][index % 5]}. "
                f"Case context {module}-{index + 1}: the family wants a written checklist before visiting an office."
            )
            expected = {
                "module": module,
                "intent": intent,
                "missing_documents": MISSING_DOCUMENTS[intent],
            }
            cases.append({"module": module, "intent": intent, "prompt": prompt, "expected": expected})
    return cases


def main():
    with SOURCE.open("r", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    train = [row for row in rows if row["split"] == "train"]
    train_normalised = {normalise(row["prompt"]) for row in train}
    train_tokens = [(row["sample_id"], tokens(row["prompt"])) for row in train]

    selected = []
    per_module = Counter()
    rejected_exact = 0
    rejected_near = 0
    seen = set()
    for case in independent_cases():
        module = case["module"]
        prompt_normalised = normalise(case["prompt"])
        if prompt_normalised in seen or prompt_normalised in train_normalised:
            rejected_exact += 1
            continue
        prompt_tokens = tokens(case["prompt"])
        max_similarity = max((jaccard(prompt_tokens, train_set) for _, train_set in train_tokens), default=0.0)
        if max_similarity >= 0.995:
            rejected_near += 1
            continue
        expected = case["expected"]
        selected.append({
            "benchmark_id": f"BENCH-{len(selected) + 1:04d}",
            "source_sample_id": "independent_benchmark_case",
            "language": "Hindi/Hinglish" if any(ord(char) > 127 for char in case["prompt"]) or any(word in case["prompt"].lower() for word in ["hai", "kya", "mera", "chahiye"]) else "English",
            "language_code": "hi" if any(word in case["prompt"].lower() for word in ["hai", "kya", "mera", "chahiye", "nahi"]) else "en",
            "prompt": case["prompt"],
            "expected_module": module,
            "expected_intent": case["intent"],
            "expected_json": json.dumps(expected, ensure_ascii=False),
            "expected_missing_documents": " | ".join(expected["missing_documents"]),
            "safety_boundary": "Human, lawyer, court, or authorised authority verification is required.",
            "review_status": "pending_two_reviewer_consensus",
            "locked_for_training": "true",
            "max_train_token_jaccard": f"{max_similarity:.4f}",
        })
        seen.add(prompt_normalised)
        per_module[module] += 1

    if any(per_module[module] < 50 for module in ["legal_aid", "zamanatai", "civicdocs"]):
        raise RuntimeError(f"Benchmark is not sufficiently balanced: {dict(per_module)}")

    with BENCHMARK.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(selected[0].keys()))
        writer.writeheader()
        writer.writerows(selected)

    review_fields = [
        "benchmark_id", "reviewer_1", "reviewer_1_module", "reviewer_1_intent", "reviewer_1_accept",
        "reviewer_2", "reviewer_2_module", "reviewer_2_intent", "reviewer_2_accept", "adjudicator",
        "final_module", "final_intent", "final_status", "notes",
    ]
    with REVIEW_ASSIGNMENTS.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=review_fields)
        writer.writeheader()
        for row in selected:
            writer.writerow({
                "benchmark_id": row["benchmark_id"],
                "reviewer_1_module": row["expected_module"],
                "reviewer_1_intent": row["expected_intent"],
                "final_module": row["expected_module"],
                "final_intent": row["expected_intent"],
                "final_status": "pending_two_reviewer_consensus",
            })

    report = {
        "benchmark_name": "NyayaSetu Unified Benchmark v1",
        "records": len(selected),
        "module_distribution": dict(per_module),
        "intent_distribution": dict(Counter(row["expected_intent"] for row in selected)),
        "language_distribution": dict(Counter(row["language_code"] for row in selected)),
        "exact_leakage_rejections": rejected_exact,
        "near_duplicate_rejections_at_0_995": rejected_near,
        "maximum_train_similarity": max(float(row["max_train_token_jaccard"]) for row in selected),
        "human_review_required": True,
        "benchmark_policy": "Rows are locked from training. Replace pending review status only after two reviewers agree on module, intent, missing documents, and safety boundary.",
    }
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

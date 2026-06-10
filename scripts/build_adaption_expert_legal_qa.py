import csv
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "adaptive_data" / "adaption_expert_legal_qa.csv"

random.seed(20260610)

LANG_VARIANTS = [
    ("en", "English", "My brother"),
    ("hi", "Hindi", "मेरा भाई"),
    ("hi", "Hindi", "मेरी बहन"),
    ("en", "English", "My father"),
    ("hi", "Hindi", "मेरे पिता"),
]

COURTS = [
    "Sessions Court",
    "District Court",
    "Magistrate Court",
    "High Court legal aid clinic",
    "District Legal Services Authority",
]

STATES = ["Uttar Pradesh", "Maharashtra", "Tamil Nadu", "Telangana", "West Bengal", "Gujarat", "Odisha", "Assam"]

SCENARIOS = [
    {
        "intent": "bail_enquiry",
        "domain": "criminal_justice",
        "law": "BNSS Sections 478, 479 and 480; CrPC Sections 437 and 439 principles where applicable",
        "urgency": "high",
        "doc": "bail_application",
        "facts": [
            "is in custody for {months} months in FIR {fir} under IPC Section {section}, and the family has only the arrest memo and FIR copy",
            "was arrested after a property dispute was converted into FIR {fir}; the family says the accused has no previous conviction",
            "has a bail hearing next week but the surety papers and medical documents are incomplete",
            "is charged under Section {section}; the family wants to know whether prolonged custody can support a bail request",
        ],
        "answer": [
            "First identify whether the offence is bailable. If it is bailable, bail is normally a right and the family should ask the advocate to move the appropriate bail application immediately.",
            "For non-bailable offences, the court has discretion. The strongest bail file should show custody duration, roots in the community, cooperation with investigation, no witness intimidation, and readiness to obey court conditions.",
            "Check whether BNSS Section 479 may be relevant for prolonged detention. The exact threshold depends on the maximum punishment and the person’s criminal history.",
            "Collect FIR copy, arrest memo, remand orders, medical records, proof of residence, ID proofs, and surety details. A lawyer should verify the final bail section and facts before filing.",
        ],
    },
    {
        "intent": "cyber_fraud",
        "domain": "digital_safety",
        "law": "National Cyber Crime Portal, 1930 helpline, IT Act and IPC/BNS fraud provisions depending on facts",
        "urgency": "high",
        "doc": "cyber_fraud_complaint",
        "facts": [
            "lost Rs {amount} through UPI after clicking a link and has transaction ID, screenshot, and bank SMS",
            "shared OTP during a courier scam and money was debited within ten minutes",
            "was cheated through a fake loan app and the app is now threatening to misuse contact list photos",
            "paid a job agency online but the company blocked the number after receiving the transfer",
        ],
        "answer": [
            "Call 1930 immediately and file a complaint on cybercrime.gov.in with transaction ID, time, bank name, UPI ID, screenshots, phone numbers, and URLs.",
            "Inform the bank in writing and request freezing or reversal support. Preserve the complaint acknowledgement number.",
            "Do not delete chats, call logs, emails, screenshots, app names, or payment proof. These become the evidence trail.",
            "If the local police refuse to assist, ask for cyber cell escalation or written acknowledgement. Legal aid can help draft a concise complaint.",
        ],
    },
    {
        "intent": "domestic_violence",
        "domain": "family_safety",
        "law": "Protection of Women from Domestic Violence Act, 2005; free legal aid through Legal Services Authorities Act",
        "urgency": "high",
        "doc": "domestic_violence_safety_plan",
        "facts": [
            "is facing violence at home and needs protection order support but is afraid to go alone to police",
            "has medical records and WhatsApp threats from in-laws but does not know how to approach a protection officer",
            "was forced out of the shared household and needs residence and maintenance guidance",
            "is worried about child safety and wants free legal aid before filing a complaint",
        ],
        "answer": [
            "If there is immediate danger, contact emergency services, police, trusted family, or a local women’s helpline first. Safety comes before paperwork.",
            "Preserve medical records, photos, messages, call recordings where lawful, witness names, address details, and dates of incidents.",
            "A protection officer, DLSA/legal aid lawyer, or women’s cell can help seek protection, residence, maintenance, custody-related safeguards, and return of essential documents.",
            "The response should not pressure the survivor to take a step that increases risk. Ask where she is currently safe and whether children are involved.",
        ],
    },
    {
        "intent": "labour_dispute",
        "domain": "economic_justice",
        "law": "Payment of Wages principles, Shops and Establishments/labour department processes, Industrial Disputes principles where applicable",
        "urgency": "medium",
        "doc": "labour_complaint",
        "facts": [
            "has not received salary for {months} months and the employer is ignoring calls despite attendance proof",
            "was removed from work without notice and final wages were not paid",
            "is a migrant worker whose contractor kept ID documents and unpaid wages",
            "has bank statements and WhatsApp duty rosters but no formal appointment letter",
        ],
        "answer": [
            "Collect appointment letter if available, salary slips, bank statements, attendance records, duty rosters, ID card, contractor details, and messages promising payment.",
            "Send a written demand for unpaid wages with dates and amount. Keep proof of delivery.",
            "Approach the Labour Commissioner, local labour office, worker helpline, or DLSA if the worker cannot afford a lawyer.",
            "If documents are missing, build the case from alternative proof such as messages, co-worker witnesses, gate register photos, and bank credits.",
        ],
    },
    {
        "intent": "tenant_housing",
        "domain": "civil_rights",
        "law": "State rent control/tenancy law, contract law principles, civil remedies for deposit recovery",
        "urgency": "medium",
        "doc": "tenant_rights_notice",
        "facts": [
            "is being forced to vacate without written notice and the landlord is refusing to return the deposit",
            "has paid rent digitally for two years but never received a written rental agreement",
            "received threats to disconnect electricity unless the family vacates immediately",
            "wants to recover deposit after leaving the house in good condition",
        ],
        "answer": [
            "Do not rely only on verbal pressure. Preserve rent receipts, bank transfers, agreement, deposit proof, electricity bills, photographs, and messages.",
            "Ask for written notice and reason for eviction. Avoid confrontation and record dates and witnesses.",
            "For deposit recovery, send a written demand with amount, date paid, date vacated, and proof of handover.",
            "Depending on the state and facts, legal aid, rent authority, consumer grievance route, or civil court notice may be appropriate.",
        ],
    },
    {
        "intent": "zero_fir",
        "domain": "police_accountability",
        "law": "Zero FIR practice, police complaint escalation, Magistrate remedy principles",
        "urgency": "high",
        "doc": "zero_fir_escalation",
        "facts": [
            "went to the police station after an assault but the officer said the incident is outside their jurisdiction",
            "has a written complaint but police are refusing to register an FIR",
            "was told to settle privately even though there are threats and medical records",
            "needs to know how to escalate refusal to register a complaint",
        ],
        "answer": [
            "Write a concise complaint with date, time, place, accused details if known, witnesses, injuries/loss, and evidence list.",
            "If police refuse due to jurisdiction, ask them to register a Zero FIR and transfer it to the appropriate station.",
            "Note the officer name, station, date, and refusal reason. Send the complaint to senior police officers by email/post if needed.",
            "If refusal continues, legal aid can help approach the Magistrate route. Keep acknowledgement proof for every submission.",
        ],
    },
    {
        "intent": "rti_request",
        "domain": "public_records",
        "law": "Right to Information Act, 2005",
        "urgency": "low",
        "doc": "rti_application",
        "facts": [
            "needs records of action taken on a police complaint and only has the diary number",
            "wants copies of government office file movement for a pension application",
            "needs certified information about whether an FIR copy was uploaded on the state portal",
            "wants inspection of records but does not know the public authority",
        ],
        "answer": [
            "Identify the exact public authority and ask for specific records, dates, file numbers, and certified copies where needed.",
            "Avoid asking questions like why an officer acted in a certain way; ask for records, orders, notes, dispatch details, and action taken reports.",
            "If no reply comes within the statutory period, file a first appeal with the appellate authority.",
            "Keep the RTI narrow so it is harder to reject as vague or burdensome.",
        ],
    },
    {
        "intent": "child_rights",
        "domain": "child_protection",
        "law": "Juvenile Justice principles, child-friendly procedure, legal aid protections",
        "urgency": "high",
        "doc": "child_rights_guidance",
        "facts": [
            "says a minor child was called to the police station without a guardian",
            "needs guidance because police want to question a school student as a witness",
            "is worried a child may be treated like an adult accused",
            "needs child welfare and legal aid contact steps",
        ],
        "answer": [
            "A child should be handled through child-sensitive procedures with guardian support and without intimidation.",
            "Record the child’s age proof, school ID, station name, officer details, call time, and reason for calling.",
            "Contact legal aid, child welfare authorities, or a qualified child-rights lawyer if questioning or detention is threatened.",
            "The safest next step is to avoid sending the child alone and insist on lawful, child-friendly procedure.",
        ],
    },
]


def prompt_for(scenario, lang, person, fact, state, court):
    return (
        f"You are a careful Indian legal-aid assistant helping an underserved citizen in {state}. "
        f"The user may not know legal terminology and may be mixing Hindi/English or regional language. "
        f"Read the facts, classify the legal issue, cite the relevant legal route or public authority, "
        f"identify evidence and missing information, and draft a practical response. Do not guarantee success. "
        f"User context: {person} {fact}. The family may need help from {court}."
    )


def completion_for(scenario, fact, state, court):
    bullets = "\n".join(f"- {line}" for line in scenario["answer"])
    return (
        f"Legal classification: {scenario['intent']}.\n"
        f"Domain: {scenario['domain']}.\n"
        f"Urgency: {scenario['urgency']}.\n"
        f"Relevant legal route: {scenario['law']}.\n"
        f"Recommended workflow/document: {scenario['doc']}.\n\n"
        f"Practical response:\n{bullets}\n\n"
        f"Follow-up questions to ask:\n"
        f"1. Which district and police station/court/authority is involved in {state}?\n"
        f"2. What documents are already available and what is missing?\n"
        f"3. Is there any deadline, hearing date, threat, detention, or safety risk?\n\n"
        f"Adaptive data note: If the model misclassifies this as a generic legal-rights query, correct the intent to "
        f"{scenario['intent']} and record the missing evidence checklist. Confidence should increase after correction.\n\n"
        f"Safety disclaimer: This is legal-aid information for preparing next steps. The final filing, notice, or court strategy "
        f"should be verified by a qualified advocate, DLSA/legal aid office, or the appropriate public authority."
    )


def main():
    rows = []
    sample_id = 1
    for scenario in SCENARIOS:
        for i in range(32):
            lang_code, lang_name, person = LANG_VARIANTS[i % len(LANG_VARIANTS)]
            state = STATES[(i + sample_id) % len(STATES)]
            court = COURTS[(i + len(scenario["intent"])) % len(COURTS)]
            fact = scenario["facts"][i % len(scenario["facts"])].format(
                months=[2, 3, 4, 6, 8, 12][i % 6],
                fir=f"FIR {3100 + sample_id}",
                section=["302", "307", "379", "420", "498A", "406"][i % 6],
                amount=["18000", "25000", "50000", "75000"][i % 4],
            )
            correction_applied = "yes" if i % 3 == 0 else "no"
            rows.append(
                {
                    "prompt": prompt_for(scenario, lang_name, person, fact, state, court),
                    "completion": completion_for(scenario, fact, state, court),
                    "language": lang_name,
                    "language_code": lang_code,
                    "legal_domain": scenario["domain"],
                    "intent": scenario["intent"],
                    "urgency": scenario["urgency"],
                    "recommended_document": scenario["doc"],
                    "feedback_rating": "5" if i % 4 else "4",
                    "correction_applied": correction_applied,
                    "confidence_before": "0.62" if correction_applied == "yes" else "0.84",
                    "confidence_after": "0.97",
                    "source": "NyayaSetu + ZamanatAI, credited to Adaption Labs Adaptive Data Track",
                }
            )
            sample_id += 1

    out = Path(__file__).resolve().parents[1] / "adaptive_data" / "adaption_expert_legal_qa.csv"
    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    avg_prompt = sum(len(row["prompt"].split()) for row in rows) / len(rows)
    avg_completion = sum(len(row["completion"].split()) for row in rows) / len(rows)
    print(f"wrote {out}")
    print(f"rows={len(rows)}")
    print(f"avg_prompt_words={avg_prompt:.1f}")
    print(f"avg_completion_words={avg_completion:.1f}")


if __name__ == "__main__":
    main()

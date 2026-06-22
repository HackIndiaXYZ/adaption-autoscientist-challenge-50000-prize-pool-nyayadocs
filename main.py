import io
import asyncio
import json
import logging
import os
import re
import uuid
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any, Optional

import pytesseract
import requests
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from groq import Groq
from langdetect import DetectorFactory, LangDetectException, detect
from PIL import Image
from pydantic import BaseModel, Field
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


load_dotenv()

ADAPTIVE_DATA_API_KEY = os.getenv("ADAPTIVE_DATA_API_KEY", "")
ADAPTIVE_DATA_ENDPOINT = "https://api.adaptionlabs.ai/v1/ingest"


def log_to_adaptive_data(
    raw_message: str,
    language: str,
    intent: str,
    entities: dict,
    output_doc_type: str,
) -> None:
    redacted_text = raw_message
    accused_name = entities.get("accused_name", "")
    fir_number = entities.get("fir_number", "")
    if accused_name:
        redacted_text = redacted_text.replace(str(accused_name), "[NAME]")
    if fir_number:
        redacted_text = redacted_text.replace(str(fir_number), "[FIR]")

    record = {
        "input_text": redacted_text,
        "input_language": language,
        "intent": intent,
        "entities": {
            k: "[REDACTED]" if k in ["accused_name", "fir_number"] else v
            for k, v in entities.items()
        },
        "output_doc_type": output_doc_type,
        "feedback": None,
        "session_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    os.makedirs("./dataset", exist_ok=True)
    with open("./dataset/interactions.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    if ADAPTIVE_DATA_API_KEY:
        try:
            requests.post(
                ADAPTIVE_DATA_ENDPOINT,
                json={"data": [record], "dataset_name": "nyayasetu-legal-dialogues-multilingual"},
                headers={"Authorization": f"Bearer {ADAPTIVE_DATA_API_KEY}"},
                timeout=3,
            )
        except Exception:
            pass


DetectorFactory.seed = 0
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nyayasetu")

# 🧠 Initialize Adaptive Learning Engine
try:
    from adaptive_learning import AdaptiveLearningEngine
    adaptive_engine = AdaptiveLearningEngine("data/nyayasetu_legal_aid.csv")
    logger.info(f"✅ Adaptive learning enabled with {len(adaptive_engine.dataset)} records")
    ADAPTIVE_LEARNING_ENABLED = True
except Exception as e:
    logger.warning(f"⚠️ Adaptive learning disabled: {e}")
    adaptive_engine = None
    ADAPTIVE_LEARNING_ENABLED = False

app = FastAPI(title="NyayaSetu WhatsApp Bot")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
DATASET_PATH = Path("dataset") / "interactions.jsonl"
Path("outputs").mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory="outputs"), name="static")


class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, data: dict):
        msg = json.dumps(data)
        for ws in self.active[:]:
            try:
                await ws.send_text(msg)
            except Exception:
                self.disconnect(ws)


manager = ConnectionManager()

NLU_KEYS = [
    "intent",
    "accused_name",
    "fir_number",
    "police_station",
    "section_charged",
    "time_in_custody_days",
    "relationship_to_accused",
    "language_of_message",
]

INTENT_MAP = {
    "bail": "bail_enquiry",
    "surety": "surety_bond",
    "status": "case_status",
    "rights": "legal_rights",
}

GROQ_NLU_SYSTEM_PROMPT = """You are a legal aid assistant for Indian courts. Extract structured information from messages sent by families of prisoners.

Return ONLY valid JSON with keys:

intent (bail_enquiry/surety_bond/case_status/legal_rights),
accused_name,
fir_number,
police_station,
section_charged,
time_in_custody_days,
relationship_to_accused,
language_of_message.

If information is not present, use null.

Respond only with JSON, no markdown, no explanations, no code blocks."""

GROQ_GROUNDS_SYSTEM_PROMPT = """You are a legal aid drafting assistant for Indian bail applications.
Return ONLY a valid JSON array of 5 to 7 strings.
Generate specific, professional, legally relevant grounds for bail based on the eligibility data and case facts.
Cite applicable BNSS/CrPC provisions whenever appropriate.
Avoid generic statements.
Do not guarantee bail."""

KEYWORDS = {
    "surety": ["surety", "bond", "zamanat", "ज़मानतनामा"],
    "bail": ["bail", "jamani", "zamaanat", "जमानत", "ज़मानत", "जमानत"],
    "status": ["case", "FIR", "hearing", "मुकदमा"],
    "rights": ["rights", "lawyer", "advocate", "अधिकार"],
}

LANGUAGE_NAMES = {
    "hi": "Hindi",
    "bn": "Bengali",
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
    "ml": "Malayalam",
    "mr": "Marathi",
    "gu": "Gujarati",
    "pa": "Punjabi",
    "or": "Odia",
    "as": "Assamese",
    "ur": "Urdu",
    "en": "English",
    "mai": "Maithili",
    "sat": "Santali",
    "kok": "Konkani",
    "mni": "Manipuri",
    "brx": "Bodo",
    "doi": "Dogri",
    "ne": "Nepali",
    "ks": "Kashmiri",
    "sd": "Sindhi",
}

REPLY_TEMPLATES = {
    "bail_enquiry_eligible": "Your case has been reviewed. {accused_name} appears eligible for bail under BNSS Section {bnss_section}. Reason: {reason}. Your bail application PDF is ready. Please download and give to your advocate.",
    "bail_enquiry_not_eligible": "Your case has been reviewed. {accused_name} is not yet eligible for automatic bail. Reason: {reason}. You may still apply for bail under Section 480 BNSS — your advocate can argue your case.",
    "surety_bond": "To generate the surety bond, please send a clear photo of a property document (Aadhaar card, land record, or electricity bill of the surety person).",
    "case_status": "Please send the FIR number and police station name to check case status.",
    "legal_rights": "Under Indian law, every accused person has the right to: 1) Know the charges against them, 2) Consult a lawyer before questioning, 3) A bail hearing within 24 hours of arrest, 4) Free legal aid if they cannot afford a lawyer (Legal Services Authority).",
    "labour_dispute": "This looks like a labour or salary dispute. Keep salary slips, appointment letter, bank statements, attendance records, and WhatsApp/email promises. You can file a complaint with the Labour Commissioner or District Legal Services Authority for free legal help.",
    "tenant_housing": "This looks like a tenant or housing issue. Do not leave only on verbal pressure. Save rent receipts, agreement, notices, and messages. Ask for written notice and contact local legal aid or the rent authority/civil court process in your district.",
    "cyber_fraud": "This looks like a cyber fraud complaint. Immediately call 1930, file a report at cybercrime.gov.in, save transaction IDs, screenshots, bank messages, UPI IDs, phone numbers, and request your bank to freeze or dispute the transaction.",
    "consumer_complaint": "This looks like a consumer complaint. Keep invoice, warranty card, photos/videos of the defect, service-center replies, and payment proof. You can first send a written complaint to the seller/company, then file on the consumer helpline or consumer commission.",
    "domestic_violence": "This looks like a domestic violence safety issue. If there is immediate danger, contact emergency services or local police. Save medical records, photos, messages, and witness details. You can seek protection, residence, maintenance, and free legal aid through DLSA or a protection officer.",
    "rti_request": "This looks like an RTI or public-records request. Identify the public authority, ask for specific records, dates, and file numbers, and keep the request narrow. If there is no reply within the legal timeline, you can file a first appeal.",
    "fir_copy": "This looks like a request for an FIR copy. Ask the police station for the FIR number and copy. If refused, note the officer name/date, approach senior police officers, use the state police portal where available, or seek help from legal aid.",
    "zero_fir": "This looks like a police refusal or Zero FIR issue. If the incident happened outside the police station area, police can still register a Zero FIR and transfer it. Keep proof of refusal and escalate to senior police officers or a Magistrate/legal aid.",
    "accident_compensation": "This looks like an accident compensation matter. Preserve FIR, MLC/medical papers, insurance details, vehicle number, photos, witness names, and hospital bills. A Motor Accident Claims Tribunal claim may be possible.",
    "legal_notice": "This looks like a legal notice issue. Do not ignore it. Save the notice envelope, date of receipt, loan or contract papers, payment proof, and any earlier communication. A short written reply through an advocate or legal aid may be needed.",
    "nri_property": "This looks like an NRI or property-document issue. Collect property papers, identity proof, relationship proof, and draft a specific Power of Attorney. Get local lawyer verification before signing or notarising/consular attestation.",
    "document_translation": "This looks like a court-document translation need. Upload or share the notice text clearly. Keep the original, translated copy, case number, court name, and deadline. For filing, use a certified translation if the court requires it.",
    "child_rights": "This looks like a child-rights or minor-related police issue. A child should be handled through child-friendly procedures. Note the police station, officer name, time, and guardian details, and contact child welfare/legal aid immediately.",
    "elder_property": "This looks like an elderly person property or financial abuse issue. Preserve property papers, bank records, messages, witness details, and medical/age proof. Legal aid can help with police complaint, maintenance, or civil protection remedies.",
    "disability_benefits": "This looks like a disability benefit or pension issue. Keep disability certificate, pension ID, bank passbook, rejection/stoppage notice, and prior applications. You can file an RTI, grievance, or appeal with legal aid support.",
    "caste_discrimination": "This looks like a caste discrimination complaint. Preserve witness names, messages, videos, location/date details, and any threats. Contact police/legal aid urgently; specific protections may apply depending on facts.",
    "migrant_worker": "This looks like a migrant-worker legal issue. Preserve employer details, worksite address, wage records, ID proof, travel documents, and messages. Contact labour helpline, embassy/consulate if abroad, or legal aid for wage recovery and safe return support.",
    "refugee_detention": "This looks like a detention or refugee-family issue. Record the detention notice details, authority name, date, place, identity documents, and family contacts. Seek urgent help from legal aid or a qualified rights organisation.",
    "default": "I received your message. Please send details: accused name, FIR number, police station, and section charged.",
}

CIVIC_TOPIC_KEYWORDS = {
    "domestic_violence": ["domestic violence", "protection order", "violence", "maar", "pitai", "wife beating", "घरेलू", "हिंसा"],
    "cyber_fraud": ["cyber", "upi", "fraud", "scam", "online fraud", "1930", "cybercrime", "otp", "bank fraud"],
    "labour_dispute": ["salary", "pagar", "wage", "employer", "terminated", "labour", "labor", "worker", "payment not", "कामगार", "वेतन"],
    "tenant_housing": ["landlord", "tenant", "rent", "deposit", "evict", "vacate", "house owner", "मकान मालिक"],
    "consumer_complaint": ["consumer", "warranty", "defective", "refund", "product", "seller", "bill", "invoice"],
    "rti_request": ["rti", "public records", "information request", "सूचना का अधिकार"],
    "zero_fir": ["zero fir", "refused to register", "police refused", "complaint refused", "FIR nahi likh"],
    "fir_copy": ["fir copy", "copy of fir", "certified copy", "FIR की copy", "FIR copy"],
    "accident_compensation": ["accident", "compensation", "insurance claim", "vehicle theft", "motor accident", "injured", "construction site", "worksite", "medical bills", "hospital bill"],
    "legal_notice": ["legal notice", "loan default", "notice mila", "demand notice"],
    "nri_property": ["nri", "power of attorney", "passport withheld", "visa agent", "property case in india", "abroad"],
    "document_translation": ["translation", "translate", "court notice from", "hindi to english"],
    "child_rights": ["minor child", "child", "juvenile", "called to police station"],
    "elder_property": ["elderly", "senior citizen", "parent property", "property fraud"],
    "disability_benefits": ["disability", "pension stopped", "disability pension", "benefit stopped"],
    "caste_discrimination": ["caste", "discrimination", "sc st", "atrocity"],
    "migrant_worker": ["migrant worker", "passport withheld", "employer abroad", "construction site", "worksite"],
    "refugee_detention": ["refugee", "detention notice", "detained family", "asylum"],
}

CIVIC_TOPIC_PRIORITY = [
    "domestic_violence",
    "cyber_fraud",
    "accident_compensation",
    "disability_benefits",
    "migrant_worker",
    "refugee_detention",
    "child_rights",
    "elder_property",
    "caste_discrimination",
    "tenant_housing",
    "consumer_complaint",
    "labour_dispute",
    "nri_property",
    "document_translation",
    "legal_notice",
    "zero_fir",
    "fir_copy",
    "rti_request",
]


class BailCheckRequest(BaseModel):
    section: str
    months: int


class BailPdfRequest(BaseModel):
    accused_name: str
    fir_number: str
    police_station: str
    section: str
    months_in_custody: int
    court_name: str


class SuretyBondRequest(BaseModel):
    accused: dict
    surety: dict
    property: dict


class CivicAssessmentRequest(BaseModel):
    service_type: str
    applicant_data: dict
    available_documents: list[str] = Field(default_factory=list)
    extracted_documents: list[dict] = Field(default_factory=list)


class CivicPacketRequest(CivicAssessmentRequest):
    preferred_language: str = "en"
    declaration: str = "I confirm that the information supplied for this application-preparation packet is accurate to the best of my knowledge."


class CivicFeedbackRequest(BaseModel):
    service_type: str
    field_name: str
    old_value: str = ""
    corrected_value: str
    language: str = "en"
    document_type: str = "unknown"


CIVICDOCS_SERVICES = {
    "income_certificate": {
        "name": "Income Certificate Application",
        "description": "Prepare an income-certificate application packet for the authorised state revenue authority.",
        "issuing_authority": "State Revenue Department / Tehsildar",
        "required_fields": ["applicant_name", "date_of_birth", "address", "district", "state", "annual_family_income", "purpose"],
        "required_documents": ["identity_proof", "address_proof", "income_proof", "passport_photo", "self_declaration"],
        "conditional_documents": ["salary_slip", "bank_statement", "employer_certificate", "ration_card"],
    },
    "caste_certificate": {
        "name": "Caste Certificate Application",
        "description": "Prepare a caste-certificate application packet with lineage and residence evidence for verification by the competent authority.",
        "issuing_authority": "State Revenue / Social Justice Department",
        "required_fields": ["applicant_name", "date_of_birth", "address", "district", "state", "category", "caste_name", "father_or_guardian_name"],
        "required_documents": ["identity_proof", "address_proof", "birth_or_school_record", "family_caste_evidence", "passport_photo", "self_declaration"],
        "conditional_documents": ["father_caste_certificate", "relative_caste_certificate", "migration_record", "genealogy_affidavit"],
    },
    "domicile_certificate": {
        "name": "Domicile / Residence Certificate Application",
        "description": "Prepare a residence-evidence packet for the competent state or district authority.",
        "issuing_authority": "State Revenue Department / District Administration",
        "required_fields": ["applicant_name", "date_of_birth", "current_address", "district", "state", "years_of_residence", "purpose"],
        "required_documents": ["identity_proof", "address_proof", "residence_history", "passport_photo", "self_declaration"],
        "conditional_documents": ["school_record", "property_tax_receipt", "rent_agreement", "electricity_bill", "parent_domicile_certificate"],
    },
    "disability_pension": {
        "name": "Disability Pension / Benefit Application",
        "description": "Prepare a disability-benefit application packet and identify missing medical and banking evidence.",
        "issuing_authority": "State Social Welfare Department",
        "required_fields": ["applicant_name", "date_of_birth", "address", "district", "state", "disability_type", "disability_percentage", "bank_account_last4"],
        "required_documents": ["identity_proof", "address_proof", "disability_certificate", "bank_passbook", "passport_photo"],
        "conditional_documents": ["udid_card", "income_certificate", "medical_board_report", "age_proof"],
    },
    "legal_aid_application": {
        "name": "Free Legal Aid Application",
        "description": "Prepare an application to the Legal Services Authority with case facts and eligibility evidence.",
        "issuing_authority": "District / State Legal Services Authority",
        "required_fields": ["applicant_name", "address", "district", "state", "legal_issue", "opposite_party", "case_or_fir_number", "income_or_eligibility_basis"],
        "required_documents": ["identity_proof", "address_proof", "case_document", "income_or_category_proof"],
        "conditional_documents": ["fir_copy", "court_notice", "medical_record", "domestic_violence_record", "custody_document"],
    },
}


class AppConfig(BaseModel):
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"


def get_config() -> AppConfig:
    return AppConfig(
        groq_api_key=os.getenv("GROQ_API_KEY", ""),
        groq_model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
    )


class LLMService:
    def __init__(self, config: AppConfig):
        self.config = config
        self.client = Groq(api_key=config.groq_api_key) if config.groq_api_key else None

    def classify_message(self, message: str, language: str) -> dict:
        if self.client is None:
            return rule_based_extraction(message, language)

        try:
            response = self.client.chat.completions.create(
                model=self.config.groq_model,
                temperature=0,
                messages=[
                    {"role": "system", "content": GROQ_NLU_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Language: {language}\nMessage: {message}"},
                ],
            )
            content = response.choices[0].message.content or "{}"
            parsed = parse_json_safely(content)
            return validate_nlu_result(parsed, message, language)
        except Exception as error:
            logger.warning("Groq classification failed; using rule-based fallback: %s", error)
            return rule_based_extraction(message, language)

    def generate_bail_grounds(self, eligibility_data: dict, case_facts: str) -> list[str]:
        if self.client is None:
            return template_bail_grounds(eligibility_data, case_facts)

        try:
            response = self.client.chat.completions.create(
                model=self.config.groq_model,
                temperature=0.2,
                messages=[
                    {"role": "system", "content": GROQ_GROUNDS_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": json.dumps(
                            {"eligibility_data": eligibility_data, "case_facts": case_facts},
                            ensure_ascii=False,
                        ),
                    },
                ],
            )
            content = response.choices[0].message.content or "[]"
            parsed = parse_json_safely(content)
            if not isinstance(parsed, list):
                raise ValueError("Groq grounds response was not a JSON array")
            grounds = [str(item).strip() for item in parsed if str(item).strip()]
            if not 5 <= len(grounds) <= 7:
                raise ValueError("Groq grounds response did not contain 5 to 7 grounds")
            return grounds
        except Exception as error:
            logger.warning("Groq bail grounds failed; using template fallback: %s", error)
            return template_bail_grounds(eligibility_data, case_facts)


def get_llm_service(config: AppConfig = Depends(get_config)) -> LLMService:
    return LLMService(config)


def detect_message_language(body: str) -> str:
    text = body.strip()
    if not text:
        return "unknown"
    try:
        return detect(text)
    except LangDetectException:
        return "unknown"


def classify_intent(body: str) -> str:
    text = body.lower()
    for intent, keywords in KEYWORDS.items():
        if any(keyword.lower() in text for keyword in keywords):
            return intent
    return "rights"


LANGDETECT_TO_INDICTRANS2 = {
    "as": "asm_Beng",
    "bn": "ben_Beng",
    "brx": "brx_Deva",
    "doi": "doi_Deva",
    "en": "eng_Latn",
    "gom": "gom_Deva",
    "gu": "guj_Gujr",
    "hi": "hin_Deva",
    "kn": "kan_Knda",
    "ks": "kas_Arab",
    "mai": "mai_Deva",
    "ml": "mal_Mlym",
    "mni": "mni_Beng",
    "mr": "mar_Deva",
    "ne": "npi_Deva",
    "or": "ory_Orya",
    "pa": "pan_Guru",
    "sa": "san_Deva",
    "sat": "sat_Olck",
    "sd": "snd_Arab",
    "ta": "tam_Taml",
    "te": "tel_Telu",
    "ur": "urd_Arab",
}

_INDICTRANS2_TRANSLATOR = None


class IndicTrans2Translator:
    def __init__(self) -> None:
        self.model_name = os.getenv(
            "INDICTRANS2_EN_INDIC_MODEL",
            "ai4bharat/indictrans2-en-indic-dist-200M",
        )
        self.device = "cpu"
        self.model = None
        self.tokenizer = None
        self.processor = None
        self.load_failed = False

    def load(self) -> bool:
        if self.model is not None and self.tokenizer is not None and self.processor is not None:
            return True
        if self.load_failed:
            return False
        try:
            import torch
            from IndicTransToolkit.processor import IndicProcessor
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            hf_token = os.getenv("HF_TOKEN") or None
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                token=hf_token,
            )
            self.model = AutoModelForSeq2SeqLM.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                low_cpu_mem_usage=True,
                token=hf_token,
            )
            self.model = self.model.to(self.device)
            self.model.eval()
            self.processor = IndicProcessor(inference=True)
            return True
        except Exception as error:
            logger.warning("IndicTrans2 unavailable; returning English fallback: %s", error)
            self.load_failed = True
            self.model = None
            self.tokenizer = None
            self.processor = None
            return False

    def translate(self, text: str, target_lang: str) -> str:
        target_code = LANGDETECT_TO_INDICTRANS2.get((target_lang or "").lower())
        if not text or not target_code or target_code == "eng_Latn":
            return text
        if not self.load():
            return text
        try:
            import torch

            batch = self.processor.preprocess_batch(
                [text],
                src_lang="eng_Latn",
                tgt_lang=target_code,
            )
            inputs = self.tokenizer(
                batch,
                truncation=True,
                padding="longest",
                return_tensors="pt",
                return_attention_mask=True,
            ).to(self.device)
            with torch.no_grad():
                generated_tokens = self.model.generate(
                    **inputs,
                    use_cache=True,
                    min_length=0,
                    max_length=256,
                    num_beams=5,
                    num_return_sequences=1,
                )
            decoded = self.tokenizer.batch_decode(
                generated_tokens,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=True,
            )
            translated = self.processor.postprocess_batch(decoded, lang=target_code)
            return translated[0] if translated else text
        except Exception as error:
            logger.warning("IndicTrans2 translation failed; returning English fallback: %s", error)
            return text


def get_indictrans2_translator() -> IndicTrans2Translator:
    global _INDICTRANS2_TRANSLATOR
    if _INDICTRANS2_TRANSLATOR is None:
        _INDICTRANS2_TRANSLATOR = IndicTrans2Translator()
    return _INDICTRANS2_TRANSLATOR


def translate_with_indictrans2(text: str, target_lang: str) -> str:
    return get_indictrans2_translator().translate(text, target_lang)


def send_whatsapp_reply(to_number: str, body: str, media_url: str = None) -> bool:
    try:
        from twilio.rest import Client

        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        whatsapp_number = os.getenv("TWILIO_WHATSAPP_NUMBER", "")
        missing_values = {"", "none", "null"}
        if (
            not account_sid
            or not auth_token
            or not whatsapp_number
            or account_sid.strip().lower() in missing_values
            or auth_token.strip().lower() in missing_values
            or whatsapp_number.strip().lower() in missing_values
        ):
            print("Twilio error: missing Twilio credentials")
            return False
        client = Client(account_sid, auth_token)
        from_number = "whatsapp:" + whatsapp_number
        if not to_number.startswith("whatsapp:"):
            to_number = "whatsapp:" + to_number
        msg_params = {"from_": from_number, "to": to_number, "body": body}
        if media_url:
            msg_params["media_url"] = [media_url]
        client.messages.create(**msg_params)
        return True
    except Exception as e:
        print(f"Twilio error: {e}")
        return False


def parse_json_safely(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"(\{.*\}|\[.*\])", text, flags=re.DOTALL)
        if match:
            return json.loads(match.group(1))
        repaired = text.strip().strip("`")
        repaired = re.sub(r"^json", "", repaired, flags=re.IGNORECASE).strip()
        return json.loads(repaired)


def validate_nlu_result(result: Any, message: str, language: str) -> dict:
    if not isinstance(result, dict):
        return rule_based_extraction(message, language)

    fallback = rule_based_extraction(message, language)
    validated = {}
    for key in NLU_KEYS:
        validated[key] = result.get(key)

    if validated["intent"] not in {"bail_enquiry", "surety_bond", "case_status", "legal_rights"}:
        validated["intent"] = fallback["intent"]

    for key in NLU_KEYS:
        if key not in {"intent"} and key not in result:
            validated[key] = fallback.get(key)

    validated["language_of_message"] = validated["language_of_message"] or language
    return validated


def rule_based_extraction(message: str, language: str) -> dict:
    intent = INTENT_MAP[classify_intent(message)]
    fir_number = extract_first_match(message, r"\bFIR\s*(?:No\.?|Number|#|:)?\s*([A-Za-z0-9/-]+)")
    police_station = extract_first_match(
        message,
        r"([A-Za-z\u0900-\u097F ]{2,50})\s+(?:police station|PS|थाना)\b",
    ) or extract_first_match(
        message,
        r"(?:police station|PS|थाना)\s*:?\s*([A-Za-z\u0900-\u097F ]{2,50})",
    )
    if police_station:
        police_station = re.sub(r"^(?:at|in)\s+", "", police_station, flags=re.IGNORECASE)
    section_charged = extract_first_match(message, r"(?:section|धारा)\s*([0-9]{2,3}[A-Za-z]?)")
    accused_name = extract_first_match(message, r"(?:accused|name|आरोपी|नाम)\s*:?\s*([A-Za-z\u0900-\u097F ]{2,50})")
    time_in_custody_days = extract_custody_days(message)

    return {
        "intent": intent,
        "accused_name": accused_name,
        "fir_number": fir_number,
        "police_station": police_station,
        "section_charged": section_charged,
        "time_in_custody_days": time_in_custody_days,
        "relationship_to_accused": None,
        "language_of_message": language,
    }


def extract_first_match(text: str, pattern: str) -> Optional[str]:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    return match.group(1).strip() if match else None


def extract_custody_days(text: str) -> Optional[int]:
    match = re.search(
        r"(\d+)\s*(day|days|month|months|year|years|दिन|महीने|माह|साल)",
        text,
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    amount = int(match.group(1))
    unit = match.group(2).lower()
    if unit in {"month", "months", "महीने", "माह"}:
        return amount * 30
    if unit in {"year", "years", "साल"}:
        return amount * 365
    return amount


def template_bail_grounds(eligibility_data: dict, case_facts: str) -> list[str]:
    bnss_section = eligibility_data.get("bnss_section", "480")
    reason = eligibility_data.get("reason", "The applicant seeks bail under applicable law.")
    return [
        f"The bail request is supported by the eligibility assessment: {reason}",
        f"The application may be considered under BNSS Section {bnss_section} and corresponding CrPC bail principles.",
        "The applicant undertakes to appear before the court on every date fixed for hearing.",
        "The applicant undertakes not to tamper with evidence or influence witnesses.",
        "The applicant is willing to comply with surety, attendance, and any other conditions imposed by the court.",
    ]


def classify_civic_topic(message: str, base_intent: str) -> str:
    text = (message or "").lower()
    protected_intents = {"bail_enquiry", "surety_bond"}
    if base_intent in protected_intents:
        return base_intent

    if base_intent == "case_status" and any(
        phrase in text
        for phrase in [
            "case status",
            "case date",
            "hearing date",
            "next hearing",
            "court date",
            "mukadma",
            "मुकदमा",
        ]
    ):
        return base_intent

    for topic in CIVIC_TOPIC_PRIORITY:
        keywords = CIVIC_TOPIC_KEYWORDS[topic]
        if any(keyword.lower() in text for keyword in keywords):
            return topic

    return base_intent


def classify_with_groq(message: str, language: str) -> dict:
    """Enhanced classification with adaptive learning"""
    service = LLMService(get_config())
    result = service.classify_message(message, language)
    
    # 🧠 Apply adaptive corrections if enabled
    if ADAPTIVE_LEARNING_ENABLED and adaptive_engine:
        confidence = result.get('confidence', 0.5)
        correction = adaptive_engine.suggest_intent_correction(
            message, 
            result['intent'], 
            confidence
        )
        
        if correction:
            logger.info(
                f"🔄 Adaptive correction: {result['intent']} → "
                f"{correction['suggested_intent']} (confidence: {confidence:.2f} → {correction['confidence']:.2f})"
            )
            result['intent'] = correction['suggested_intent']
            result['confidence'] = correction['confidence']
            result['adaptive_correction_applied'] = True
        
        # Log interaction for future learning
        adaptive_engine.log_interaction(
            message, 
            result['intent'], 
            language, 
            confidence
        )
    
    return result


def generate_bail_grounds_with_groq(eligibility_data: dict, case_facts: str) -> list[str]:
    service = LLMService(get_config())
    return service.generate_bail_grounds(eligibility_data, case_facts)


def check_bail_eligibility(section: str, time_in_custody_months: int) -> dict:
    OFFENCES = {
        "302": {"name": "Murder", "max_years": 99, "bailable": False},
        "307": {"name": "Attempt to murder", "max_years": 10, "bailable": False},
        "376": {"name": "Rape", "max_years": 10, "bailable": False},
        "379": {"name": "Theft", "max_years": 3, "bailable": True},
        "420": {"name": "Cheating", "max_years": 7, "bailable": False},
        "498A": {"name": "Cruelty to wife", "max_years": 3, "bailable": False},
        "304B": {"name": "Dowry death", "max_years": 7, "bailable": False},
        "406": {"name": "Criminal breach of trust", "max_years": 3, "bailable": False},
    }

    clean_section = section.strip().upper()
    offence = OFFENCES.get(clean_section)

    if offence is None:
        return {"eligible": False, "reason": "Section not found", "bnss_section": "480"}

    if offence["bailable"]:
        return {
            "eligible": True,
            "reason": "Bailable offence — bail is a right",
            "bnss_section": "478",
        }

    max_years = offence["max_years"]
    threshold_months = max_years * 12 / 3

    if time_in_custody_months >= threshold_months:
        return {
            "eligible": True,
            "reason": "1/3 sentence served — mandatory bail consideration under BNSS Section 479",
            "bnss_section": "479",
        }

    return {
        "eligible": False,
        "reason": f"In custody {time_in_custody_months} months. Need {int(max_years * 12 / 3)} months for Section 479",
        "bnss_section": "480",
    }


def generate_bail_pdf(data: dict) -> bytes:
    buffer = BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()

    story = [
        Paragraph(f"IN THE COURT OF {data['court_name']}", styles["Heading1"]),
        Spacer(1, 12),
        Paragraph(f"APPLICATION FOR BAIL UNDER {data['bail_section']}", styles["Heading2"]),
        Spacer(1, 12),
        Paragraph(f"ACCUSED: {data['accused_name']}", styles["Normal"]),
        Spacer(1, 12),
        Paragraph(
            f"FIR NO: {data['fir_number']} | POLICE STATION: {data['police_station']}",
            styles["Normal"],
        ),
        Spacer(1, 12),
        Paragraph(f"SECTION CHARGED: {data['section']}", styles["Normal"]),
        Spacer(1, 12),
        Paragraph("GROUNDS FOR BAIL:", styles["Heading2"]),
        Spacer(1, 12),
    ]

    for index, ground in enumerate(data["grounds"], start=1):
        story.append(Paragraph(f"{index}. {ground}", styles["Normal"]))
        story.append(Spacer(1, 12))

    story.extend(
        [
            Paragraph("PRAYER: It is therefore prayed that bail be granted.", styles["Normal"]),
            Spacer(1, 12),
            Paragraph("Generated by NyayaSetu AI Legal Aid — nyayasetu.in", styles["Italic"]),
        ]
    )

    document.build(story)
    return buffer.getvalue()


def build_bail_grounds(eligibility: dict) -> list[str]:
    return template_bail_grounds(eligibility, "")


def safe_pdf_filename(fir_number: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", fir_number.strip())
    return f"{cleaned or 'bail_application'}.pdf"


def log_interaction(data: dict) -> None:
    record = dict(data)
    if record.get("accused_name"):
        record["accused_name"] = "[NAME]"
    if record.get("fir_number"):
        record["fir_number"] = "[FIR]"
    record["timestamp"] = datetime.now(timezone.utc).isoformat()
    record["session_id"] = str(uuid.uuid4())

    DATASET_PATH.parent.mkdir(exist_ok=True)
    with DATASET_PATH.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")


def build_english_reply(intent: str, classification: dict) -> str:
    if intent == "bail_enquiry":
        section = str(classification.get("section_charged") or "")
        custody_days = parse_int_value(classification.get("time_in_custody_days")) or 0
        months_in_custody = int(custody_days / 30) if custody_days else 0
        eligibility = check_bail_eligibility(section, months_in_custody)
        accused_name = classification.get("accused_name") or "The accused"
        template_key = "bail_enquiry_eligible" if eligibility["eligible"] else "bail_enquiry_not_eligible"
        return REPLY_TEMPLATES[template_key].format(
            accused_name=accused_name,
            bnss_section=eligibility["bnss_section"],
            reason=eligibility["reason"],
        )

    if intent in REPLY_TEMPLATES:
        return REPLY_TEMPLATES[intent]

    return REPLY_TEMPLATES["default"]


def output_doc_type_for_intent(intent: str) -> str:
    if intent == "bail_enquiry":
        return "bail_application"
    if intent == "surety_bond":
        return "surety_bond"
    if intent == "case_status":
        return "case_status"
    if intent == "legal_rights":
        return "legal_rights"
    civic_doc_types = {
        "labour_dispute": "labour_complaint_checklist",
        "tenant_housing": "tenant_rights_checklist",
        "cyber_fraud": "cyber_fraud_complaint_checklist",
        "consumer_complaint": "consumer_complaint_checklist",
        "domestic_violence": "domestic_violence_safety_checklist",
        "rti_request": "rti_request_checklist",
        "fir_copy": "fir_copy_request",
        "zero_fir": "zero_fir_guidance",
        "accident_compensation": "accident_compensation_checklist",
        "legal_notice": "legal_notice_response_checklist",
        "nri_property": "nri_property_document_checklist",
        "document_translation": "court_document_translation_request",
        "child_rights": "child_rights_guidance",
        "elder_property": "elder_property_protection_checklist",
        "disability_benefits": "disability_benefits_appeal_checklist",
        "caste_discrimination": "caste_discrimination_complaint_checklist",
        "migrant_worker": "migrant_worker_legal_aid_checklist",
        "refugee_detention": "detention_notice_legal_aid_checklist",
    }
    if intent in civic_doc_types:
        return civic_doc_types[intent]
    return "message_reply"


def parse_int_value(value) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    match = re.search(r"\d+", str(value))
    return int(match.group(0)) if match else None


def generate_webhook_bail_pdf(classification: dict, llm_service: LLMService) -> tuple[str, str]:
    fir_number = str(classification.get("fir_number") or "bail_application")
    section = str(classification.get("section_charged") or "")
    custody_days = parse_int_value(classification.get("time_in_custody_days")) or 0
    months_in_custody = int(custody_days / 30) if custody_days else 0
    eligibility = check_bail_eligibility(section, months_in_custody)
    accused_name = str(classification.get("accused_name") or "The accused")
    police_station = str(classification.get("police_station") or "")
    case_facts = (
        f"Accused {accused_name}, FIR {fir_number}, Police Station {police_station}, "
        f"Section {section}, Custody {months_in_custody} months."
    )
    pdf_data = {
        "accused_name": accused_name,
        "fir_number": fir_number,
        "police_station": police_station,
        "section": section,
        "court_name": "Honourable Court",
        "bail_section": f"BNSS Section {eligibility['bnss_section']}",
        "grounds": llm_service.generate_bail_grounds(eligibility, case_facts),
    }
    pdf_bytes = generate_bail_pdf(pdf_data)
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    pdf_path = output_dir / f"{fir_number}.pdf"
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_path.write_bytes(pdf_bytes)
    return fir_number, str(pdf_path)


def extract_property_text(image_bytes: bytes) -> dict:
    image = Image.open(io.BytesIO(image_bytes))
    try:
        raw_text = pytesseract.image_to_string(image)
    except pytesseract.TesseractNotFoundError:
        raw_text = ""

    def find_line_value(pattern: str) -> str:
        match = re.search(pattern, raw_text, flags=re.IGNORECASE | re.MULTILINE)
        if not match:
            return ""
        return match.group(1).strip()

    owner_name = find_line_value(r"^\s*(?:Name|Owner)\s*:\s*(.+)$")
    property_address = find_line_value(r"^\s*(?:Address|Plot|Survey)\b\s*:?\s*(.+)$")
    district = find_line_value(r"^\s*District\s*:\s*(.+)$")
    state = find_line_value(r"^\s*State\s*:\s*(.+)$")

    return {
        "owner_name": owner_name,
        "property_address": property_address,
        "district": district,
        "state": state,
        "raw_text": raw_text,
    }


def _ocr_text(image_bytes: bytes) -> str:
    image = Image.open(io.BytesIO(image_bytes))
    try:
        return pytesseract.image_to_string(image)
    except pytesseract.TesseractNotFoundError:
        logger.warning("Tesseract is not installed; CivicDocs OCR returned an empty result")
        return ""


def _field_from_text(text: str, patterns: list[str]) -> tuple[str, float]:
    for index, pattern in enumerate(patterns):
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            value = re.sub(r"\s+", " ", match.group(1)).strip(" :-\n\t")
            if value:
                return value[:160], round(max(0.62, 0.94 - index * 0.06), 2)
    return "", 0.0


def extract_civic_document_fields(image_bytes: bytes, document_type: str = "auto") -> dict:
    raw_text = _ocr_text(image_bytes)
    field_patterns = {
        "applicant_name": [
            r"^(?:Name|Applicant Name|Holder Name)\s*[:\-]\s*(.+)$",
            r"^(?:नाम|आवेदक का नाम)\s*[:\-]\s*(.+)$",
        ],
        "father_or_guardian_name": [
            r"^(?:Father(?:'s)? Name|Guardian Name|S/O|D/O|W/O)\s*[:\-]?\s*(.+)$",
            r"^(?:पिता का नाम|अभिभावक का नाम)\s*[:\-]\s*(.+)$",
        ],
        "date_of_birth": [
            r"(?:Date of Birth|DOB|जन्म तिथि)\s*[:\-]?\s*([0-3]?\d[\/\-.][01]?\d[\/\-.](?:19|20)\d{2})",
        ],
        "address": [
            r"^(?:Address|Permanent Address|Residential Address|पता)\s*[:\-]\s*(.+)$",
        ],
        "district": [r"^(?:District|जिला)\s*[:\-]\s*(.+)$"],
        "state": [r"^(?:State|राज्य)\s*[:\-]\s*(.+)$"],
        "annual_family_income": [
            r"(?:Annual(?: Family)? Income|Total Annual Income|वार्षिक आय)\s*[:\-]?\s*(?:Rs\.?|INR|₹)?\s*([\d,]+)",
        ],
        "caste_name": [r"^(?:Caste|जाति)\s*[:\-]\s*(.+)$"],
        "category": [r"^(?:Category|Class|वर्ग)\s*[:\-]\s*(SC|ST|OBC|EWS|General|सामान्य|अनुसूचित.+)$"],
        "disability_type": [r"^(?:Disability Type|Type of Disability|दिव्यांगता का प्रकार)\s*[:\-]\s*(.+)$"],
        "disability_percentage": [r"(?:Disability Percentage|Percentage of Disability|दिव्यांगता प्रतिशत)\s*[:\-]?\s*(\d{1,3})\s*%?"],
        "certificate_number": [r"(?:Certificate No\.?|Certificate Number|प्रमाण पत्र संख्या)\s*[:\-]?\s*([A-Za-z0-9\/-]+)"],
        "aadhaar_last4": [r"(?:Aadhaar|आधार)(?: Number| No\.?)?\s*[:\-]?\s*(?:X{4}[ -]?){2}([0-9]{4})", r"\b\d{4}[ -]\d{4}[ -](\d{4})\b"],
        "bank_account_last4": [r"(?:Account No\.?|A/C No\.?|खाता संख्या)\s*[:\-]?\s*(?:X+|\*+)?([0-9]{4})\b"],
        "document_number": [r"(?:Document No\.?|ID No\.?|Registration No\.?)\s*[:\-]?\s*([A-Za-z0-9\/-]+)"],
    }
    fields = {}
    confidences = {}
    for field_name, patterns in field_patterns.items():
        value, confidence = _field_from_text(raw_text, patterns)
        fields[field_name] = value
        confidences[field_name] = confidence

    found = sum(1 for value in fields.values() if value)
    overall_confidence = round(sum(confidences.values()) / max(1, found), 2) if found else 0.0
    return {
        "document_type": document_type,
        "fields": fields,
        "confidence": confidences,
        "overall_confidence": overall_confidence,
        "requires_confirmation": overall_confidence < 0.75 or found < 2,
        "raw_text": raw_text,
        "privacy_notice": "Review and confirm OCR fields. NyayaSetu does not store uploaded document images in this workflow.",
    }


def _normalised_comparison(value: Any) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value or "").lower())


def check_civic_application(payload: CivicAssessmentRequest) -> dict:
    service = CIVICDOCS_SERVICES.get(payload.service_type)
    if not service:
        raise ValueError(f"Unsupported CivicDocs service: {payload.service_type}")

    applicant = {key: str(value).strip() for key, value in payload.applicant_data.items() if value is not None}
    missing_fields = [field for field in service["required_fields"] if not applicant.get(field)]
    available = {item.strip().lower() for item in payload.available_documents if item.strip()}
    missing_documents = [document for document in service["required_documents"] if document.lower() not in available]

    values_by_field: dict[str, list[dict]] = {}
    low_confidence_fields = []
    for document in payload.extracted_documents:
        doc_type = str(document.get("document_type") or "uploaded_document")
        fields = document.get("fields") or {}
        confidence = document.get("confidence") or {}
        for field_name, value in fields.items():
            if not value:
                continue
            values_by_field.setdefault(field_name, []).append({"value": value, "document_type": doc_type})
            if float(confidence.get(field_name) or 0) < 0.75:
                low_confidence_fields.append({"field": field_name, "document_type": doc_type, "value": value})

    mismatches = []
    for field_name, observations in values_by_field.items():
        distinct = {_normalised_comparison(item["value"]) for item in observations if item["value"]}
        applicant_value = applicant.get(field_name)
        if applicant_value:
            distinct.add(_normalised_comparison(applicant_value))
        distinct.discard("")
        if len(distinct) > 1:
            mismatches.append({"field": field_name, "observations": observations, "applicant_value": applicant_value or ""})

    field_score = 1 - len(missing_fields) / max(1, len(service["required_fields"]))
    document_score = 1 - len(missing_documents) / max(1, len(service["required_documents"]))
    consistency_score = max(0.0, 1 - len(mismatches) * 0.2 - len(low_confidence_fields) * 0.04)
    readiness_score = round((field_score * 0.4 + document_score * 0.4 + consistency_score * 0.2) * 100)

    blockers = []
    if missing_fields:
        blockers.append("Complete all mandatory applicant fields")
    if missing_documents:
        blockers.append("Collect the mandatory supporting documents")
    if mismatches:
        blockers.append("Resolve spelling or identity mismatches across documents")
    if low_confidence_fields:
        blockers.append("Confirm low-confidence OCR fields against the original documents")

    return {
        "service_type": payload.service_type,
        "service_name": service["name"],
        "description": service["description"],
        "issuing_authority": service["issuing_authority"],
        "readiness_score": readiness_score,
        "status": "ready_for_authority_review" if readiness_score >= 90 and not mismatches else "needs_attention" if readiness_score >= 60 else "incomplete",
        "missing_fields": missing_fields,
        "missing_documents": missing_documents,
        "conditional_documents": service["conditional_documents"],
        "mismatches": mismatches,
        "low_confidence_fields": low_confidence_fields,
        "blockers": blockers,
        "next_steps": [
            "Confirm every OCR-extracted field against the original document",
            "Resolve name, date-of-birth, and address mismatches before submission",
            f"Submit only through the authorised {service['issuing_authority']} portal or office",
            "Keep acknowledgement and application/reference number after submission",
        ],
        "disclaimer": "NyayaSetu prepares an application packet. It does not issue, approve, or guarantee any government certificate or benefit.",
    }


def generate_civic_application_packet(payload: CivicPacketRequest, assessment: dict) -> bytes:
    buffer = BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=42, leftMargin=42, topMargin=42, bottomMargin=42)
    styles = getSampleStyleSheet()
    service = CIVICDOCS_SERVICES[payload.service_type]
    story = [
        Paragraph("NYAYASETU CIVICDOCS", styles["Title"]),
        Spacer(1, 12),
        Paragraph(service["name"].upper(), styles["Heading1"]),
        Spacer(1, 12),
        Paragraph("APPLICATION PREPARATION PACKET - NOT AN OFFICIAL CERTIFICATE", styles["Heading2"]),
        Spacer(1, 12),
        Paragraph(f"Authorised issuing authority: {service['issuing_authority']}", styles["Normal"]),
        Spacer(1, 12),
        Paragraph(f"Readiness score: {assessment['readiness_score']}% ({assessment['status']})", styles["Normal"]),
        Spacer(1, 12),
        Paragraph("Applicant Information", styles["Heading2"]),
        Spacer(1, 12),
    ]
    for field_name in service["required_fields"]:
        label = field_name.replace("_", " ").title()
        value = str(payload.applicant_data.get(field_name) or "[TO BE COMPLETED]")
        story.extend([Paragraph(f"<b>{label}:</b> {value}", styles["Normal"]), Spacer(1, 8)])

    story.extend([Paragraph("Supporting Document Checklist", styles["Heading2"]), Spacer(1, 12)])
    available = {item.lower() for item in payload.available_documents}
    for item in service["required_documents"]:
        status = "AVAILABLE" if item.lower() in available else "MISSING"
        story.extend([Paragraph(f"[ {status} ] {item.replace('_', ' ').title()}", styles["Normal"]), Spacer(1, 8)])

    if assessment["mismatches"]:
        story.extend([Paragraph("Identity / Data Mismatches Requiring Resolution", styles["Heading2"]), Spacer(1, 12)])
        for mismatch in assessment["mismatches"]:
            story.extend([Paragraph(f"- {mismatch['field'].replace('_', ' ').title()}: verify values across uploaded documents.", styles["Normal"]), Spacer(1, 8)])

    story.extend([
        Paragraph("Declaration", styles["Heading2"]),
        Spacer(1, 12),
        Paragraph(payload.declaration, styles["Normal"]),
        Spacer(1, 20),
        Paragraph("Applicant signature: ______________________________", styles["Normal"]),
        Spacer(1, 12),
        Paragraph("Date: __________________  Place: __________________", styles["Normal"]),
        Spacer(1, 20),
        Paragraph("Important", styles["Heading2"]),
        Spacer(1, 8),
        Paragraph(assessment["disclaimer"], styles["Normal"]),
        Spacer(1, 12),
        Paragraph("Generated by NyayaSetu CivicDocs - multilingual public-service application assistance", styles["Italic"]),
    ])
    document.build(story)
    return buffer.getvalue()


def log_civic_feedback(payload: CivicFeedbackRequest) -> dict:
    record = {
        "sample_id": f"CIVIC-{uuid.uuid4()}",
        "module": "civicdocs",
        "service_type": payload.service_type,
        "language": payload.language,
        "document_type": payload.document_type,
        "feedback_type": "ocr_field_correction",
        "correction": {
            "field": payload.field_name,
            "old": "[REDACTED]" if payload.old_value else "",
            "new": "[REDACTED]",
            "source": "user_confirmation",
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    path = Path("dataset") / "civicdocs_feedback.jsonl"
    path.parent.mkdir(exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return {"saved": True, "sample_id": record["sample_id"], "message": "Correction saved for adaptive learning without retaining the corrected personal value."}


def generate_surety_bond_pdf(accused: dict, surety: dict, property_data: dict) -> bytes:
    buffer = BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()

    accused_name = str(accused.get("name", ""))
    fir_number = str(accused.get("fir_number", ""))
    section = str(accused.get("section", ""))
    surety_name = str(surety.get("name", ""))
    surety_address = str(surety.get("address", ""))
    surety_occupation = str(surety.get("occupation", ""))
    surety_relationship = str(surety.get("relationship", ""))
    owner_name = str(property_data.get("owner_name", ""))
    property_address = str(property_data.get("property_address", ""))
    district = str(property_data.get("district", ""))

    story = [
        Paragraph("SURETY BOND / MUCHCHALKA", styles["Title"]),
        Spacer(1, 12),
        Paragraph("PERSONAL BOND UNDER FORM 45 CrPC", styles["Heading2"]),
        Spacer(1, 12),
        Paragraph(
            f"Case Details: FIR No. {fir_number} | Section {section} | Accused: {accused_name}",
            styles["Normal"],
        ),
        Spacer(1, 12),
        Paragraph(
            (
                f"I, {surety_name}, {surety_occupation}, residing at {surety_address}, "
                f"do hereby bind myself as surety for {accused_name} "
                f"charged under Section {section}, FIR No. {fir_number}"
            ),
            styles["Normal"],
        ),
        Spacer(1, 12),
        Paragraph("Property Details", styles["Heading2"]),
        Spacer(1, 12),
        Paragraph(f"Owner Name: {owner_name}", styles["Normal"]),
        Spacer(1, 12),
        Paragraph(f"Property Address: {property_address}", styles["Normal"]),
        Spacer(1, 12),
        Paragraph(f"District: {district}", styles["Normal"]),
        Spacer(1, 12),
        Paragraph(f"Relationship to Accused: {surety_relationship}", styles["Normal"]),
        Spacer(1, 12),
        Paragraph("Bond amount: Rs. 10,000/- (Rupees Ten Thousand Only)", styles["Normal"]),
        Spacer(1, 12),
        Paragraph("Witness 1 Signature: ______________________________", styles["Normal"]),
        Spacer(1, 12),
        Paragraph("Witness 2 Signature: ______________________________", styles["Normal"]),
        Spacer(1, 12),
        Paragraph("Surety Signature: ______________________________", styles["Normal"]),
        Spacer(1, 12),
        Paragraph("Notarial Clause", styles["Heading2"]),
        Spacer(1, 12),
        Paragraph("Sworn before me on _______ day of _______ 2025", styles["Normal"]),
    ]

    document.build(story)
    pdf_bytes = buffer.getvalue()

    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    filename = f"bond_{re.sub(r'[^A-Za-z0-9_.-]+', '_', fir_number.strip()) or 'fir'}.pdf"
    (output_dir / filename).write_bytes(pdf_bytes)

    return pdf_bytes


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/check-bail")
def check_bail(payload: BailCheckRequest) -> dict:
    return check_bail_eligibility(payload.section, payload.months)


@app.post("/generate-bail-pdf")
def generate_bail_pdf_endpoint(
    payload: BailPdfRequest,
    llm_service: LLMService = Depends(get_llm_service),
) -> Response:
    eligibility = check_bail_eligibility(payload.section, payload.months_in_custody)
    case_facts = (
        f"Accused {payload.accused_name}, FIR {payload.fir_number}, "
        f"Police Station {payload.police_station}, Section {payload.section}, "
        f"Custody {payload.months_in_custody} months."
    )
    data = {
        "accused_name": payload.accused_name,
        "fir_number": payload.fir_number,
        "police_station": payload.police_station,
        "section": payload.section,
        "court_name": payload.court_name,
        "bail_section": f"BNSS Section {eligibility['bnss_section']}",
        "grounds": llm_service.generate_bail_grounds(eligibility, case_facts),
    }
    pdf_bytes = generate_bail_pdf(data)

    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    filename = safe_pdf_filename(payload.fir_number)
    (output_dir / filename).write_bytes(pdf_bytes)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/upload-property-doc")
async def upload_property_doc(file: UploadFile = File(...)) -> dict:
    image_bytes = await file.read()
    return extract_property_text(image_bytes)


@app.post("/generate-surety-bond")
def generate_surety_bond(payload: SuretyBondRequest) -> Response:
    pdf_bytes = generate_surety_bond_pdf(payload.accused, payload.surety, payload.property)
    fir_number = str(payload.accused.get("fir_number", ""))
    filename = f"bond_{re.sub(r'[^A-Za-z0-9_.-]+', '_', fir_number.strip()) or 'fir'}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/civicdocs/services")
def civicdocs_services() -> dict:
    return {
        "services": [
            {
                "service_type": key,
                **value,
                "boundary": "Application preparation only; the authorised government authority issues the certificate or benefit.",
            }
            for key, value in CIVICDOCS_SERVICES.items()
        ]
    }


@app.post("/civicdocs/ocr")
async def civicdocs_ocr(
    file: UploadFile = File(...),
    document_type: str = Form("auto"),
) -> dict:
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Upload a JPG, PNG, or other supported document image")
    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded document image is empty")
    try:
        return extract_civic_document_fields(image_bytes, document_type)
    except Exception as error:
        logger.exception("CivicDocs OCR failed")
        raise HTTPException(status_code=422, detail=f"Could not read the document image: {error}") from error


@app.post("/civicdocs/assess")
def civicdocs_assess(payload: CivicAssessmentRequest) -> dict:
    try:
        result = check_civic_application(payload)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    log_to_adaptive_data(
        raw_message=f"CivicDocs assessment requested for {payload.service_type}",
        language="en",
        intent=payload.service_type,
        entities={"service_type": payload.service_type, "applicant_name": payload.applicant_data.get("applicant_name")},
        output_doc_type="civic_application_assessment",
    )
    return result


@app.post("/civicdocs/generate-packet")
def civicdocs_generate_packet(payload: CivicPacketRequest) -> Response:
    try:
        assessment = check_civic_application(payload)
        pdf_bytes = generate_civic_application_packet(payload, assessment)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    filename = f"civicdocs_{payload.service_type}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.pdf"
    output_path = Path("outputs") / filename
    output_path.write_bytes(pdf_bytes)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-CivicDocs-Readiness": str(assessment["readiness_score"]),
        },
    )


@app.post("/civicdocs/feedback")
def civicdocs_feedback(payload: CivicFeedbackRequest) -> dict:
    if payload.service_type not in CIVICDOCS_SERVICES:
        raise HTTPException(status_code=400, detail="Unsupported CivicDocs service")
    return log_civic_feedback(payload)


@app.get("/dataset/stats")
def dataset_stats() -> dict:
    total = 0
    languages: dict[str, int] = {}
    intents: dict[str, int] = {}

    if DATASET_PATH.exists():
        with DATASET_PATH.open("r", encoding="utf-8") as file:
            for line in file:
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                total += 1
                language = str(record.get("language") or "unknown")
                intent = str(record.get("intent") or "unknown")
                languages[language] = languages.get(language, 0) + 1
                intents[intent] = intents.get(intent, 0) + 1

    return {"total": total, "languages": languages, "intents": intents}


@app.get("/dataset/export")
def dataset_export() -> FileResponse:
    DATASET_PATH.parent.mkdir(exist_ok=True)
    DATASET_PATH.touch(exist_ok=True)
    return FileResponse(
        path=DATASET_PATH,
        media_type="application/jsonl",
        filename="nyayasetu_dataset.jsonl",
        headers={"Content-Disposition": "attachment; filename=nyayasetu_dataset.jsonl"},
    )


# 🧠 Adaptive Learning Endpoints
@app.get("/api/adaptive-stats")
async def get_adaptive_stats() -> JSONResponse:
    """Get adaptive learning statistics and improvements"""
    if not ADAPTIVE_LEARNING_ENABLED or not adaptive_engine:
        return JSONResponse({
            "enabled": False,
            "message": "Adaptive learning is not enabled"
        })
    
    stats = adaptive_engine.get_improvement_stats()
    return JSONResponse({
        "enabled": True,
        "stats": stats,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })


@app.get("/api/quality-insights")
async def get_quality_insights(
    intent: Optional[str] = None,
    language: Optional[str] = None
) -> JSONResponse:
    """Get quality insights for specific intent/language"""
    if not ADAPTIVE_LEARNING_ENABLED or not adaptive_engine:
        return JSONResponse({
            "enabled": False,
            "message": "Adaptive learning is not enabled"
        })
    
    insights = adaptive_engine.get_quality_insights(intent, language)
    return JSONResponse({
        "intent": intent,
        "language": language,
        "insights": insights
    })


@app.get("/api/similar-examples")
async def get_similar_examples(
    intent: str,
    language: str,
    limit: int = 5
) -> JSONResponse:
    """Get similar high-quality examples from adaptive dataset"""
    if not ADAPTIVE_LEARNING_ENABLED or not adaptive_engine:
        return JSONResponse({
            "enabled": False,
            "examples": [],
            "message": "Adaptive learning is not enabled"
        })
    
    examples = adaptive_engine.get_similar_examples(intent, language, limit)
    return JSONResponse({
        "intent": intent,
        "language": language,
        "examples": examples,
        "count": len(examples)
    })


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.post("/webhook")
async def webhook(
    request: Request,
    llm_service: LLMService = Depends(get_llm_service),
) -> JSONResponse:
    form = await request.form()

    body = str(form.get("Body") or "")
    from_number = str(form.get("From") or "")

    # Read all required Twilio WhatsApp fields from the incoming form payload.
    _num_media = str(form.get("NumMedia") or "0")
    _media_url = str(form.get("MediaUrl0") or "")
    _media_content_type = str(form.get("MediaContentType0") or "")

    language = detect_message_language(body)
    classification = llm_service.classify_message(body, language)
    base_intent = classification["intent"]
    intent = classify_civic_topic(body, base_intent)
    classification["intent"] = intent
    english_reply = build_english_reply(intent, classification)
    reply = translate_with_indictrans2(english_reply, language)
    pdf_media_url = None

    if intent == "bail_enquiry":
        fir_number, _pdf_path = generate_webhook_bail_pdf(classification, llm_service)
        pdf_media_url = os.getenv("BASE_URL", "") + "/static/" + fir_number + ".pdf"

    send_whatsapp_reply(from_number, reply)

    if intent == "bail_enquiry" and pdf_media_url:
        send_whatsapp_reply(from_number, "Your bail application PDF:", pdf_media_url)

    result = {
        "intent": intent,
        "language": language,
        "body": body,
        "from": from_number,
        "reply": reply,
    }
    log_interaction({**classification, **result})
    detected_language = language
    entities = classification
    output_doc_type = output_doc_type_for_intent(intent)
    asyncio.create_task(manager.broadcast({
        "type": "new_message",
        "input_text": body[:80],
        "input_language": detected_language,
        "language_name": LANGUAGE_NAMES.get(detected_language, detected_language),
        "intent": intent,
        "has_pdf": output_doc_type == "bail_application",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }))
    log_to_adaptive_data(body, detected_language, intent, entities, output_doc_type)

    return JSONResponse(result)

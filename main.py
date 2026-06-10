import io
import asyncio
import json
import logging
import os
import re
import uuid
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any, Optional

import pytesseract
import requests
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Request, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from groq import Groq
from langdetect import DetectorFactory, LangDetectException, detect
from PIL import Image
from pydantic import BaseModel
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
        "timestamp": datetime.utcnow().isoformat(),
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
    "bail": ["bail", "jamani", "zamaanat", "जमानत", "ज़मानत", "जमानत"],
    "surety": ["surety", "bond", "zamanat", "ज़मानतनामा"],
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
    "default": "I received your message. Please send details: accused name, FIR number, police station, and section charged.",
}


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
    police_station = extract_first_match(message, r"(?:police station|PS|थाना)\s*:?\s*([A-Za-z\u0900-\u097F ]{2,50})")
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


def classify_with_groq(message: str, language: str) -> dict:
    service = LLMService(get_config())
    return service.classify_message(message, language)


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
    record["timestamp"] = datetime.utcnow().isoformat()
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
    intent = classification["intent"]
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
        "timestamp": datetime.utcnow().isoformat(),
    }))
    log_to_adaptive_data(body, detected_language, intent, entities, output_doc_type)

    return JSONResponse(result)

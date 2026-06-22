import json

import pytest

from main import (
    CivicAssessmentRequest,
    CivicFeedbackRequest,
    CivicPacketRequest,
    check_civic_application,
    generate_civic_application_packet,
    log_civic_feedback,
)


def complete_income_payload():
    return CivicAssessmentRequest(
        service_type="income_certificate",
        applicant_data={
            "applicant_name": "[NAME]",
            "date_of_birth": "01/01/2000",
            "address": "Pune",
            "district": "Pune",
            "state": "Maharashtra",
            "annual_family_income": "120000",
            "purpose": "Scholarship",
        },
        available_documents=[
            "identity_proof",
            "address_proof",
            "income_proof",
            "passport_photo",
            "self_declaration",
        ],
    )


def test_complete_income_application_is_ready():
    result = check_civic_application(complete_income_payload())
    assert result["readiness_score"] == 100
    assert result["status"] == "ready_for_authority_review"
    assert result["missing_fields"] == []
    assert result["missing_documents"] == []


def test_missing_documents_lower_readiness():
    payload = complete_income_payload()
    payload.available_documents = ["identity_proof"]
    result = check_civic_application(payload)
    assert result["readiness_score"] < 80
    assert "income_proof" in result["missing_documents"]


def test_document_mismatch_is_detected():
    payload = complete_income_payload()
    payload.extracted_documents = [
        {
            "document_type": "aadhaar",
            "fields": {"applicant_name": "Ananya D Patil"},
            "confidence": {"applicant_name": 0.94},
        },
        {
            "document_type": "school_record",
            "fields": {"applicant_name": "Ananya Daitkar"},
            "confidence": {"applicant_name": 0.91},
        },
    ]
    result = check_civic_application(payload)
    assert result["mismatches"][0]["field"] == "applicant_name"
    assert result["status"] == "needs_attention"


def test_unsupported_service_rejected():
    with pytest.raises(ValueError):
        check_civic_application(CivicAssessmentRequest(service_type="passport", applicant_data={}))


def test_civic_packet_is_valid_pdf():
    assessment_payload = complete_income_payload()
    assessment = check_civic_application(assessment_payload)
    packet = CivicPacketRequest(**assessment_payload.model_dump())
    pdf = generate_civic_application_packet(packet, assessment)
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 2000


def test_feedback_log_redacts_corrected_value(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = log_civic_feedback(
        CivicFeedbackRequest(
            service_type="income_certificate",
            field_name="applicant_name",
            old_value="Wrong Name",
            corrected_value="Correct Name",
        )
    )
    record = json.loads((tmp_path / "dataset" / "civicdocs_feedback.jsonl").read_text())
    assert result["saved"] is True
    assert record["correction"]["old"] == "[REDACTED]"
    assert record["correction"]["new"] == "[REDACTED]"
    assert "Correct Name" not in json.dumps(record)

from scripts.validate_model_output import validate_prediction


def valid_prediction():
    return {
        "module": "civicdocs",
        "intent": "income_certificate",
        "language": "hi",
        "urgency": "medium",
        "entities": {},
        "missing_information": ["district"],
        "missing_documents": ["income_proof"],
        "next_actions": ["Confirm OCR fields", "Visit the authorised authority"],
        "recommended_document": "income_certificate_application",
        "readiness_score": 70,
        "confidence": 0.92,
        "safety_boundary": "The authorised government authority must verify and approve the application.",
    }


def test_valid_prediction_passes_contract():
    assert validate_prediction(valid_prediction()) == []


def test_certificate_issuance_without_boundary_fails():
    prediction = valid_prediction()
    prediction["safety_boundary"] = "Approved."
    errors = validate_prediction(prediction)
    assert any("safety_boundary" in error for error in errors)


def test_invalid_module_and_confidence_fail():
    prediction = valid_prediction()
    prediction["module"] = "certificate_generator"
    prediction["confidence"] = 1.5
    errors = validate_prediction(prediction)
    assert any("invalid module" in error for error in errors)
    assert any("confidence" in error for error in errors)

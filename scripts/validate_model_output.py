import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "model" / "nyayasetu_model_contract.json"


def load_contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def validate_prediction(prediction: Any) -> list[str]:
    contract = load_contract()["output_schema"]
    errors = []
    if not isinstance(prediction, dict):
        return ["prediction must be a JSON object"]

    for field in contract["required"]:
        if field not in prediction:
            errors.append(f"missing required field: {field}")

    module = prediction.get("module")
    if module not in contract["properties"]["module"]["enum"]:
        errors.append(f"invalid module: {module}")

    intent = prediction.get("intent")
    if intent not in contract["properties"]["intent"]["enum"]:
        errors.append(f"invalid intent: {intent}")

    urgency = prediction.get("urgency")
    if urgency not in contract["properties"]["urgency"]["enum"]:
        errors.append(f"invalid urgency: {urgency}")

    if not isinstance(prediction.get("entities"), dict):
        errors.append("entities must be an object")

    for field in ["missing_information", "missing_documents", "next_actions"]:
        if not isinstance(prediction.get(field), list):
            errors.append(f"{field} must be an array")

    confidence = prediction.get("confidence")
    if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
        errors.append("confidence must be between 0 and 1")

    readiness = prediction.get("readiness_score")
    if readiness is not None and (not isinstance(readiness, int) or not 0 <= readiness <= 100):
        errors.append("readiness_score must be an integer between 0 and 100")

    boundary = prediction.get("safety_boundary")
    if not isinstance(boundary, str) or len(boundary.strip()) < 20:
        errors.append("safety_boundary must be a meaningful string")
    else:
        lower = boundary.lower()
        if not any(term in lower for term in ["verify", "authority", "court", "lawyer", "advocate", "legal-aid"]):
            errors.append("safety_boundary must require human or authority verification")

    return errors


if __name__ == "__main__":
    import sys

    payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")) if len(sys.argv) > 1 else json.load(sys.stdin)
    validation_errors = validate_prediction(payload)
    print(json.dumps({"valid": not validation_errors, "errors": validation_errors}, indent=2))
    raise SystemExit(1 if validation_errors else 0)

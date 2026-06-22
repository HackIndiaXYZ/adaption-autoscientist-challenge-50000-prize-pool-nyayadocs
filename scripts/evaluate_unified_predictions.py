import csv
import json
import sys
from collections import Counter
from pathlib import Path

from validate_model_output import validate_prediction


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = ROOT / "data" / "nyayasetu_benchmark_v1.csv"


def classification_metrics(expected: list[str], predicted: list[str]) -> dict:
    labels = sorted(set(expected) | set(predicted))
    correct = sum(1 for gold, guess in zip(expected, predicted) if gold == guess)
    f1_scores = []
    for label in labels:
        tp = sum(1 for gold, guess in zip(expected, predicted) if gold == label and guess == label)
        fp = sum(1 for gold, guess in zip(expected, predicted) if gold != label and guess == label)
        fn = sum(1 for gold, guess in zip(expected, predicted) if gold == label and guess != label)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1_scores.append(2 * precision * recall / (precision + recall) if precision + recall else 0.0)
    return {"accuracy": round(correct / len(expected), 4), "macro_f1": round(sum(f1_scores) / len(f1_scores), 4)}


def set_f1(expected_values: list[set[str]], predicted_values: list[set[str]]) -> float:
    scores = []
    for expected, predicted in zip(expected_values, predicted_values):
        if not expected and not predicted:
            scores.append(1.0)
            continue
        tp = len(expected & predicted)
        precision = tp / len(predicted) if predicted else 0.0
        recall = tp / len(expected) if expected else 0.0
        scores.append(2 * precision * recall / (precision + recall) if precision + recall else 0.0)
    return round(sum(scores) / len(scores), 4)


def main(predictions_path: str):
    with BENCHMARK.open("r", encoding="utf-8") as handle:
        benchmark = {row["benchmark_id"]: row for row in csv.DictReader(handle)}
    with Path(predictions_path).open("r", encoding="utf-8") as handle:
        predictions = {row["benchmark_id"]: row for row in csv.DictReader(handle)}

    expected_modules, predicted_modules = [], []
    expected_intents, predicted_intents = [], []
    expected_documents, predicted_documents = [], []
    valid_json = 0
    safety_valid = 0
    failures = Counter()

    for benchmark_id, item in benchmark.items():
        row = predictions.get(benchmark_id)
        if not row:
            prediction = {}
            failures["missing_prediction"] += 1
        else:
            try:
                prediction = json.loads(row["prediction_json"])
            except json.JSONDecodeError:
                prediction = {}
                failures["invalid_json"] += 1
        errors = validate_prediction(prediction)
        if not errors:
            valid_json += 1
        if not any("safety_boundary" in error for error in errors):
            safety_valid += 1
        expected_modules.append(item["expected_module"])
        predicted_modules.append(prediction.get("module", "invalid"))
        expected_intents.append(item["expected_intent"])
        predicted_intents.append(prediction.get("intent", "invalid"))
        expected_documents.append({value.strip().lower() for value in item["expected_missing_documents"].split("|") if value.strip()})
        predicted_documents.append({str(value).strip().lower() for value in prediction.get("missing_documents", []) if str(value).strip()})

    report = {
        "benchmark_records": len(benchmark),
        "module": classification_metrics(expected_modules, predicted_modules),
        "intent": classification_metrics(expected_intents, predicted_intents),
        "missing_document_macro_f1": set_f1(expected_documents, predicted_documents),
        "structured_json_validity": round(valid_json / len(benchmark), 4),
        "safety_boundary_compliance": round(safety_valid / len(benchmark), 4),
        "failures": dict(failures),
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/evaluate_unified_predictions.py <predictions.csv>")
    main(sys.argv[1])

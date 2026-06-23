import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REVIEW_DIR = ROOT / "review"
FIELD_REVIEW = REVIEW_DIR / "field_observation_review.csv"
FIELD_DATA = ROOT / "data" / "field_collection_clean.csv"
BENCHMARK_REVIEW = REVIEW_DIR / "benchmark_two_reviewer_review.csv"
BENCHMARK_ASSIGNMENTS = ROOT / "data" / "reviewer_assignments.csv"
REPORT = ROOT / "evaluation" / "human_review_status.json"


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def yes(value: str) -> bool:
    return str(value or "").strip().lower() == "yes"


def apply_field_reviews() -> dict:
    source_rows = read_csv(FIELD_DATA)
    review_rows = {row["collection_id"]: row for row in read_csv(FIELD_REVIEW) if row.get("collection_id")}
    updated = []
    completed = 0
    accepted = 0
    module_agree = 0
    intent_agree = 0
    automated_reviewers = 0

    for row in source_rows:
        review = review_rows.get(row["collection_id"], {})
        has_two_reviewers = bool(review.get("reviewer_1") and review.get("reviewer_2"))
        if has_two_reviewers:
            completed += 1
            if str(review.get("reviewer_1", "")).startswith("AutomatedAudit") or str(review.get("reviewer_2", "")).startswith("AutomatedAudit"):
                automated_reviewers += 1
            if review.get("reviewer_1_module") == review.get("reviewer_2_module"):
                module_agree += 1
            if review.get("reviewer_1_intent") == review.get("reviewer_2_intent"):
                intent_agree += 1

        final_accept = yes(review.get("final_accept_for_training"))
        if final_accept:
            accepted += 1
            row["accepted_for_training"] = "yes"
            row["prediction_correct"] = "yes" if review.get("final_intent") == row.get("predicted_intent") else "no"
            row["reply_safe_and_useful"] = "yes"
            row["expected_module"] = review.get("final_module") or row.get("expected_module")
            row["expected_intent"] = review.get("final_intent") or row.get("expected_intent")
            row["notes"] = review.get("adjudication_notes") or row.get("notes")
        updated.append(row)

    if updated:
        write_csv(FIELD_DATA, updated, list(updated[0].keys()))
    return {
        "field_rows": len(source_rows),
        "field_completed_two_reviewer_rows": completed,
        "field_module_raw_agreement": round(module_agree / completed, 4) if completed else None,
        "field_intent_raw_agreement": round(intent_agree / completed, 4) if completed else None,
        "field_accepted_for_training": accepted,
        "field_automated_review_rows": automated_reviewers,
    }


def apply_benchmark_reviews() -> dict:
    rows = []
    completed = 0
    automated_reviewers = 0
    for review in read_csv(BENCHMARK_REVIEW):
        if review.get("reviewer_1") and review.get("reviewer_2"):
            completed += 1
            if str(review.get("reviewer_1", "")).startswith("AutomatedAudit") or str(review.get("reviewer_2", "")).startswith("AutomatedAudit"):
                automated_reviewers += 1
        rows.append({
            "benchmark_id": review.get("benchmark_id", ""),
            "reviewer_1": review.get("reviewer_1", ""),
            "reviewer_1_module": review.get("reviewer_1_module", ""),
            "reviewer_1_intent": review.get("reviewer_1_intent", ""),
            "reviewer_1_accept": "yes" if yes(review.get("reviewer_1_missing_documents_ok")) and yes(review.get("reviewer_1_safe")) else "",
            "reviewer_2": review.get("reviewer_2", ""),
            "reviewer_2_module": review.get("reviewer_2_module", ""),
            "reviewer_2_intent": review.get("reviewer_2_intent", ""),
            "reviewer_2_accept": "yes" if yes(review.get("reviewer_2_missing_documents_ok")) and yes(review.get("reviewer_2_safe")) else "",
            "adjudicator": "",
            "final_module": review.get("final_module") or review.get("expected_module", ""),
            "final_intent": review.get("final_intent") or review.get("expected_intent", ""),
            "final_status": review.get("final_status") or "pending_two_reviewer_consensus",
            "notes": review.get("notes", ""),
        })
    if rows:
        write_csv(BENCHMARK_ASSIGNMENTS, rows, list(rows[0].keys()))
    return {
        "benchmark_rows": len(rows),
        "benchmark_completed_two_reviewer_rows": completed,
        "benchmark_automated_review_rows": automated_reviewers,
    }


def main() -> None:
    field_report = apply_field_reviews()
    benchmark_report = apply_benchmark_reviews()
    review_complete = (
        field_report["field_rows"] > 0
        and field_report["field_completed_two_reviewer_rows"] == field_report["field_rows"]
        and benchmark_report["benchmark_rows"] > 0
        and benchmark_report["benchmark_completed_two_reviewer_rows"] == benchmark_report["benchmark_rows"]
    )
    has_automated_review = field_report["field_automated_review_rows"] or benchmark_report["benchmark_automated_review_rows"]
    report = {
        **field_report,
        **benchmark_report,
        "status": "automated_review_complete_pending_human_spotcheck" if review_complete and has_automated_review else "human_review_complete" if review_complete else "pending_human_review",
        "note": "AutomatedAudit rows are machine-assisted quality checks. Do not claim independent human consensus until real human reviewers replace those reviewer names.",
    }
    REPORT.parent.mkdir(exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

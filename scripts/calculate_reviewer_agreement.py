import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSIGNMENTS = ROOT / "data" / "reviewer_assignments.csv"
OUTPUT = ROOT / "evaluation" / "reviewer_agreement.json"


def main():
    with ASSIGNMENTS.open("r", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    completed = [row for row in rows if row["reviewer_1"] and row["reviewer_2"] and row["reviewer_2_module"] and row["reviewer_2_intent"]]
    module_agreement = sum(row["reviewer_1_module"] == row["reviewer_2_module"] for row in completed)
    intent_agreement = sum(row["reviewer_1_intent"] == row["reviewer_2_intent"] for row in completed)
    both_accept = sum(row["reviewer_1_accept"].lower() == "yes" and row["reviewer_2_accept"].lower() == "yes" for row in completed)
    automated_rows = sum(row["reviewer_1"].startswith("AutomatedAudit") or row["reviewer_2"].startswith("AutomatedAudit") for row in completed)
    complete = len(completed) == len(rows)
    report = {
        "total_assignments": len(rows),
        "completed_two_reviewer_rows": len(completed),
        "module_raw_agreement": round(module_agreement / len(completed), 4) if completed else None,
        "intent_raw_agreement": round(intent_agreement / len(completed), 4) if completed else None,
        "both_reviewers_accept_rate": round(both_accept / len(completed), 4) if completed else None,
        "automated_review_rows": automated_rows,
        "status": "automated_review_complete_pending_human_spotcheck" if complete and automated_rows else "ready" if complete else "pending_human_review",
        "warning": "AutomatedAudit rows are not independent human consensus. Replace reviewer names with real reviewers before claiming human-reviewed agreement.",
    }
    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

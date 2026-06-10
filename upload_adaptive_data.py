import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv


DATASET_PATH = Path("dataset/interactions.jsonl")
ADAPTIVE_DATA_ENDPOINT = "https://api.adaptionlabs.ai/v1/ingest"
DATASET_NAME = "nyayasetu-legal-dialogues-multilingual"
BATCH_SIZE = 25


def load_records(path: Path) -> list[dict]:
    records = []
    if not path.exists():
        return records
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def main() -> int:
    load_dotenv(".env")
    api_key = os.getenv("ADAPTIVE_DATA_API_KEY", "").strip()
    if not api_key:
        print("ADAPTIVE_DATA_API_KEY is missing")
        return 1

    records = load_records(DATASET_PATH)
    if not records:
        print("No records found in dataset/interactions.jsonl")
        return 1

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    uploaded = 0
    for start in range(0, len(records), BATCH_SIZE):
        batch = records[start:start + BATCH_SIZE]
        response = requests.post(
            ADAPTIVE_DATA_ENDPOINT,
            json={"data": batch, "dataset_name": DATASET_NAME},
            headers=headers,
            timeout=20,
        )
        if response.status_code >= 400:
            print(f"Upload failed at rows {start + 1}-{start + len(batch)}")
            print(f"Status: {response.status_code}")
            print(response.text[:1000])
            return 1
        uploaded += len(batch)
        print(f"Uploaded {uploaded}/{len(records)} rows")

    print("Adaptive Data upload successful")
    return 0


if __name__ == "__main__":
    sys.exit(main())

from huggingface_hub import HfApi
from dotenv import load_dotenv
import os

load_dotenv()

api = HfApi()
api.upload_file(
    path_or_fileobj="./dataset/interactions.jsonl",
    path_in_repo="data/interactions.jsonl",
    repo_id="Ananya80/nyayasetu-legal-dialogues-multilingual",
    repo_type="dataset",
    token=os.getenv("HF_TOKEN"),
)
print("Uploaded successfull")

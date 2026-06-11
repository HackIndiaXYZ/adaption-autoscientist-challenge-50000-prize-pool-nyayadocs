from huggingface_hub import HfApi
from dotenv import load_dotenv
import os

load_dotenv()

api = HfApi()

# First, let's check current files
print("Uploading enhanced dataset to HuggingFace...")
print("Folder: ./adaptive_data")
print("Repo: Ananya80/nyayasetu-legal-dialogues-multilingual")

api.upload_folder(
    folder_path="./adaptive_data",
    path_in_repo=".",
    repo_id="Ananya80/nyayasetu-legal-dialogues-multilingual",
    repo_type="dataset",
    token=os.getenv("HF_TOKEN"),
    commit_message="Enhanced dataset v2.0: 3496 records with 10 patterns per intent for 10/10 quality",
)
print("\n✅ Upload successful!")
print("Dataset now has 3,496 records (65% increase)")
print("Visit: https://huggingface.co/datasets/Ananya80/nyayasetu-legal-dialogues-multilingual")

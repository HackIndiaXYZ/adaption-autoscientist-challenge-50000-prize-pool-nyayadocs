from huggingface_hub import HfApi
from dotenv import load_dotenv
import os

load_dotenv()

api = HfApi()

print("Uploading NyayaSetu adaptive and unified datasets to Hugging Face...")
print("Repo: Ananya80/nyayasetu-legal-dialogues-multilingual")

api.upload_folder(
    folder_path="./adaptive_data",
    path_in_repo=".",
    repo_id="Ananya80/nyayasetu-legal-dialogues-multilingual",
    repo_type="dataset",
    token=os.getenv("HF_TOKEN"),
    commit_message="Update adaptive legal-aid dataset artifacts",
)
for filename in [
    "nyayasetu_unified_autoscientist.csv",
    "nyayasetu_unified_eval.csv",
    "nyayasetu_unified_schema.json",
]:
    api.upload_file(
        path_or_fileobj=f"./data/{filename}",
        path_in_repo=f"unified/{filename}",
        repo_id="Ananya80/nyayasetu-legal-dialogues-multilingual",
        repo_type="dataset",
        token=os.getenv("HF_TOKEN"),
        commit_message=f"Publish unified AutoScientist artifact: {filename}",
    )
print("\nUpload successful: adaptive artifacts plus 2,451-record unified dataset")
print("Visit: https://huggingface.co/datasets/Ananya80/nyayasetu-legal-dialogues-multilingual")

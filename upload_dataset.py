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
    "field_collection_clean.csv",
    "nyayasetu_benchmark_v1.csv",
    "nyayasetu_benchmark_report.json",
]:
    api.upload_file(
        path_or_fileobj=f"./data/{filename}",
        path_in_repo=f"unified/{filename}",
        repo_id="Ananya80/nyayasetu-legal-dialogues-multilingual",
        repo_type="dataset",
        token=os.getenv("HF_TOKEN"),
        commit_message=f"Publish unified AutoScientist artifact: {filename}",
    )
for filename in [
    "baseline_predictions.csv",
    "baseline_metrics.json",
    "reviewer_agreement.json",
]:
    api.upload_file(
        path_or_fileobj=f"./evaluation/{filename}",
        path_in_repo=f"evaluation/{filename}",
        repo_id="Ananya80/nyayasetu-legal-dialogues-multilingual",
        repo_type="dataset",
        token=os.getenv("HF_TOKEN"),
        commit_message=f"Publish evaluation artifact: {filename}",
    )
print("\nUpload successful: adaptive artifacts plus 2,573-record unified dataset with Twilio field observations")
print("Visit: https://huggingface.co/datasets/Ananya80/nyayasetu-legal-dialogues-multilingual")

from huggingface_hub import HfApi
from dotenv import load_dotenv
import os

load_dotenv()

api = HfApi()
api.upload_folder(
    folder_path="./adaptive_data",
    path_in_repo=".",
    repo_id="Ananya80/nyayasetu-legal-dialogues-multilingual",
    repo_type="dataset",
    token=os.getenv("HF_TOKEN"),
)
print("Uploaded successful")

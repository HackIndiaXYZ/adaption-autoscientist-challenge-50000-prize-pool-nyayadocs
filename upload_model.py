from pathlib import Path
import os

from dotenv import load_dotenv
from huggingface_hub import HfApi


load_dotenv()

MODEL_DIR = Path("model/adaption_nyayasetu_legal_assist")
REPO_ID = "Ananya80/adaption_nyayasetu_legal_assist"
REQUIRED_FILES = ["README.md", "training_config.json"]


def main() -> None:
    missing = [name for name in REQUIRED_FILES if not (MODEL_DIR / name).exists()]
    if missing:
        raise SystemExit(f"Missing required files: {missing}")

    has_weights = any((MODEL_DIR / name).exists() for name in ["adapter_model.safetensors", "pytorch_model.bin", "model.safetensors"])
    if not has_weights:
        print("Warning: no model weight file found. Uploading model card/config only.")
        print("Export weights from Adaption and place them in model/adaption_nyayasetu_legal_assist/ before final model release.")

    token = os.getenv("HF_TOKEN")
    if not token:
        raise SystemExit("HF_TOKEN is not set in .env")

    api = HfApi()
    api.create_repo(repo_id=REPO_ID, repo_type="model", exist_ok=True, token=token)
    api.upload_folder(
        folder_path=str(MODEL_DIR),
        repo_id=REPO_ID,
        repo_type="model",
        token=token,
        commit_message="Publish NyayaSetu AutoScientist model card and adapter artifacts",
    )
    print(f"Uploaded model artifacts to https://huggingface.co/{REPO_ID}")


if __name__ == "__main__":
    main()

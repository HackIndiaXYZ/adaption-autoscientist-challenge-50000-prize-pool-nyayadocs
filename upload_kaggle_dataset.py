import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(".env")

root = Path(__file__).resolve().parent
kaggle_dir = root / ".kaggle"
kaggle_dir.mkdir(exist_ok=True)

token = os.getenv("KAGGLE_API_TOKEN") or os.getenv("KAGGLE_TOKEN") or os.getenv("KAGGLE_KEY")
if not token:
    raise SystemExit("Missing KAGGLE_TOKEN or KAGGLE_API_TOKEN in .env")

env = os.environ.copy()
env["KAGGLE_CONFIG_DIR"] = str(kaggle_dir)
env["KAGGLE_API_TOKEN"] = token

cmd = [
    sys.executable,
    "-m",
    "kaggle",
    "datasets",
    "create",
    "-p",
    str(root / "adaptive_data"),
    "--dir-mode",
    "zip",
    "--public",
]

result = subprocess.run(cmd, env=env, text=True)
if result.returncode != 0:
    update_cmd = [
        sys.executable,
        "-m",
        "kaggle",
        "datasets",
        "version",
        "-p",
        str(root / "adaptive_data"),
        "--dir-mode",
        "zip",
        "-m",
        "Update NyayaSetu adaptive dataset release",
    ]
    result = subprocess.run(update_cmd, env=env, text=True)

raise SystemExit(result.returncode)

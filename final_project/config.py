# final_project/config.py
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "csv_files"
DATA_DIR.mkdir(parents=True, exist_ok=True)

FRANKFURTER_BASE_URL = "https://api.frankfurter.app"

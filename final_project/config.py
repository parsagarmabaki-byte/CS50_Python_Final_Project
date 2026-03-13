# final_project/config.py
"""Configuration settings for the final project application.

This module defines application-wide constants including paths and API URLs.
"""
from pathlib import Path

#: Project root directory, resolved from this file's location.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

#: Directory for storing CSV data files. Created if it doesn't exist.
DATA_DIR = PROJECT_ROOT / "csv_files"
DATA_DIR.mkdir(parents=True, exist_ok=True)

#: Base URL for the Frankfurter currency exchange API.
FRANKFURTER_BASE_URL = "https://api.frankfurter.app"

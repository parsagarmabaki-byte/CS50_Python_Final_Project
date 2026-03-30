# final_project/config.py
"""Configuration settings for the final project application.

This module defines application-wide constants including paths and API URLs.
"""
from pathlib import Path

#: Project root directory (web_ui/final_project), resolved from this file's location.
WEB_PROJECT_ROOT = Path(__file__).resolve().parent.parent

#: Terminal UI project root (parent of web_ui), for shared data files.
PROJECT_ROOT = WEB_PROJECT_ROOT.parent

#: Directory for storing CSV data files (shared with terminal_ui).
#: Points to PROJECT_ROOT/csv_files to share data between web and terminal UI.
DATA_DIR = PROJECT_ROOT / "csv_files"
DATA_DIR.mkdir(parents=True, exist_ok=True)

#: Directory for storing user account directories (watchlists, prices).
ACCOUNT_DIR = DATA_DIR / "account_directory"
ACCOUNT_DIR.mkdir(parents=True, exist_ok=True)

#: Base URL for the Frankfurter currency exchange API.
FRANKFURTER_BASE_URL = "https://api.frankfurter.app"

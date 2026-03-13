# final_project/api_clients.py
import requests
from typing import Dict
from .config import FRANKFURTER_BASE_URL

class FrankfurterClient:
    def __init__(self, base_url: str = FRANKFURTER_BASE_URL):
        self.base_url = base_url.rstrip("/")

    def latest(self, base: str, symbols: str) -> Dict:
        # base and symbols expect ISO currency codes like "USD" and "SEK"
        url = f"{self.base_url}/latest?from={base}&to={symbols}"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json()

    def range(self, start_date: str, end_date: str, base: str, symbols: str) -> Dict:
        url = f"{self.base_url}/{start_date}..{end_date}?from={base}&to={symbols}"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json()

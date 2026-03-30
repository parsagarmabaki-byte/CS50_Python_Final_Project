# final_project/api_clients.py
"""API client modules for external currency exchange services.

This module provides client classes for interacting with the Frankfurter
currency exchange rate API.
"""
import requests
from typing import Dict
from .config import FRANKFURTER_BASE_URL


class FrankfurterClient:
    """Client for the Frankfurter currency exchange rate API."""

    def __init__(self, base_url: str = FRANKFURTER_BASE_URL):
        """Initialize the Frankfurter API client.

        Args:
            base_url: The base URL for the Frankfurter API.
                      Defaults to the configured FRANKFURTER_BASE_URL.
        """
        self.base_url = base_url.rstrip("/")

    def latest(self, base: str, symbols: str) -> Dict:
        """Fetch the latest exchange rates.

        Args:
            base: Base currency ISO code (e.g., "USD").
            symbols: Target currency ISO code (e.g., "SEK").

        Returns:
            A dictionary containing the exchange rate data from the API.

        Raises:
            requests.HTTPError: If the API request fails.
        """
        # base and symbols expect ISO currency codes like "USD" and "SEK"
        url = f"{self.base_url}/latest?from={base}&to={symbols}"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json()

    def range(self, start_date: str, end_date: str, base: str, symbols: str) -> Dict:
        """Fetch exchange rates for a date range.

        Args:
            start_date: Start date in YYYY-MM-DD format.
            end_date: End date in YYYY-MM-DD format.
            base: Base currency ISO code (e.g., "USD").
            symbols: Target currency ISO code (e.g., "SEK").

        Returns:
            A dictionary containing exchange rate data for the date range.

        Raises:
            requests.HTTPError: If the API request fails.
        """
        url = f"{self.base_url}/{start_date}..{end_date}?from={base}&to={symbols}"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json()

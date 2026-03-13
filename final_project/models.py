# final_project/models.py
"""Data models for the final project application.

This module defines the core data structures used throughout the application
for representing user accounts, price records, and watchlist entries.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Account:
    """Represents a user account.

    Attributes:
        username: The unique username for the account.
        password: The user's password (stored in plain text).
        email: The user's email address (optional).
        created: The date the account was created (optional, YYYY-MM-DD format).
    """
    username: str
    password: str
    email: Optional[str] = None
    created: Optional[str] = None


@dataclass
class PriceRecord:
    """Represents a recorded currency exchange price.

    Attributes:
        symbol: The currency pair symbol (e.g., "FX:USDSEK").
        price: The exchange rate value.
        date: The date of the price record (YYYY-MM-DD format).
        source: The source of the price data (e.g., "Frankfurter").
    """
    symbol: str
    price: float
    date: str
    source: str


@dataclass
class WatchlistEntry:
    """Represents an entry in a user's watchlist.

    Attributes:
        symbol: The currency pair symbol to track (e.g., "FX:USDSEK").
    """
    symbol: str

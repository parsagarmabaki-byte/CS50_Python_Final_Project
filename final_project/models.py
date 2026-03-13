# final_project/models.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class Account:
    username: str
    password: str
    email: Optional[str] = None
    created: Optional[str] = None

@dataclass
class PriceRecord:
    symbol: str
    price: float
    date: str
    source: str

@dataclass
class WatchlistEntry:
    symbol: str

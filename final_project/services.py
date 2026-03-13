# final_project/services.py
import re
from datetime import datetime, timezone
from typing import List
from .models import Account, PriceRecord, WatchlistEntry
from .repositories import AccountRepository, WatchlistRepository, PricesRepository
from .api_clients import FrankfurterClient

class AccountService:
    def __init__(self, repo: AccountRepository):
        self.repo = repo

    def register(self, username: str, password: str, email: str | None = None) -> Account:
        if self.repo.find(username):
            raise ValueError("username exists")
        acc = Account(username=username, password=password, email=email, created=datetime.now(timezone.utc).strftime("%Y-%m-%d"))
        self.repo.add_account(acc)
        return acc

    def authenticate(self, username: str, password: str) -> bool:
        acc = self.repo.find(username)
        return acc is not None and acc.password == password

class WatchlistService:
    SYMBOL_RE = re.compile(r"^([A-Z]{3})([A-Z]{3})$")

    def __init__(self, watchlist_repo: WatchlistRepository, prices_repo: PricesRepository, api_client: FrankfurterClient):
        self.watchlist_repo = watchlist_repo
        self.prices_repo = prices_repo
        self.api_client = api_client

    def add_symbol(self, username: str, base: str, quote: str) -> PriceRecord:
        base_up = base.upper()
        quote_up = quote.upper()
        if not self.SYMBOL_RE.match(base_up + quote_up):
            raise ValueError("invalid currency codes")
        symbol = f"FX:{base_up}{quote_up}"
        self.watchlist_repo.add(username, WatchlistEntry(symbol))
        resp = self.api_client.latest(base_up, quote_up)
        # Frankfurter returns { "amount":1.0, "base":"USD", "date":"2022-01-01", "rates": {"SEK": 10.0}}
        price = float(resp["rates"][quote_up])
        date = resp.get("date", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
        record = PriceRecord(symbol=symbol, price=price, date=date, source="Frankfurter")
        self.prices_repo.append(username, record)
        return record

    def list_watchlist(self, username: str) -> List[WatchlistEntry]:
        return self.watchlist_repo.list(username)

    def get_latest_prices(self, username: str) -> List[PriceRecord]:
        return self.prices_repo.list_latest(username)

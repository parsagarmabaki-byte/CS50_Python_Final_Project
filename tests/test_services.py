# tests/test_services.py
from pathlib import Path
from final_project.services import WatchlistService, AccountService
from final_project.repositories import CSVWatchlistRepository, CSVPricesRepository, CSVAccountRepository
from final_project.api_clients import FrankfurterClient
from final_project.models import Account
import pytest

class DummyFrankfurter:
    def latest(self, base, symbols):
        return {"base": base, "date": "2025-01-02", "rates": {symbols: 10.0}}

def test_add_symbol(tmp_path: Path):
    data_dir = tmp_path
    acc_repo = CSVAccountRepository(data_dir / "Accounts.csv")
    acc_repo.add_account(Account("bob","pw",None,"2025-01-01"))
    watch_repo = CSVWatchlistRepository(data_dir)
    prices_repo = CSVPricesRepository(data_dir)
    api = DummyFrankfurter()
    svc = WatchlistService(watch_repo, prices_repo, api)
    pr = svc.add_symbol("bob", "USD", "SEK")
    assert pr.symbol == "FX:USDSEK"
    assert pr.price == 10.0

# tests/test_repositories.py
import pytest
from pathlib import Path
from final_project.repositories import CSVAccountRepository
from final_project.models import Account

def test_csv_account_repo(tmp_path: Path):
    p = tmp_path / "Accounts.csv"
    repo = CSVAccountRepository(p)
    assert repo.list_accounts() == []
    acc = Account("alice","pw","a@x.com","2025-01-01")
    repo.add_account(acc)
    found = repo.find("alice")
    assert found is not None and found.username == "alice"
    repo.delete("alice")
    assert repo.find("alice") is None

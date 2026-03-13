# tests/test_web.py
from fastapi.testclient import TestClient
from final_project.web import app, _token_store
from final_project.repositories import CSVAccountRepository
from final_project.models import Account
from pathlib import Path
import pytest

client = TestClient(app)

def _create_test_services(tmp_path: Path):
    """Helper to create test services with mocked API client."""
    acc_repo = CSVAccountRepository(tmp_path / "Accounts.csv")
    from final_project.repositories import CSVWatchlistRepository, CSVPricesRepository
    watch_repo = CSVWatchlistRepository(tmp_path)
    prices_repo = CSVPricesRepository(tmp_path)
    # use a dummy client to avoid network
    class Dummy:
        def latest(self, base, symbols):
            return {"base": base, "date": "2025-01-02", "rates": {symbols: 10.0}}
    api = Dummy()
    from final_project.services import AccountService, WatchlistService
    return AccountService(acc_repo), WatchlistService(watch_repo, prices_repo, api)

def test_register_login_and_watchlist_flow(tmp_path: Path, monkeypatch):
    # ensure services use tmp_path by monkeypatching build_services to use repos in tmp_path
    from final_project import cli
    from final_project import web

    def build_services_tmp():
        return _create_test_services(tmp_path)

    monkeypatch.setattr(cli, "build_services", build_services_tmp)
    monkeypatch.setattr(web, "build_services", build_services_tmp)

    # Register
    r = client.post("/register", json={"username": "u1", "password": "pw", "email": "a@b.com"})
    assert r.status_code == 200

    # Login
    r = client.post("/login", json={"username": "u1", "password": "pw"})
    assert r.status_code == 200
    token = r.json()["token"]
    assert token in _token_store

    headers = {"Authorization": f"Bearer {token}"}

    # Add symbol
    r = client.post("/me/watchlist", json={"base": "USD", "quote": "SEK"}, headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["symbol"] == "FX:USDSEK"
    assert body["price"] == 10.0

    # Get watchlist
    r = client.get("/me/watchlist", headers=headers)
    assert r.status_code == 200
    assert r.json() == [{"symbol": "FX:USDSEK"}]

    # Get latest prices
    r = client.get("/me/prices", headers=headers)
    assert r.status_code == 200
    prs = r.json()
    assert any(p["symbol"] == "FX:USDSEK" for p in prs)

    # Update prices
    r = client.post("/me/prices/update", headers=headers)
    assert r.status_code == 200

    # Export CSV
    r = client.get("/me/prices/export", headers=headers)
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]

    # Logout
    r = client.post("/logout", headers=headers)
    assert r.status_code == 200
    # token should be invalidated
    r = client.get("/me/watchlist", headers=headers)
    assert r.status_code == 401


def test_remove_symbol(tmp_path: Path, monkeypatch):
    from final_project import cli
    from final_project import web

    def build_services_tmp():
        return _create_test_services(tmp_path)

    monkeypatch.setattr(cli, "build_services", build_services_tmp)
    monkeypatch.setattr(web, "build_services", build_services_tmp)

    # Register and login
    client.post("/register", json={"username": "u2", "password": "pw"})
    r = client.post("/login", json={"username": "u2", "password": "pw"})
    token = r.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Add symbol
    client.post("/me/watchlist", json={"base": "EUR", "quote": "GBP"}, headers=headers)
    
    # Verify watchlist
    r = client.get("/me/watchlist", headers=headers)
    assert r.json() == [{"symbol": "FX:EURGBP"}]

    # Remove symbol
    r = client.delete("/me/watchlist/FX:EURGBP", headers=headers)
    assert r.status_code == 200

    # Verify removal
    r = client.get("/me/watchlist", headers=headers)
    assert r.json() == []


def test_auth_errors(tmp_path: Path, monkeypatch):
    from final_project import cli
    from final_project import web

    def build_services_tmp():
        return _create_test_services(tmp_path)

    monkeypatch.setattr(cli, "build_services", build_services_tmp)
    monkeypatch.setattr(web, "build_services", build_services_tmp)

    # Missing auth token
    r = client.get("/me/watchlist")
    assert r.status_code == 401

    # Invalid token
    r = client.get("/me/watchlist", headers={"Authorization": "Bearer invalid-token"})
    assert r.status_code == 401

    # Invalid login credentials
    client.post("/register", json={"username": "u3", "password": "pw"})
    r = client.post("/login", json={"username": "u3", "password": "wrong"})
    assert r.status_code == 401


def test_invalid_symbol_codes(tmp_path: Path, monkeypatch):
    from final_project import cli
    from final_project import web

    def build_services_tmp():
        return _create_test_services(tmp_path)

    monkeypatch.setattr(cli, "build_services", build_services_tmp)
    monkeypatch.setattr(web, "build_services", build_services_tmp)

    # Register and login
    client.post("/register", json={"username": "u4", "password": "pw"})
    r = client.post("/login", json={"username": "u4", "password": "pw"})
    token = r.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Invalid currency codes (not 3 letters)
    r = client.post("/me/watchlist", json={"base": "US", "quote": "SEK"}, headers=headers)
    assert r.status_code == 400

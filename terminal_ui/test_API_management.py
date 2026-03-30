from datetime import date
from pathlib import Path

import API_management as api


def test_group_symbols_splits_fx_pairs_precisely():
    records = [
        {"symbol": "FX:USDSEK"},
        {"symbol": "FX:EURNOK"},
    ]

    assert api.group_symbols(records) == [("USD", "SEK"), ("EUR", "NOK")]


def test_append_to_watchlist_writes_expected_symbol(tmp_path, monkeypatch):
    user_dir = tmp_path / "alice"
    user_dir.mkdir()
    watchlist = user_dir / "Watchlist.csv"
    watchlist.write_text("Stocks\n", encoding="utf-8")

    monkeypatch.setattr(api, "account_files_path", lambda username: user_dir)

    api.append_to_watchlist("alice", "USD", "SEK")

    assert watchlist.read_text(encoding="utf-8").splitlines() == [
        "Stocks",
        "FX:USDSEK",
    ]


def test_append_price_entry_writes_price_row(tmp_path, monkeypatch):
    user_dir = tmp_path / "alice"
    user_dir.mkdir()
    prices = user_dir / "Prices.csv"
    prices.write_text("symbol,price,date,source\n", encoding="utf-8")

    monkeypatch.setattr(api, "account_files_path", lambda username: user_dir)

    api.append_price_entry(
        "alice",
        "USD",
        "SEK",
        {"rates": {"SEK": 10.5}, "date": "2026-03-30"},
    )

    assert prices.read_text(encoding="utf-8").splitlines() == [
        "symbol,price,date,source",
        "FX:USDSEK,10.5,2026-03-30,Frankfurter",
    ]


def test_update_symbol_data_returns_price_and_date(monkeypatch):
    monkeypatch.setattr(
        api,
        "frankfurter_api",
        lambda base, quote: {"rates": {quote: 11.27}, "date": "2026-03-29"},
    )

    assert api.update_symbol_data("USD", "SEK") == (11.27, "2026-03-29")


def test_update_prices_returns_none_when_prices_file_has_no_records(monkeypatch):
    monkeypatch.setattr(api, "account_files_path", lambda username: Path("/unused"))
    monkeypatch.setattr(api, "read_file", lambda file_path: [])

    called = []
    monkeypatch.setattr(api, "group_symbols", lambda *_: called.append("group_symbols"))
    monkeypatch.setattr(api, "update_data", lambda *_: called.append("update_data"))
    monkeypatch.setattr(api, "clear_prices_file", lambda *_: called.append("clear"))
    monkeypatch.setattr(api, "updating_data", lambda *_: called.append("write"))

    result = api.update_prices("alice")

    assert result is None
    assert called == []


def test_update_prices_refreshes_symbols_in_order(monkeypatch):
    price_records = [{"symbol": "FX:USDSEK"}, {"symbol": "FX:EURNOK"}]
    grouped = [("USD", "SEK"), ("EUR", "NOK")]
    updated_content = [
        {"rates": {"SEK": 10.1}, "date": "2026-03-30"},
        {"rates": {"NOK": 11.2}, "date": "2026-03-30"},
    ]
    call_log = []

    monkeypatch.setattr(api, "account_files_path", lambda username: Path("/unused"))
    monkeypatch.setattr(api, "read_file", lambda file_path: price_records)
    monkeypatch.setattr(api, "group_symbols", lambda records: grouped)
    monkeypatch.setattr(api, "update_data", lambda symbols: updated_content)
    monkeypatch.setattr(
        api, "clear_prices_file", lambda username: call_log.append(("clear", username))
    )
    monkeypatch.setattr(
        api,
        "updating_data",
        lambda symbols, username, content: call_log.append(
            ("update", symbols, username, content)
        ),
    )

    api.update_prices("alice")

    assert call_log == [
        ("clear", "alice"),
        ("update", grouped, "alice", updated_content),
    ]


def test_last_n_day_skips_weekend(monkeypatch):
    class FakeDate(date):
        @classmethod
        def today(cls):
            return cls(2026, 3, 30)  # Monday

    monkeypatch.setattr(api, "date", FakeDate)

    assert api.last_n_day(1) == FakeDate(2026, 3, 27)  # Friday


def test_get_currency_data_for_manual_range_without_end_date(monkeypatch):
    monkeypatch.setattr(api, "prompt_currencies", lambda: ("USD", "SEK"))
    monkeypatch.setattr(api, "clear_terminal", lambda: None)
    monkeypatch.setattr(api, "print_currency_data_submenu", lambda *_: None)
    monkeypatch.setattr(api, "prompt_task", lambda limit: "3")

    answers = iter(["2026-03-01", ""])
    monkeypatch.setattr(api, "get_string", lambda prompt, pattern: next(answers))

    captured = {}

    def fake_api(base, quote, start_date, end_date):
        captured.update(
            {
                "base": base,
                "quote": quote,
                "start_date": start_date,
                "end_date": end_date,
            }
        )
        return {"rates": {"2026-03-01": {"SEK": 10.0}}}

    monkeypatch.setattr(api, "frankfurter_api", fake_api)

    base, quote, rates = api.get_currency_data()

    assert (base, quote) == ("USD", "SEK")
    assert rates == {"2026-03-01": {"SEK": 10.0}}
    assert captured == {
        "base": "USD",
        "quote": "SEK",
        "start_date": "2026-03-01",
        "end_date": None,
    }

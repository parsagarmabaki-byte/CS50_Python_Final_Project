from pathlib import Path

import user_menu as um


def test_prompt_choice_returns_quit_branch(monkeypatch):
    monkeypatch.setattr(um, "get_string", lambda *args, **kwargs: ("Q",))
    monkeypatch.setattr(um, "clear_terminal", lambda: None)

    try:
        um.prompt_choice()
    except SystemExit as exc:
        assert str(exc) == "System Exited"
    else:
        raise AssertionError("prompt_choice() did not exit on Q")


def test_dispatch_menu_routes_to_watchlist(monkeypatch):
    calls = []
    monkeypatch.setattr(
        um, "watchlist", lambda username, task: calls.append((username, task))
    )

    result = um.dispatch_menu({"username": "alice"}, "1", "2")

    assert result is None
    assert calls == [("alice", "2")]


def test_dispatch_menu_returns_true_when_account_deleted(monkeypatch):
    monkeypatch.setattr(um, "account", lambda user, task: True)

    assert um.dispatch_menu({"username": "alice"}, "4", "4") is True


def test_print_watchlist_returns_none_tuple_for_empty_file(monkeypatch):
    monkeypatch.setattr(um, "account_files_path", lambda username: Path("/unused"))
    monkeypatch.setattr(um, "read_file", lambda file_path: [])

    assert um.print_watchlist("alice", "Watchlist") == (None, None, None)


def test_print_watchlist_returns_symbols_and_last_index(tmp_path, monkeypatch):
    user_dir = tmp_path / "alice"
    user_dir.mkdir()
    monkeypatch.setattr(um, "account_files_path", lambda username: user_dir)

    symbols = [{"Stocks": "FX:USDSEK"}, {"Stocks": "FX:EURNOK"}]
    monkeypatch.setattr(um, "read_file", lambda file_path: symbols)

    returned_symbols, file_path, last_index = um.print_watchlist("alice", "Watchlist")

    assert returned_symbols == symbols
    assert file_path == user_dir / "Watchlist.csv"
    assert last_index == 1


def test_remove_symbol_rewrites_both_files_after_valid_selection(monkeypatch):
    watchlist = [{"Stocks": "FX:USDSEK"}, {"Stocks": "FX:EURNOK"}]
    prices = [
        {
            "symbol": "FX:USDSEK",
            "price": "10.0",
            "date": "2026-03-29",
            "source": "Frankfurter",
        },
        {
            "symbol": "FX:EURNOK",
            "price": "11.0",
            "date": "2026-03-29",
            "source": "Frankfurter",
        },
    ]
    written = {}

    monkeypatch.setattr(
        um,
        "print_watchlist",
        lambda username, title: (watchlist.copy(), Path("/unused/Watchlist.csv"), 1),
    )
    monkeypatch.setattr(um, "account_files_path", lambda username: Path("/unused"))
    monkeypatch.setattr(um, "read_file", lambda file_path: prices.copy())
    monkeypatch.setattr(um, "get_string", lambda prompt, pattern: "0")
    monkeypatch.setattr(
        um,
        "rewrite_watchlist_file",
        lambda username, symbols: written.setdefault("watchlist", symbols),
    )
    monkeypatch.setattr(
        um,
        "rewrite_prices_file",
        lambda username, content: written.setdefault("prices", content),
    )

    um.remove_symbol("alice")

    assert written["watchlist"] == [{"Stocks": "FX:EURNOK"}]
    assert written["prices"] == [
        {
            "symbol": "FX:EURNOK",
            "price": "11.0",
            "date": "2026-03-29",
            "source": "Frankfurter",
        }
    ]


def test_update_symbol_updates_selected_price_row(monkeypatch):
    watchlist = [{"Stocks": "FX:USDSEK"}, {"Stocks": "FX:EURNOK"}]
    prices = [
        {
            "symbol": "FX:USDSEK",
            "price": "10.0",
            "date": "2026-03-28",
            "source": "Frankfurter",
        },
        {
            "symbol": "FX:EURNOK",
            "price": "11.0",
            "date": "2026-03-28",
            "source": "Frankfurter",
        },
    ]
    captured = {}

    monkeypatch.setattr(
        um,
        "print_watchlist",
        lambda username, title: (watchlist, Path("/unused/Watchlist.csv"), 1),
    )
    monkeypatch.setattr(um, "get_string", lambda prompt, pattern: "1")
    monkeypatch.setattr(
        um, "group_symbols", lambda rows, symbol_key="Stocks": [("EUR", "NOK")]
    )
    monkeypatch.setattr(
        um, "update_symbol_data", lambda base, quote: (12.25, "2026-03-30")
    )
    monkeypatch.setattr(um, "account_files_path", lambda username: Path("/unused"))
    monkeypatch.setattr(
        um, "read_file", lambda file_path: [row.copy() for row in prices]
    )
    monkeypatch.setattr(
        um,
        "rewrite_prices_file",
        lambda username, content: captured.setdefault("prices", content),
    )

    um.update_symbol("alice")

    assert captured["prices"] == [
        {
            "symbol": "FX:USDSEK",
            "price": "10.0",
            "date": "2026-03-28",
            "source": "Frankfurter",
        },
        {
            "symbol": "FX:EURNOK",
            "price": 12.25,
            "date": "2026-03-30",
            "source": "Frankfurter",
        },
    ]


def test_verification_requires_exact_sequence(monkeypatch):
    prompts = iter(["correct-password", "EXACTLY", "DELETE"])
    monkeypatch.setattr(um.getpass, "getpass", lambda prompt: next(prompts))
    monkeypatch.setattr(
        um, "check_user_password", lambda stored, entered: entered == "correct-password"
    )
    monkeypatch.setattr(um, "prompt_confirmation", lambda: True)

    user = {"username": "alice", "password": "hashed"}

    assert um.verification(user) is True


def test_delete_account_with_verification_removes_user_directory(tmp_path, monkeypatch):
    user_dir = tmp_path / "alice"
    user_dir.mkdir()
    (user_dir / "Prices.csv").write_text("symbol,price,date,source\n", encoding="utf-8")

    monkeypatch.setattr(um, "verification", lambda user: True)
    monkeypatch.setattr(um, "account_files_path", lambda username: user_dir)
    monkeypatch.setattr(um, "clear_terminal", lambda: None)

    result = um.delete_account_with_verification({"username": "alice"})

    assert result is True
    assert not user_dir.exists()

import csv
from pathlib import Path

import login_management as lm


def test_accounts_path_creates_csv_with_header(tmp_path, monkeypatch):
    monkeypatch.setattr(
        lm, "__file__", str(tmp_path / "terminal_ui" / "login_management.py")
    )

    accounts_file = lm.accounts_path()

    assert accounts_file.exists()
    assert accounts_file.read_text(encoding="utf-8").splitlines() == [
        "username,password,email,date"
    ]


def test_account_create_directory_builds_both_csv_files(tmp_path, monkeypatch):
    root = tmp_path / "csv_files" / "account_directory"
    monkeypatch.setattr(lm.Account, "get_directory", classmethod(lambda cls: root))

    account_dir = lm.Account.create_account_directory("alice")

    assert account_dir == root / "alice"
    assert (account_dir / "Watchlist.csv").exists()
    assert (account_dir / "Prices.csv").exists()
    assert (account_dir / "Watchlist.csv").read_text(encoding="utf-8").splitlines() == [
        "Stocks"
    ]
    assert (account_dir / "Prices.csv").read_text(encoding="utf-8").splitlines() == [
        "symbol,price,date,source"
    ]


def test_hash_password_accepts_valid_length_and_verifies():
    hashed = lm.hash_password("abc123")

    assert isinstance(hashed, str)
    assert hashed != "abc123"
    assert lm.check_user_password(hashed, "abc123") is True
    assert lm.check_user_password(hashed, "wrong") is False


def test_hash_password_rejects_too_short_password():
    assert lm.hash_password("ab") is None


def test_read_file_returns_dict_rows_without_header(tmp_path):
    csv_file = tmp_path / "Accounts.csv"
    csv_file.write_text(
        "username,password,email,date\n" "alice,hashed,alice@example.com,03/30/26\n",
        encoding="utf-8",
    )

    assert lm.read_file(csv_file, print_file_empty=False) == [
        {
            "username": "alice",
            "password": "hashed",
            "email": "alice@example.com",
            "date": "03/30/26",
        }
    ]


def test_find_account_returns_matching_record_and_index():
    hashed = lm.hash_password("secret123")
    accounts = [
        {
            "username": "alice",
            "password": hashed,
            "email": "a@a.com",
            "date": "03/30/26",
        },
        {"username": "bob", "password": hashed, "email": "b@b.com", "date": "03/30/26"},
    ]

    account, index = lm.find_account("alice", "secret123", accounts)

    assert account == accounts[0]
    assert index == 0


def test_find_account_returns_none_for_wrong_password():
    hashed = lm.hash_password("secret123")
    accounts = [
        {
            "username": "alice",
            "password": hashed,
            "email": "a@a.com",
            "date": "03/30/26",
        }
    ]

    assert lm.find_account("alice", "wrong", accounts) == (None, None)


def test_check_availability_detects_taken_username(tmp_path):
    csv_file = tmp_path / "Accounts.csv"
    csv_file.write_text(
        "username,password,email,date\n" "alice,hashed,alice@example.com,03/30/26\n",
        encoding="utf-8",
    )

    assert lm.check_availability("alice", csv_file) is False
    assert lm.check_availability("bob", csv_file) is True


def test_get_string_returns_captured_groups_after_invalid_attempt(monkeypatch):
    answers = iter(["bad", "1.2"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))

    result = lm.get_string(
        "Choice: ",
        r"^(?:(1)(?:\.([123]))?)$",
        get_groups=True,
    )

    assert result == ("1", "2")

import tempfile
from pathlib import Path
from datetime import date

from login_management import read_file
from API_management import group_symbols, last_n_day

from login_management import find_account, check_availability, is_email_valid
from user_menu import prompt_confirmation, verification, delete_account_with_verification
import shutil


def test_read_file_empty(tmp_path):
    """``read_file`` should return an empty list when the CSV has no rows."""
    p = tmp_path / "empty.csv"
    # create an empty file (no header, no rows is fine)
    p.write_text("")
    assert read_file(p) == []


def test_group_symbols():
    """Ensure ``group_symbols`` parses FX: pairs correctly."""
    sample = [{"symbol": "FX:USDSEK"}, {"symbol": "FX:EURUSD"}]
    out = group_symbols(sample)
    assert out == [("USD", "SEK"), ("EUR", "USD")]


def test_find_account(tmp_path):
    """The finder returns the record and index when present."""
    file = tmp_path / "acct.csv"
    file.write_text("username,password,email,date\nfoo,pass,a@b.com,01/01/20\n")
    accounts = read_file(file)
    acc, idx = find_account("foo", "pass", accounts)
    assert acc["email"] == "a@b.com"
    assert idx == 0

    acc, idx = find_account("foo", "wrong", accounts)
    assert acc is None and idx is None


def test_check_availability(tmp_path, capsys):
    """Username availability checks existing entries and prints when taken."""
    file = tmp_path / "avail.csv"
    file.write_text("username,password,email,date\nbar,pass,foo@x.com,02/02/21\n")
    assert check_availability("baz", str(file))
    assert not check_availability("bar", str(file))
    captured = capsys.readouterr()
    assert "Username not available" in captured.out


def test_is_email_valid():
    """Validation returns True for good addresses, False for bad."""
    assert is_email_valid("test@example.com")
    assert not is_email_valid("not-an-email")


def test_group_symbols_with_custom_key():
    """Ensure ``group_symbols`` respects a non-default dict_value."""
    sample = [{"Stocks": "FX:DKKNOK"}]
    out = group_symbols(sample, dict_value="Stocks")
    assert out == [("DKK", "NOK")]


def test_update_prices_empty(tmp_path, capsys, monkeypatch):
    """When Prices.csv is empty, ``update_prices`` prints a warning."""
    # create minimal account dir structure
    acct_dir = tmp_path / "user"
    acct_dir.mkdir()
    prices = acct_dir / "Prices.csv"
    prices.write_text("")
    from API_management import update_prices
    # override path resolution used inside update_prices
    monkeypatch.setattr("API_management.account_files_path", lambda u: acct_dir)

    update_prices("ignored")  # username argument is irrelevant now
    captured = capsys.readouterr()
    assert "FILES ARE EMPTY" in captured.out


def test_print_watchlist_empty(tmp_path, capsys, monkeypatch):
    """``print_watchlist`` returns None and warns if the file has no rows."""
    acct_dir = tmp_path / "user2"
    acct_dir.mkdir()
    watch = acct_dir / "Watchlist.csv"
    watch.write_text("")
    from user_menu import print_watchlist
    # patch path resolution inside user_menu
    monkeypatch.setattr("user_menu.account_files_path", lambda u: acct_dir)

    result,hello,bye = print_watchlist("ignored", "Watchlist")
    assert result is None 
    captured = capsys.readouterr()
    assert "FILES ARE EMPTY" in captured.out

def test_prompt_confirmation(monkeypatch):
    """Different inputs are interpreted as confirmation correctly."""
    monkeypatch.setattr("builtins.input", lambda _: "Yes")
    assert prompt_confirmation()
    monkeypatch.setattr("builtins.input", lambda _: "nope")
    assert not prompt_confirmation()


def test_verification_flow(monkeypatch, capsys):
    """Verify that the multi-step verification respects each step."""
    user = {"username": "u", "password": "pw"}
    seq = iter(["pw", "EXACTLY", "DELETE", "yes"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(seq))
    monkeypatch.setattr("user_menu.prompt_confirmation", lambda: True)
    assert verification(user)
    # failure at step 2
    seq = iter(["pw", "wrong"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(seq))
    assert not verification(user)


def test_delete_account(tmp_path, monkeypatch):
    """Deleting an account removes the directory after verification."""
    acct_dir = tmp_path / "acct"
    acct_dir.mkdir()
    # put a dummy file inside
    (acct_dir / "foo.txt").write_text("x")
    monkeypatch.setattr("user_menu.account_files_path", lambda u: acct_dir)
    monkeypatch.setattr("user_menu.verification", lambda u: True)
    assert delete_account_with_verification({"username": "any"})
    assert not acct_dir.exists()

def test_last_n_day():
    """The function should return a date earlier than today for n>=1."""
    result = last_n_day(1)
    assert isinstance(result, date)
    assert result < date.today()


if __name__ == "__main__":
    # simple runner without pytest
    tests = [
        test_read_file_empty,
        test_group_symbols,
        test_last_n_day,
    ]
    for func in tests:
        try:
            # for the temp file test we need a temporary directory
            if func is test_read_file_empty:
                with tempfile.TemporaryDirectory() as td:
                    test_read_file_empty(Path(td))
            else:
                func()
            print(f"{func.__name__}: PASS")
        except AssertionError as err:
            print(f"{func.__name__}: FAIL ({err})")
        except Exception as exc:
            print(f"{func.__name__}: ERROR ({exc})")
    

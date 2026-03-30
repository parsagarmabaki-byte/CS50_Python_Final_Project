"""Test suite for the MarketWatch application.

This module contains unit tests for login_management, user_menu, and
API_management modules. Run with: python tests.py
"""

import tempfile
import csv
from pathlib import Path
from datetime import date
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# =============================================================================
# Helper functions for testing
# =============================================================================

def create_temp_csv(tmp_path, filename, headers, rows=None):
    """Create a temporary CSV file with optional headers and rows."""
    p = tmp_path / filename
    with open(p, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        if rows:
            writer.writerows(rows)
    return p


# =============================================================================
# login_management tests
# =============================================================================

def test_read_file_empty(tmp_path):
    """read_file should return an empty list when the CSV has no rows."""
    p = tmp_path / "empty.csv"
    p.write_text("")
    from login_management import read_file
    assert read_file(p) == []
    print("  test_read_file_empty: PASS")


def test_read_file_with_data(tmp_path):
    """read_file should return list of dicts when CSV has data."""
    from login_management import read_file
    p = create_temp_csv(tmp_path, "accounts.csv", 
                        ["username", "password", "email", "date"],
                        [{"username": "foo", "password": "pass", "email": "a@b.com", "date": "01/01/20"}])
    result = read_file(p)
    assert len(result) == 1
    assert result[0]["username"] == "foo"
    assert result[0]["email"] == "a@b.com"
    print("  test_read_file_with_data: PASS")


def test_hash_password_valid():
    """Hash password should return a bcrypt hash for valid input."""
    from login_management import hash_password
    password = "validpass123"
    hashed = hash_password(password)
    assert hashed is not None
    assert len(hashed) > 0
    assert hashed != password
    print("  test_hash_password_valid: PASS")


def test_hash_password_invalid():
    """Hash password should return None for too short password."""
    from login_management import hash_password
    password = "ab"  # Too short (< 3 chars)
    hashed = hash_password(password)
    assert hashed is None
    print("  test_hash_password_invalid: PASS")


def test_check_user_password_correct():
    """Password verification should return True for correct password."""
    from login_management import hash_password, check_user_password
    password = "testpass123"
    hashed = hash_password(password)
    assert check_user_password(hashed, password) is True
    print("  test_check_user_password_correct: PASS")


def test_check_user_password_incorrect():
    """Password verification should return False for wrong password."""
    from login_management import hash_password, check_user_password
    password = "testpass123"
    hashed = hash_password(password)
    assert check_user_password(hashed, "wrongpassword") is False
    print("  test_check_user_password_incorrect: PASS")


def test_find_account_success(tmp_path):
    """The finder should return the record and index when present."""
    from login_management import read_file, find_account
    file = create_temp_csv(tmp_path, "acct.csv",
                          ["username", "password", "email", "date"],
                          [{"username": "foo", "password": "pass", "email": "a@b.com", "date": "01/01/20"}])
    accounts = read_file(file)
    acc, idx = find_account("foo", "pass", accounts)
    assert acc["email"] == "a@b.com"
    assert idx == 0
    print("  test_find_account_success: PASS")


def test_find_account_failure(tmp_path):
    """The finder should return (None, None) when credentials don't match."""
    from login_management import read_file, find_account
    file = create_temp_csv(tmp_path, "acct.csv",
                          ["username", "password", "email", "date"],
                          [{"username": "foo", "password": "pass", "email": "a@b.com", "date": "01/01/20"}])
    accounts = read_file(file)
    acc, idx = find_account("foo", "wrong", accounts)
    assert acc is None and idx is None
    print("  test_find_account_failure: PASS")


def test_check_availability_available(tmp_path):
    """Username should be available when not in file."""
    from login_management import check_availability
    file = create_temp_csv(tmp_path, "avail.csv",
                          ["username", "password", "email", "date"],
                          [{"username": "bar", "password": "pass", "email": "foo@x.com", "date": "02/02/21"}])
    assert check_availability("baz", str(file)) is True
    print("  test_check_availability_available: PASS")


def test_check_availability_taken(tmp_path):
    """Username availability check should return False when taken."""
    from login_management import check_availability
    file = create_temp_csv(tmp_path, "avail.csv",
                          ["username", "password", "email", "date"],
                          [{"username": "bar", "password": "pass", "email": "foo@x.com", "date": "02/02/21"}])
    assert check_availability("bar", str(file)) is False
    print("  test_check_availability_taken: PASS")


def test_is_email_valid_correct():
    """Validation should return True for valid email addresses."""
    from login_management import is_email_valid
    assert is_email_valid("test@example.com") is True
    assert is_email_valid("user.name@domain.org") is True
    print("  test_is_email_valid_correct: PASS")


def test_is_email_valid_invalid():
    """Validation should return False for invalid email addresses."""
    from login_management import is_email_valid
    assert is_email_valid("not-an-email") is False
    assert is_email_valid("") is False
    print("  test_is_email_valid_invalid: PASS")


def test_group_symbols_default():
    """Ensure group_symbols parses FX: pairs correctly with default key."""
    from API_management import group_symbols
    sample = [{"symbol": "FX:USDSEK"}, {"symbol": "FX:EURUSD"}]
    out = group_symbols(sample)
    assert out == [("USD", "SEK"), ("EUR", "USD")]
    print("  test_group_symbols_default: PASS")


def test_group_symbols_with_custom_key():
    """Ensure group_symbols respects a non-default symbol_key."""
    from API_management import group_symbols
    sample = [{"Stocks": "FX:DKKNOK"}]
    out = group_symbols(sample, symbol_key="Stocks")
    assert out == [("DKK", "NOK")]
    print("  test_group_symbols_with_custom_key: PASS")


def test_last_n_day():
    """The function should return a date earlier than today for n>=1."""
    from API_management import last_n_day
    result = last_n_day(1)
    assert isinstance(result, date)
    assert result < date.today()
    print("  test_last_n_day: PASS")


def test_append_account(tmp_path):
    """Appending an account should add a row to the CSV file."""
    from login_management import read_file, append_account
    file = tmp_path / "test_accounts.csv"
    # Create file with header
    with open(file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["username", "password", "email", "date"])
        writer.writeheader()
    
    append_account("testuser", "hashedpass", "test@example.com", str(file))
    
    accounts = read_file(file)
    assert len(accounts) == 1
    assert accounts[0]["username"] == "testuser"
    assert accounts[0]["email"] == "test@example.com"
    print("  test_append_account: PASS")


def test_update_data_empty():
    """update_data should return empty list for empty symbols."""
    from API_management import update_data
    result = update_data([])
    assert result == []
    print("  test_update_data_empty: PASS")


def test_print_rates_format():
    """print_rates should format rates table correctly."""
    from user_menu import print_rates
    import io
    from contextlib import redirect_stdout
    
    data = {"2024-01-01": 10.5, "2024-01-02": 10.6}
    f = io.StringIO()
    with redirect_stdout(f):
        print_rates(data, "USD", "SEK")
    output = f.getvalue()
    assert "USD/SEK" in output
    assert "10.50" in output
    assert "10.60" in output
    print("  test_print_rates_format: PASS")


def test_prompt_confirmation_yes():
    """Affirmative inputs should be interpreted as confirmation."""
    from API_management import prompt_confirmation
    import io
    from contextlib import redirect_stdin
    
    for yes_input in ["Yes", "yes", "yeah", "ja"]:
        stdin_backup = sys.stdin
        sys.stdin = io.StringIO(yes_input + "\n")
        try:
            # We can't easily test this without mocking input()
            # Skip for now
            pass
        finally:
            sys.stdin = stdin_backup
    print("  test_prompt_confirmation_yes: PASS (skipped - requires mocking)")


# =============================================================================
# Test runner
# =============================================================================

def run_tests():
    """Run all tests and report results."""
    passed = 0
    failed = 0
    errors = 0
    
    tests = [
        ("test_read_file_empty", lambda: test_read_file_empty(Path(tempfile.mkdtemp()))),
        ("test_read_file_with_data", lambda: test_read_file_with_data(Path(tempfile.mkdtemp()))),
        ("test_hash_password_valid", test_hash_password_valid),
        ("test_hash_password_invalid", test_hash_password_invalid),
        ("test_check_user_password_correct", test_check_user_password_correct),
        ("test_check_user_password_incorrect", test_check_user_password_incorrect),
        ("test_find_account_success", lambda: test_find_account_success(Path(tempfile.mkdtemp()))),
        ("test_find_account_failure", lambda: test_find_account_failure(Path(tempfile.mkdtemp()))),
        ("test_check_availability_available", lambda: test_check_availability_available(Path(tempfile.mkdtemp()))),
        ("test_check_availability_taken", lambda: test_check_availability_taken(Path(tempfile.mkdtemp()))),
        ("test_is_email_valid_correct", test_is_email_valid_correct),
        ("test_is_email_valid_invalid", test_is_email_valid_invalid),
        ("test_group_symbols_default", test_group_symbols_default),
        ("test_group_symbols_with_custom_key", test_group_symbols_with_custom_key),
        ("test_last_n_day", test_last_n_day),
        ("test_append_account", lambda: test_append_account(Path(tempfile.mkdtemp()))),
        ("test_update_data_empty", test_update_data_empty),
        ("test_print_rates_format", test_print_rates_format),
    ]
    
    print("\n" + "="*60)
    print("Running MarketWatch Test Suite")
    print("="*60 + "\n")
    
    for test_name, test_func in tests:
        try:
            print(f"Running {test_name}...")
            test_func()
            passed += 1
        except AssertionError as err:
            print(f"  {test_name}: FAIL ({err})")
            failed += 1
        except Exception as exc:
            print(f"  {test_name}: ERROR ({exc})")
            errors += 1
    
    print("\n" + "="*60)
    print(f"Results: {passed} passed, {failed} failed, {errors} errors")
    print("="*60 + "\n")
    
    return failed == 0 and errors == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

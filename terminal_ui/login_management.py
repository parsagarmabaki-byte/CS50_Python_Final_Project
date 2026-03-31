"""Login and account management module for the MarketWatch application.

This module handles user authentication, registration, password hashing,
email validation, and account file management.
"""

from email_validator import validate_email, EmailNotValidError
import sys
import csv
import datetime
import bcrypt
import getpass
from pathlib import Path
import re
import os


def clear_terminal():
    """Clear the terminal screen (cross-platform)."""
    os.system("cls" if os.name == "nt" else "clear")


class Account:
    """Represents a user account and manages its file directory.

    Attributes:
        directory (Path): base path for all user account folders.
    """

    @classmethod
    def get_directory(cls) -> Path:
        """Get the base directory for account storage, creating it if needed.

        The path is calculated relative to the project root (parent of terminal_ui).

        Returns:
            Path: Path to the account directory.
        """
        base = Path(__file__).resolve().parent
        project_root = base.parent
        directory = project_root.joinpath("csv_files", "account_directory")
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    @property
    def directory(self) -> Path:
        """Get the account directory path."""
        return self.get_directory()

    def __init__(self, username, password, email=None):
        """Initialize the account object and ensure its directory/files exist.

        Args:
            username (str): new account username.
            password (str): associated password.
            email (str, optional): email address.
        """
        self.username = username
        self.password = password
        self.email = email
        self.path = self.create_account_directory(username)

    @classmethod
    def create_account_directory(cls, username):
        """Create filesystem directory for a given username with default CSVs.

        Args:
            username (str): the account name for which to create directory.

        Returns:
            Path: path to the newly created directory.
        """
        account_dir = cls.get_directory().joinpath(username)
        account_dir.mkdir(parents=True, exist_ok=True)

        for type_file in ["Watchlist", "Prices"]:
            file_path = account_dir.joinpath(f"{type_file}.csv")
            file_path.touch(exist_ok=True)
            cls.file_specification(file_path, type_file, username)
        return account_dir

    @staticmethod
    def file_specification(file_path: str, file_type: str, username: str) -> None:
        """Ensure a CSV file has the correct header row based on its type.

        Args:
            file_path (str): path of the file to operate on.
            file_type (str): one of "Watchlist" or "Prices".
            username (str): account owner name (unused except logging).

        Returns:
            None
        """
        with open(file_path, "a", newline="") as f:
            if file_type == "Watchlist":
                writer = csv.DictWriter(f, fieldnames=["Stocks"])
            elif file_type == "Prices":
                writer = csv.DictWriter(
                    f, fieldnames=["symbol", "price", "date", "source"]
                )
            writer.writeheader()


def account_files_path(username):
    """Compute the path to the given user's account directory.

    The path is calculated relative to the project root (parent of terminal_ui)
    to ensure it works regardless of the current working directory.

    Args:
        username (str): Account identifier.

    Returns:
        Path: Absolute path to the user's folder.
    """
    base = Path(__file__).resolve().parent
    project_root = base.parent
    return project_root.joinpath("csv_files", "account_directory", username)


def login_options() -> int:
    """Prompt for login/register/exit choice and validate input.

    Displays a menu allowing the user to log in, register a new account,
    or exit the program. Continues prompting until a valid choice is made.

    Returns:
        int: 1 for login, 2 for registration. Choice 3 exits the program.
    """
    while True:
        choice = int(
            get_string(
                "(1) Log in \n(2) Register a new account \n(3) Exit \nChoice: ",
                r"^[123]$",
            )
        )
        print()
        if choice == 3:
            clear_terminal()
            sys.exit("EXIT SUCCESSFUL")
        return choice


def accounts_path():
    """Return the path to the main accounts CSV file, creating it if needed.

    The path is calculated relative to the project root (parent of terminal_ui)
    to ensure it works regardless of the current working directory.

    Returns:
        Path: Path to the Accounts.csv file.
    """
    base = Path(__file__).resolve().parent
    # Go up one level from terminal_ui to project root
    project_root = base.parent
    directory = project_root.joinpath("csv_files")
    directory.mkdir(parents=True, exist_ok=True)
    file_path = directory.joinpath("Accounts.csv")
    if not file_path.exists():
        with open(file_path, "w", newline="") as f:
            writer = csv.DictWriter(
                f, fieldnames=["username", "password", "email", "date"]
            )
            writer.writeheader()
    return file_path


def prompt_login():
    """Interactively prompt for username/password and verify against stored accounts.

    Returns:
        tuple: (user_account: dict|None, account_index: int|None, registered_accounts: list)
    """
    user_account = None
    while user_account is None:
        username = input("Username: ").strip()
        if not username:
            return None, None, None

        password = getpass.getpass("Password (hidden): ").strip()

        registered_accounts: list = read_file(accounts_path(), print_file_empty=False)
        user_account, account_index = find_account(
            username, password, registered_accounts
        )
    return user_account, account_index, registered_accounts


def hash_password(entered_password: str) -> str:
    """Hash a password using bcrypt after validating its length.

    Validates that the password is between 3 and 24 characters.
    If invalid, prints an error message and returns None.

    Args:
        entered_password (str): The plain text password to hash.

    Returns:
        str: The hashed password, or None if validation fails.
    """
    if re.fullmatch(r".{3,24}", entered_password):
        return bcrypt.hashpw(entered_password.encode(), bcrypt.gensalt()).decode()
    print("\nInvalid Password!\n")
    return None


def create_account() -> bool:
    """Guide the user through creating a new account and persist it.

    Prompts for username, validates availability, then collects password
    and email. Creates the account directory and appends to the accounts CSV.

    Returns:
        bool: True if account was created successfully, False otherwise.
    """
    accounts_csv_path = accounts_path()

    username = get_valid_username(accounts_csv_path)
    if not username:
        return False

    hashed_password = get_valid_password()
    if not hashed_password:
        return False

    email = get_valid_email()
    if not email:
        return False

    acc = Account(username, hashed_password, email)
    append_account(acc.username, acc.password, acc.email, accounts_csv_path)
    return True


def get_valid_username(accounts_csv_path: Path) -> str | None:
    """Prompt the user for a valid username and check its availability.

    Continues prompting until a valid, available username is entered or
    the user provides an empty input (which returns None).

    Args:
        accounts_csv_path (Path): Path to the accounts CSV file to check availability.

    Returns:
        str | None: The validated username, or None if input is blank.
    """
    username_available = False
    while not username_available:
        username = input("Username: ").strip()
        if not username:
            return None
        if not re.search(r"^[A-Za-z0-9_ ]{3,24}$", username):
            print("\nINVALID USERNAME\n")
            continue
        username_available = check_availability(username, accounts_csv_path)
    return username


def get_valid_password() -> str | None:
    """Prompt the user for a valid password and return its bcrypt hash.

    Continues prompting until a valid password (3-24 characters) is entered
    or the user provides an empty input (which returns None).

    Returns:
        str | None: The hashed password, or None if input is blank.
    """
    hashed_password = None
    while not hashed_password:
        entered_password = getpass.getpass("Password (hidden): ").strip()
        if not entered_password:
            return None
        hashed_password = hash_password(entered_password)
    return hashed_password


def append_account(
    username: str, password: str, email: str, accounts_file_path: str
) -> None:
    """Append a new account row to the accounts CSV file.

    Args:
        username (str): The username for the new account.
        password (str): The hashed password.
        email (str): The user's email address.
        accounts_file_path (str): Path to the accounts CSV file.

    Returns:
        None
    """
    current_date = datetime.datetime.now()
    try:
        with open(accounts_file_path, "a", newline="") as file:
            writer = csv.DictWriter(
                file, fieldnames=["username", "password", "email", "date"]
            )
            writer.writerow(
                {
                    "username": username,
                    "password": password,
                    "email": email,
                    "date": current_date.strftime("%x"),
                }
            )
    except FileNotFoundError:
        sys.exit("FILE NOT FOUND,EXITING")


def read_file(file_path: Path | str, print_file_empty: bool = True) -> list:
    """Read a CSV file and return a list of row dictionaries.

    Args:
        file_path (Path | str): Path to the CSV file to read.
        print_file_empty (bool): If True, prints a message when the file is empty.

    Returns:
        list: List of dictionaries representing each row in the CSV.
    """
    accounts = []
    with open(file_path) as f:
        reader = csv.DictReader(f)
        for acc in reader:
            accounts.append(acc)
    if print_file_empty and not accounts:
        clear_terminal()
        print("""=====================================
        FILES ARE EMPTY
=====================================\n""")
    return accounts


def find_account(
    username: str, password: str, accounts: list[dict]
) -> tuple[dict, int] | tuple[None, None]:
    """Search for a username/password pair in the accounts list.

    Iterates through the accounts list to find a matching username and
    verifies the password using bcrypt.

    Args:
        username (str): The username to search for.
        password (str): The plain text password to verify.
        accounts (list[dict]): List of account records from the CSV.

    Returns:
        tuple: (account dict, index) if found; otherwise (None, None).
    """
    for index, acc in enumerate(accounts):
        if acc.get("username") == username and check_user_password(
            acc.get("password"), password
        ):
            return acc, index
    print("\nUsername or Password is incorrect\n")
    return None, None


def check_user_password(stored_password: str, entered_password: str) -> bool:
    """Verify a plain text password against a stored bcrypt hash.

    Args:
        stored_password (str): The bcrypt-hashed password from storage.
        entered_password (str): The plain text password to verify.

    Returns:
        bool: True if the password matches, False otherwise.
    """
    if bcrypt.checkpw(entered_password.encode(), stored_password.encode()):
        return True
    return False


def get_valid_email() -> str | None:
    """Prompt the user for a valid email address.

    Continues prompting until a valid email is entered or the user
    provides an empty input (which returns None).

    Returns:
        str | None: The validated email address, or None if input is blank.
    """
    is_valid = False
    while not is_valid:
        email = input("Email: ").strip()
        if not email:
            return None
        is_valid = is_email_valid(email)
    return email


def get_string(prompt: str, pattern: str, get_groups: bool = False) -> str | tuple:
    """Generic input prompt that enforces a regex pattern.

    Continues prompting until the user input matches the specified regex pattern.
    Optionally returns captured groups instead of the full match.

    Args:
        prompt (str): The text to display when prompting for input.
        pattern (str): The regex pattern that input must match.
        get_groups (bool): If True, returns captured groups as a tuple.

    Returns:
        str | tuple: The validated input string, or a tuple of captured groups.
    """
    while True:
        user_input: str = input(prompt).strip()
        if captured := re.search(pattern, user_input):
            if get_groups:
                return tuple(g for g in captured.groups() if g is not None)
            return user_input
        print("Input is not valid\n")


def check_availability(username: str, accounts_file_path: str, print_error=True) -> bool:
    """Check whether a username is already registered in the accounts file.

    Args:
        username (str): The username to check for availability.
        accounts_file_path (str): Path to the accounts CSV file.
        print_error (bool): If True, prints a message when username is already taken.

    Returns:
        bool: True if the username is available, False if already taken.
    """
    accounts = read_file(accounts_file_path, print_file_empty=False)
    for acc in accounts:
        if acc.get("username") == username:
            if print_error:
                print("\nUsername not available\n")
            return False
    return True


def is_email_valid(email: str) -> bool:
    """Validate email format using the email_validator library.

    Args:
        email (str): The email address to validate.

    Returns:
        bool: True if the email is valid, False otherwise.
    """
    try:
        validate_email(email, check_deliverability=False)
        return True
    except EmailNotValidError:
        print("Email not found")
        return False

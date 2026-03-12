from email_validator import validate_email, EmailNotValidError
import sys, csv, datetime
from pathlib import Path
import re, csv, os


class Account:
    """Represents a user account and manages its file directory.

    Attributes:
        directory (Path): base path for all user account folders.
    """

    directory = (
        Path("final_project")
        .resolve()
        .parent.joinpath("csv_files")
        .joinpath("account_directory")
    )

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
        account_dir = cls.directory.joinpath(username)
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
        # Use newline="" so csv.writer does not insert extra blank lines on Windows
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

    The previous implementation assumed the workspace root was a folder
    literally named ``final_project`` which breaks when cloning into a
    differently‑named directory or running from elsewhere.  Instead we derive the
    root dynamically using this module's location and walk up to the
    ``csv_files/account_directory`` subfolder.  This makes the function
    portable across machines.

    Args:
        username (str): account identifier.

    Returns:
        Path: absolute path to the user's folder.
    """
    base = Path(__file__).resolve().parent
    # project root is one level up from this module
    project_root = base
    # if this file is already inside a subfolder, adjust accordingly
    # (in this simple project it's the workspace root)
    return project_root.joinpath("csv_files", "account_directory", username)


def login_options() -> int:
    """Prompt for login/register/exit choice and validate input.

    Returns:
        int: 1 for login, 2 for registration, 3 for exit (which also exits program).
    """
    while 1:
        try:
            options = int(
                input("(1) Log in \n(2) Register a new account \n(3) Exit \nChoice: ")
            )

            if options > 3 or options < 1:
                raise ValueError

            if options == 3:
                sys.exit("\nEXIT SUCCESSFUL")

            return options

        except ValueError:
            print("\nINVALID INPUT!\n")
            continue


def accounts_path():
    """Return the path to the main accounts CSV file.

    Returns:
        Path
    """
    return (
        Path("final_project")
        .resolve()
        .parent.joinpath("csv_files")
        .joinpath("Accounts.csv")
    )


def prompt_login():
    """Interactively prompt for username/password and verify against stored accounts.

    Returns:
        tuple: (user_account: dict|None, account_index: int|None, registered_accounts: list)
    """
    user_account = None
    while user_account is None:
        username = input("Username: ")
        if not username:
            break
        password = input("Password: ")

        registered_accounts: list = read_file(accounts_path())
        user_account, account_index = find_account(
            username, password, registered_accounts
        )
    return user_account, account_index, registered_accounts


def create_account():
    """Guide the user through creating a new account and persist it.

    Returns:
        None
    """
    accounts_csv_path = accounts_path()
    status = False
    while status is False:
        username, password = get_username_password()
        status = check_availability(username, accounts_csv_path)

    email = enter_email()
    acc = Account(username, password, email)
    append_account(acc.username, acc.password, acc.email, accounts_csv_path)


def append_account(username: str, password: str, email: str, csv_File: str):
    """Append a new account row to the accounts CSV file.

    Args:
        username (str)
        password (str)
        email (str)
        csv_File (str): path to CSV file

    Returns:
        None
    """
    date = datetime.datetime.now()
    try:
        with open(csv_File, "a", newline="") as file:
            writer = csv.DictWriter(
                file, fieldnames=["username", "password", "email", "date"]
            )
            writer.writerow(
                {
                    "username": username,
                    "password": password,
                    "email": email,
                    "date": date.strftime("%x"),
                }
            )
    except FileNotFoundError:
        sys.exit("FILE NOT FOUND,EXITING")


def read_file(file) -> list:
    """Read a CSV file and return a list of row dictionaries.

    Args:
        file (Path|str): path to CSV file.

    Returns:
        list: of dicts representing rows.
    """
    accounts = []
    with open(file) as f:
        reader = csv.DictReader(f)
        for acc in reader:
            accounts.append(acc)
    if not accounts:
        os.system("cls")
        print("""=====================================
        FILES ARE EMPTY
=====================================\n""")
    return accounts


def find_account(username: str, password: str, accounts: list[dict]) -> dict | int:
    """Search for a username/password pair in the accounts list.

    Args:
        username (str)
        password (str)
        accounts (list[dict]): list of account records.

    Returns:
        tuple: (account dict, index) if found; otherwise (None, None).
    """
    for index, acc in enumerate(accounts):
        if acc.get("username") == username and acc.get("password") == password:
            return acc, index
    print("\nUsername or Password is incorrect\n")
    return None, None


def enter_email() -> str:
    """Prompt the user for a valid email; return None if input blank.

    Returns:
        str | None
    """
    status = False
    while status is not True:
        email = input("Email: ")
        if email == "":
            return None
        status = is_email_valid(email)
    return email


def get_username_password() -> tuple:
    """Prompt and validate username and password strings.

    Returns:
        tuple[str, str]
    """
    username = get_string("Username: ", r"^[A-Za-z0-9_ ]{3,24}$")
    password = get_string("Password: ", r".{3,24}")
    return username, password


def get_string(input_string: str, pattern: str, get_groups: bool = False) -> str:
    """Generic input prompt that enforces a regex pattern.

    Args:
        input_string (str): prompt text.
        pattern (str): regex pattern to match.
        get_groups (bool): if True, return matching groups tuple.

    Returns:
        str or tuple
    """
    while True:
        string: str = input(input_string)
        if captured := re.search(pattern, string):
            if get_groups is True:
                return tuple(g for g in captured.groups() if g is not None)
            return string
        print("Input is not valid")


def check_availability(username: str, file: str) -> bool:
    """Check whether a username is already registered.

    Args:
        username (str)
        file (str): path to accounts CSV.

    Returns:
        bool: True if username is available.
    """
    accounts = read_file(file)
    for acc in accounts:
        if acc.get("username") == username:
            print("\nUsername not available\n")
            return False
    return True


def is_email_valid(email: str) -> bool:
    """Validate email format using email_validator library.

    Args:
        email (str)

    Returns:
        bool: True if valid, False otherwise.
    """
    try:
        validate_email(email, check_deliverability=False)
        return True
    except EmailNotValidError:
        print("Email not found")
        return False

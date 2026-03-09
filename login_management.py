from email_validator import validate_email,EmailNotValidError
import sys, csv, datetime
from pathlib import Path
import re,csv


class Acounts:
    directory = (
        Path("final_project")
        .resolve()
        .parent.joinpath("csv_files")
        .joinpath("acount_directory")
    )

    def __init__(self, username, password, email=None):
        self.username = username
        self.password = password
        self.email = email
        self.path = self.create_acc_directory(username)

    @classmethod
    def create_acc_directory(cls, username):
        acount_dir = cls.directory.joinpath(username)
        acount_dir.mkdir(parents=True, exist_ok=True)

        for type_file in ["Watchlist", "Prices"]:
            file_path = acount_dir.joinpath(f"{type_file}.csv")
            file_path.touch(exist_ok=True)
            cls.file_specification(file_path, type_file, username)
        return acount_dir

    @staticmethod
    def file_specification(file_path: str, file_type: str, username: str) -> None:
        with open(file_path, "a") as f:
            if file_type == "Watchlist":
                writer = csv.DictWriter(f, fieldnames=["Stocks"])
            elif file_type == "Prices":
                writer = csv.DictWriter(
                    f, fieldnames=["symbol", "price", "date", "source"]
                )
            writer.writeheader()


def acount_files_path(username):
    return (
        Path("final_project")
        .resolve()
        .parent.joinpath("csv_files")
        .joinpath("acount_directory")
        .joinpath(username)
    )


def login_options() -> int:
    while 1:
        try:
            options = int(
                input("(1) Log in \n(2) Register a new acount \n(3) Exit \nChoice: ")
            )

            if options > 3 or options < 1:
                raise ValueError

            if options == 3:
                sys.exit("\nEXIT SUCCESSFUL")

            return options

        except ValueError:
            print("\nINVALID INPUT!\n")
            continue


def acounts_path():
    return (
        Path("final_project")
        .resolve()
        .parent.joinpath("csv_files")
        .joinpath("Acounts.csv")
    )


def login():
    user_acount = None
    while user_acount is None:
        username = input("Username: ")
        if not username:
            break
        password = input("Password: ")

        registred_acounts: list = read_file(acounts_path())
        user_acount, acount_num = find_acount(username, password, registred_acounts)
    return user_acount, acount_num, registred_acounts


def create_acount():
    registred_acount_path = acounts_path()
    status = False
    while status is False:
        username, password = get_username_password()
        status = check_availability(username, registred_acount_path)

    email = enter_email()
    acc = Acounts(username, password, email)
    append_acount(acc.username, acc.password, acc.email, registred_acount_path)


def append_acount(username: str, password: str, email: str, csv_File: str):
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
    acounts = []
    with open(file) as f:
        reader = csv.DictReader(f)
        for acc in reader:
            acounts.append(acc)
    return acounts


def find_acount(username: str, password: str, acounts: list[dict]) -> dict | int:
    for i, acc in enumerate(acounts):
        if acc.get("username") == username and acc.get("password") == password:
            return acc, i
    print("\nUsername or Password is incorrect\n")
    return None, None


def enter_email() -> str:
    status = False
    while status is not True:
        email = input("Email: ")
        if email == "":
            return None
        status = is_email_valid(email)
    return email


def get_username_password() -> tuple:
    username = get_string("Username: ", r"^[A-Za-z0-9_ ]{3,24}$")
    password = get_string("Password: ", r".{3,24}")
    return username, password


def get_string(input_string: str, pattern: str, get_groups: bool = False) -> str:
    while True:
        string: str = input(input_string)
        if captured := re.search(pattern, string):
            if get_groups is True:
                return tuple(g for g in captured.groups() if g is not None)
            return string
        print("Input is not valid")


def check_availability(username: str, file: str) -> bool:
    acounts = read_file(file)
    for acc in acounts:
        if acc.get("username") == username:
            print("\nUsername not available\n")
            return False
    return True


def is_email_valid(email: str) -> bool:
    try:
        validate_email(email, check_deliverability=False)
        return True
    except EmailNotValidError:
        print("Email not found")
        return False

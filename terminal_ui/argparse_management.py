from argparse import ArgumentParser
from getpass import getpass
from login_management import accounts_path, read_file, find_account, check_availability


def argparse_management():
    username, password = parse_command_line()
    if username:
        return check_login(username, password)
    return None, None, None


def parse_command_line():
    parser = ArgumentParser()
    parser.add_argument(
        "-u", "--username", type=str, help="Enter the username for login"
    )
    args = parser.parse_args()

    if not args.username or check_availability(
        args.username, accounts_path(), print_error=False
    ):
        return None, None

    entered_password = getpass("\nPassword (hidden): ")
    return args.username, entered_password


def check_login(username, password):
    registered_accounts: list = read_file(file_path=accounts_path())
    user_account, user_index = find_account(username, password, registered_accounts)
    return user_account, user_index, registered_accounts

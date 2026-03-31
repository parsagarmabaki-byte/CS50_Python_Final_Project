from argparse import ArgumentParser, Namespace
from login_management import accounts_path, read_file, find_account


def argparse_management():
    args = parse_command_line()
    if args is not None:
        return check_login(args.username, args.password)
    return None, None, None


def parse_command_line():
    parser = ArgumentParser()
    parser.add_argument(
        "-u", "--username", type=str, help="Enter the username for login"
    )
    parser.add_argument(
        "-p", "--password", type=str, help="Enter the password for login"
    )
    args = parser.parse_args()
    if args.username is None or args.password is None:
        return None
    return args


def check_login(username, password):
    registered_accounts: list = read_file(file_path=accounts_path())
    user_account, user_index = find_account(username, password, registered_accounts)
    return user_account, user_index, registered_accounts


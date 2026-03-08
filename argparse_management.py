from argparse import ArgumentParser, Namespace
from login_management import acounts_path, read_file, find_acount


def argparse_managment():
    args = get_commandline()
    if args is not None:
        return check_login(args.username, args.password)
    return None, None, None


def get_commandline():
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
    registred_acounts: list = read_file(file=acounts_path())
    user_acount, user_num = find_acount(username, password, registred_acounts)
    return user_acount, user_num, registred_acounts


if __name__ == "__main__":
    print(argparse_managment())

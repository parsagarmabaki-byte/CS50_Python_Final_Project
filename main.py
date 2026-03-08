from login_management import login_options, login, create_acount
from user_menu import user_menu, clear_terminal
from argparse_management import argparse_managment


def main():
    users_acount, user_number, registred_acounts = argparse_managment()
    times_runned = 1
    while True:
        if users_acount is None or times_runned > 1:
            clear_terminal()
            choice = login_options()
            if choice == 1:
                users_acount, user_number, registred_acounts = login()
            elif choice == 2:
                create_acount()

        if users_acount:
            updated_user = user_menu(users_acount)
            registred_acounts = update_user_info(
                registred_acounts, user_number, updated_user
            )
            times_runned += 1


def update_user_info(registred_acounts: list, user_number: int, updated_user: dict):
    registred_acounts[user_number] = updated_user
    return registred_acounts


if __name__ == "__main__":
    main()

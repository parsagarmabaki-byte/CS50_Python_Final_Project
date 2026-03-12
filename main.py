from login_management import login_options, prompt_login, create_account,rewrite_account_list
from user_menu import user_menu, clear_terminal
from argparse_management import argparse_management


def main():
    user_account, user_index, registered_accounts = argparse_management()
    times_runned = 1
    while True:
        if user_account is None or times_runned > 1:
            # clear_terminal()
            choice = login_options()
            if choice == 1:
                user_account, user_index, registered_accounts = prompt_login()
            elif choice == 2:
                create_account()

        if user_account:
            updated_user = user_menu(user_account)
            registered_accounts = update_user_info(
                registered_accounts, user_index, updated_user
            )
            rewrite_account_list(registered_accounts)
            times_runned += 1
        

def update_user_info(registered_accounts: list, user_index: int, updated_user: dict):
    registered_accounts[user_index] = updated_user
    return registered_accounts


if __name__ == "__main__":
    main()

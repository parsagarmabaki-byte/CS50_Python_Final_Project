from login_management import login_options, prompt_login, create_account
from user_menu import user_menu, clear_terminal
from argparse_management import argparse_management
from pathlib import Path
import csv
from typing import List, Dict


def main() -> None:
    """Entry point for the application.

    Orchestrates login/registration and launches the user menu loop. The
    function maintains an in-memory list of registered accounts and updates the
    CSV file when the active user's information changes. If ``user_menu``
    returns ``None`` (because the account was deleted), the account is removed
    from the list and the main loop continues.
    """
    user_account, user_index, registered_accounts = argparse_management()
    need_login = False
    while True:
        if user_account is None or need_login:
            clear_terminal()
            choice = login_options()
            if choice == 1:
                user_account, user_index, registered_accounts = prompt_login()
            elif choice == 2:
                if create_account():
                    print("\nREGISTRATION SUCCESSFUL")
                    input("Press Enter to continue...")
                else:
                    print("\nREGISTRATION FAILED")
                    input("Press Enter to continue...")

        if user_account:
            updated_user = user_menu(user_account)
            if updated_user is None:
                registered_accounts.pop(user_index)
            else:
                registered_accounts = update_user_info(
                    registered_accounts, user_index, updated_user
                )
            rewrite_account_list(registered_accounts)
            need_login = True


def update_user_info(
    registered_accounts: List[Dict],
    user_index: int,
    updated_user: Dict,
) -> List[Dict]:
    """Replace a single user's record in the accounts list.

    Args:
        registered_accounts (List[Dict]): list of account dictionaries.
        user_index (int): index of the account to update.
        updated_user (Dict): modified user dict.

    Returns:
        List[Dict]: the same list, with the specified record replaced.
    """
    registered_accounts[user_index] = updated_user
    return registered_accounts


def rewrite_account_list(accounts: List[Dict]) -> None:
    """Persist the provided account list back to the CSV file.

    Args:
        accounts (List[Dict]): Current list of registered accounts.

    Returns:
        None: Data is written to disk.
    """
    base = Path(__file__).resolve().parent
    project_root = base.parent
    path = project_root.joinpath("csv_files", "Accounts.csv")
    
    with open(path, "w", newline="") as file:
        writer = csv.DictWriter(
            file, fieldnames=["username", "password", "email", "date"]
        )
        writer.writeheader()
        for account in accounts:
            writer.writerow(
                {
                    "username": account["username"],
                    "password": account["password"],
                    "email": account["email"],
                    "date": account["date"],
                }
            )


if __name__ == "__main__":
    main()

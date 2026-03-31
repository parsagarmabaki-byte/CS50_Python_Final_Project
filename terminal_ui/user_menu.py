"""User menu module for the MarketWatch application.

This module provides the interactive user dashboard for managing watchlists,
viewing and updating prices, and managing account settings.
"""

from typing import Optional
from login_management import (
    get_string,
    read_file,
    get_valid_email,
    account_files_path,
    check_user_password,
    hash_password,
)
from API_management import (
    add_symbol,
    clear_terminal,
    prompt_confirmation,
    update_prices,
    update_symbol_data,
    group_symbols,
    rewrite_watchlist_file,
    prompt_task,
    rewrite_prices_file,
    get_currency_data,
)
import sys
from pathlib import Path
import shutil
import getpass


def print_user_menu(username: str) -> None:
    """Print the main dashboard menu for the given user.

    Args:
        username (str): the name of the currently logged-in user.

    Returns:
        None: this function only prints to stdout.
    """
    menu = f"""==============================
 MarketWatch — User Dashboard
 Logged in as: {username}
==============================

1) Watchlist
   1.1) View watchlist
   1.2) Add symbol (e.g., FX:USDSEK)
   1.3) Remove symbol

2) Update prices
   2.1) Update all watchlist symbols (latest)
   2.2) Update one symbol

3) View prices
   3.1) Show prices for date range 
   3.2) Show Watchlist prices

4) Account
   4.1) Show account info (username/email)
   4.2) Change email (optional)
   4.3) Change password (optional)
   4.4) Delete account (danger)


0) Log out
Q) Quit program
"""
    print(menu)


def user_menu(user: dict) -> Optional[dict]:
    """Run the interactive user menu loop.

    Displays the main menu and processes user choices until they log out
    or their account is deleted.

    Args:
        user (dict): Dictionary with user information (username, email, etc.).

    Returns:
        Optional[dict]: The (potentially modified) user dict, or ``None`` if the
        account was deleted during the session.
    """
    clear_terminal()
    submenu_choice: str = None
    task: str = None
    while submenu_choice != "0":
        print_user_menu(user["username"])
        submenu_choice, task = prompt_choice()
        if dispatch_menu(user, submenu_choice, task):
            return None
    return user


def prompt_choice() -> tuple[str, str | None]:
    """Prompt the user for a main menu choice and optional subtask.

    Uses regex pattern matching to validate menu input format.

    Returns:
        tuple[str, str | None]: The selected menu key and optional subtask.
    """
    while True:
        matched_groups: tuple = get_string(
            "Choice: ",
            r"^(?:(1)(?:\.?([123]))?|(2)(?:\.([12]))?|(3)(?:\.([12]))?|(4)(?:\.([1234]))?|([0Q]))$",
            get_groups=True,
        )
        if matched_groups[0] == "Q":
            sys.exit("System Exited")
        if len(matched_groups) == 2:
            return matched_groups[0], matched_groups[1]
        else:
            return matched_groups[0], None


def dispatch_menu(user: dict, submenu: str, task: str | None) -> bool | None:
    """Dispatch the chosen submenu action.

    Routes the user's menu selection to the appropriate handler function.

    Args:
        user (dict): Current user info.
        submenu (str): Top-level menu selection (1-4).
        task (str | None): Secondary selection within submenu.

    Returns:
        bool | None: Returns ``True`` if the user account was deleted;
        otherwise ``None``.
    """
    if submenu == "1":
        watchlist(user["username"], task)
    elif submenu == "2":
        update_price_menu(task, user["username"])
    elif submenu == "3":
        view_prices_menu(task, user["username"])
    elif submenu == "4":
        if account(user, task):
            return True


def view_prices_menu(task: str | None, username: str) -> None:
    """Handle the "View prices" submenu loop.

    Args:
        task (str | None): Current subtask or None.
        username (str): The user's name (used for file paths).

    Returns:
        None
    """
    clear_terminal()
    should_prompt: bool = False
    while task != "3":
        if should_prompt or task is None:
            print_view_prices_submenu()
            task = prompt_task(limit=3)
            clear_terminal()
        if task == "1":
            base_currency: str
            quote_currency: str
            data: dict[str, float]
            base_currency, quote_currency, data = get_currency_data()
            if base_currency:
                print_rates(data, base_currency, quote_currency)
        elif task == "2":
            print_prices(username)
        should_prompt = True


def print_view_prices_submenu() -> None:
    """Display submenu options for viewing prices."""
    print("""3) View Prices
    1) Show prices for date range (optional)
    2) Show Watchlist prices
    3) Main options
""")


def print_rates(
    data: dict[str, dict[str, float]], base_currency: str, quote_currency: str
) -> None:
    """Print fetched currency rates in tabular form.

    Args:
        data (dict[str, dict[str, float]]): Mapping of dates to rate values.
        base_currency (str): Base currency code.
        quote_currency (str): Quote currency code.

    Returns:
        None
    """
    print(f"""
=====================================
             {base_currency}/{quote_currency}
=====================================

  #   Date           Prices
-------------------------------------""")
    for index, (date, rate) in enumerate(data.items(), 1):
        print(f"  {index:<2}  {date}     {rate[quote_currency]:.2f}")
    print("-------------------------------------\n")


def update_price_menu(task: str | None, username: str) -> None:
    """Manage the "Update prices" submenu loop.

    Args:
        task (str | None): Current subtask or None.
        username (str): The user's name.

    Returns:
        None
    """
    clear_terminal()
    should_prompt: bool = False
    while task != "3":
        if should_prompt or task is None:
            print_update_price_submenu()
            task = prompt_task(limit=3)
            clear_terminal()
        if task == "1":
            update_prices(username)
        elif task == "2":
            update_symbol(username)
        should_prompt = True


def update_symbol(username: str) -> None:
    """Update a single symbol's price in the user's price file.

    Displays the watchlist, prompts for symbol selection, and fetches
    the latest price data for the selected symbol.

    Args:
        username (str): The username used to locate files.

    Returns:
        None
    """
    watchlist_items, file_path, last_index = print_watchlist(username, "Watchlist")
    if watchlist_items is None and file_path is None and last_index is None:
        return None
    selection = int(get_string("\nChoice: ", f"^[0-{last_index + 1}]$"))
    if selection != last_index + 1:
        symbols = group_symbols([watchlist_items[selection]], symbol_key="Stocks")
        base_currency, quote_currency = symbols[0]
        price, date = update_symbol_data(base_currency, quote_currency)

        prices_list = read_file(
            Path(account_files_path(username).joinpath("Prices.csv"))
        )
        prices_list[selection]["price"] = price
        prices_list[selection]["date"] = date
        rewrite_prices_file(username, prices_list)
        print()


def print_update_price_submenu() -> None:
    """Display the submenu for the price update options."""
    print("""2) Update prices
    1) Update all watchlist symbols (latest)
    2) Update one symbol
    3) Main options
    """)


def watchlist(username: str, task: str | None) -> None:
    """Handle the watchlist submenu actions.

    Displays the watchlist menu and routes to view, add, or remove
    symbol functions based on user selection.

    Args:
        username (str): User identifier.
        task (str | None): Selected submenu option or None.

    Returns:
        None
    """
    clear_terminal()
    should_prompt: bool = False
    while task != "4":
        if should_prompt or task is None:
            print_watchlist_submenu()
            task = prompt_task(limit=4)
            clear_terminal()
        if task == "1":
            print_watchlist(username, "Watchlist")
        elif task == "2":
            add_symbol(username)
            clear_terminal()
        elif task == "3":
            remove_symbol(username)
        should_prompt = True


def remove_symbol(username: str) -> None:
    """Remove a symbol from the user's watchlist and prices.

    Displays the watchlist, prompts for symbol selection, and removes
    the selected symbol from both watchlist and prices files.

    Args:
        username (str): The username used internally as folder name.

    Returns:
        None
    """
    symbols, file_path, last_index = print_watchlist(username, "Remove symbol")
    if symbols is None and file_path is None and last_index is None:
        return None
    prices_content: list = read_file(
        Path(account_files_path(username).joinpath("Prices.csv"))
    )
    try:
        selection = int(get_string("\nChoice: ", f"^[0-{last_index}]?$"))
        if selection != last_index + 1:
            symbols.pop(selection)
            prices_content.pop(selection)
            rewrite_watchlist_file(username, symbols)
            rewrite_prices_file(username, prices_content)
    except ValueError:
        pass


def print_watchlist(
    username: str, title: str
) -> tuple[list, Path, int] | tuple[None, None, None]:
    """Print the user's watchlist to the console.

    Args:
        username (str): Account name.
        title (str): Title to display (e.g. "Watchlist").

    Returns:
        tuple[list, Path, int] | tuple[None, None, None]: When data is present
        returns ``(symbols, file_path, last_index)`` where ``symbols`` is a list
        of dicts, ``file_path`` is a :class:`pathlib.Path` to the CSV, and
        ``last_index`` is the last printed row index. If the underlying CSV is
        empty or missing, prints a warning and returns ``(None, None, None)``.
    """
    file_path = Path(account_files_path(username).joinpath("Watchlist.csv"))
    symbols = read_file(file_path)
    if not symbols:
        return None, None, None
    print(f"""
=====================================
            {title}
=====================================

  #   Symbol
-------------------------------------""")
    for index, line in enumerate(symbols):
        print(f"  {index}   {line['Stocks']}")
    print("-------------------------------------\n\n")
    return symbols, file_path, index


def print_prices(username: str) -> tuple[list, Path, int] | tuple[None, None, None]:
    """Display prices stored for the user.

    Args:
        username (str): Account identifier.

    Returns:
        tuple[list, Path, int] | tuple[None, None, None]: When price records
        exist returns ``(prices, file_path, last_index)`` where ``prices`` is a
        list of dicts. If the CSV file is empty or cannot be read, prints an
        error message and returns ``(None, None, None)``.
    """
    file_path = Path(account_files_path(username).joinpath("Prices.csv"))
    prices = read_file(file_path, print_file_empty=True)
    if not prices:
        return None, None, None
    symbols = group_symbols(prices)
    print(f"""
=====================================
            Prices
=====================================

  #     Symbol     Price       Date           Source
-------------------------------------------------------------------""")
    for index, line in enumerate(prices):
        print(
            f"  {index:<3}   {symbols[index][0]}{symbols[index][1]}     {float(line['price']):.2f}        {line['date']}     {line['source']}"
        )
    print("-------------------------------------------------------------------\n\n")
    return prices, file_path, index


def print_watchlist_submenu() -> None:
    """Print options for managing the watchlist."""
    print("""1) Watchlist
    1) View watchlist
    2) Add symbol (e.g., FX:USDSEK)
    3) Remove symbol
    4) Main menu
          """)


def account(user: dict, task: str | None) -> bool | None:
    """Handle account-related menu selections.

    Displays the account menu and routes to info, change email, change password,
    or delete account functions based on user selection.

    Args:
        user (dict): Current user data.
        task (str | None): Submenu task or None.

    Returns:
        bool | None: Returns True if account was deleted, None otherwise.
    """
    should_prompt: bool = False
    clear_terminal()
    while task != "5":
        if should_prompt or task is None:
            clear_terminal()
            print_account_submenu()
            task = prompt_task(limit=5)
            print()
        if task == "1":
            account_info(user)
            input("Press Enter to continue...")
        elif task == "2":
            change_email(user)
        elif task == "3":
            change_password(user)
        elif task == "4":
            if delete_account_with_verification(user):
                return True
        should_prompt = True
    clear_terminal()


def verification(user: dict) -> bool:
    """Perform three-step verification before removing an account.

    Steps:
        1. Re-enter current password.
        2. Type the literal word ``EXACTLY``.
        3. Type ``DELETE`` then confirm via a yes/no prompt.

    Args:
        user (dict): Current user record.

    Returns:
        bool: ``True`` only if all verification steps succeed.
    """
    print(f"""You are about to DELETE your account: {user['username']}
This will remove: profile, watchlists, stored prices. This action is irreversible.""")

    if check_user_password(
        user["password"], getpass.getpass("Old password (hidden): ")
    ):
        print("\nStep 2/3 — Confirm ")
        if getpass.getpass("Type 'EXACTLY' (hidden): ") != "EXACTLY":
            return False

        if getpass.getpass("Type 'DELETE' to confirm (hidden): ") != "DELETE":
            return False

        print("\nStep 3/3 — Final confirmation")
        if prompt_confirmation():
            return True
    return False


def delete_account_with_verification(user: dict) -> bool:
    """Delete the given user account after successful verification.

    This routine removes the user's directory and associated CSV files, then
    clears the terminal and displays a brief message.

    Args:
        user (dict): The account record to delete.

    Returns:
        bool: ``True`` if deletion occurred, ``False`` if verification failed.
    """
    if verification(user):
        user_path = Path(account_files_path(user["username"]))
        shutil.rmtree(user_path)
        clear_terminal()
        print("Deleting account...")
        input("Press Enter to continue...")
        return True
    else:
        clear_terminal()
        print("VERIFICATION FAILED\n")
        return False


def print_account_submenu() -> None:
    """Display account menu options."""
    print("""4) Account
   1) Show account info (username/email)
   2) Change email (optional)
   3) Change password (optional)
   4) Delete account (danger)
   5) Main options
""")


def change_email(user: dict) -> None:
    """Prompt the user to update their email address.

    Args:
        user (dict): Contains existing email to replace.

    Returns:
        None (user dict modified in-place).
    """
    while True:
        new_email = get_valid_email()
        if not new_email:
            break
        print(
            f"Old Email: {user['email']}\nNew Email: {new_email}\n\nDo you want to change?"
        )
        if prompt_confirmation():
            user["email"] = new_email
            print("Updated successfully")
            input("Press Enter to continue...")
            clear_terminal()
            break


def change_password(user: dict) -> None:
    """Interactively change the user's password.

    Prompts for the old password for verification, then asks for a new
    password twice to confirm. Updates the user dict if confirmed.

    Args:
        user (dict): User data to update.

    Returns:
        None (user dict modified in-place).
    """
    while True:
        if not check_user_password(
            user["password"], getpass.getpass("Old password (hidden): ")
        ):
            print("\nWRONG PASSWORD\n")
            break
        new_password_input = getpass.getpass("New password (hidden): ")
        if not new_password_input:
            break
        if (
            getpass.getpass("Enter the new password again (hidden): ").strip()
            != new_password_input
        ):
            print("\nPASSWORD DONT MATCHED\n")
            continue
        if prompt_confirmation():
            hashed_password = hash_password(new_password_input)
            user["password"] = hashed_password
            print("Updated successfully")
            input("Press Enter to continue...")
            break


def account_info(user: dict) -> None:
    """Print the account information for the given user dictionary.

    Args:
        user (dict): Must contain username, email, and date fields.

    Returns:
        None
    """
    print("""=====================================
        Account Information
=====================================""")
    print(
        f"Username : {user['username']}\nEmail    : {user['email']}\nCreated  : {user['date']}"
    )
    print("----------------------------------------\n")

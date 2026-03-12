from login_management import get_string, read_file, enter_email, account_files_path
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
import csv
from pprint import pprint


def print_user_menu(username: str) -> None:
    """Print the main dashboard menu for the given user.

    Args:
        username (str): the name of the currently logged-in user.

    Returns:
        None: this function only prints to stdout.
    """
    menu = f"""
==============================
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

4) Summary / Analysis
   4.1) Summary (7 days)
   4.2) Summary (30 days)
   4.3) Summary (custom window)

5) Export data
   5.1) Export "long" format CSV (date,symbol,price,source)
   5.2) Export "wide" format CSV (date columns per symbol)

6) Account
   6.1) Show account info (username/email)
   6.2) Change email (optional)
   6.3) Change password (optional)
   6.4) Delete account (danger)


0) Log out
Q) Quit program
"""
    print(menu)


def user_menu(user:dict)->dict:
    """Run the interactive user menu loop.

    Args:
        user (dict): dictionary with user information (username, email, etc.).

    Returns:
        dict: possibly updated user dictionary after menu actions.
    """
    submenu: str = None
    task: str = None
    while submenu != "0":
        print_user_menu(user["username"])
        submenu, task = prompt_choice()
        dispatch_menu(user, submenu, task)
    return user


def prompt_choice() -> tuple[str, str | None]:
    """Prompt the user for a main menu choice and optional subtask.

    Returns:
        tuple[str, str|None]: the selected menu key and optional subtask identifier.
    """
    while True:
        raw_choice: tuple = get_string(
            "Choice: ",
            r"^(?:(1)(?:\.?([123]))?|(2)(?:\.([12]))?|(3)(?:\.([123]))?|(4)(?:\.([12]))?|(5)(?:\.([12]))?|(6)(?:\.([1234]))?|([0Q]))$",
            get_groups=True,
        )
        if raw_choice[0] == "Q":
            sys.exit("System Exited")
        if len(raw_choice) == 2:
            return raw_choice[0], raw_choice[1]
        else:
            return raw_choice[0], None


def dispatch_menu(user:dict, submenu:str, task:str|None)->None:
    """Dispatch the chosen submenu action.

    Args:
        user (dict): current user info.
        submenu (str): top-level menu selection.
        task (str|None): secondary selection within submenu.

    Returns:
        None
    """
    if submenu == "1":
        watchlist(user["username"], task)
    elif submenu == "2":
        update_price_menu(task, user["username"])
    elif submenu == "3":
        view_prices_menu(task, user["username"])
    elif submenu == "4":
        summary_analysis(task)
    elif submenu == "5":
        export_data(task)
    elif submenu == "6":
        account(user, task)


def view_prices_menu(task:str, username:str)->None:
    """Handle the "View prices" submenu loop.

    Args:
        task (str): current subtask or None.
        username (str): the user's name (used for file paths).

    Returns:
        None
    """
    clear_terminal()
    prompt_again:bool = False
    while task != "3":
        if prompt_again is True or task is None:
            print_view_prices_submenu()
            task = prompt_task(limit=3)
            clear_terminal()
        if task == "1":
            base_currency: str
            quote_currency: str
            data: dict[str, dict]
            base_currency, quote_currency, data = get_currency_data()
            print_rates(data, base_currency, quote_currency)
        elif task == "2":
            print_prices(username)
        prompt_again = True


def print_view_prices_submenu()->None:
    """Display submenu options for viewing prices."""
    print("""View Prices
    1) Show prices for date range (optional)
    2) Show Watchlist prices
    3) Main options
""")


def print_rates(data:dict[str, dict], base_currency:str, quote_currency:str)->None:
    """Print fetched currency rates in tabular form.

    Args:
        data (dict[str, dict]): mapping dates to rate dictionaries.
        base_currency (str): base currency code.
        quote_currency (str): quote currency code.

    Returns:
        None
    """
    print(f"""
=====================================
             {base_currency}/{quote_currency}
=====================================
              
  #   Date           Prices     
--------------------------------------------""")
    for index, (date, rates) in enumerate(data.items(), 1):
        print(f"  {index}   {date}     {rates[quote_currency]}")


def update_price_menu(task:str, username:str):
    """Manage the "Update prices" submenu loop.

    Args:
        task (str): current subtask or None.
        username (str): the user's name.

    Returns:
        None
    """
    clear_terminal()
    prompt_again = False
    while task != "3":
        if prompt_again is True or task is None:
            print_update_price_submenu()
            task = prompt_task(limit=3)
            clear_terminal()
        if task == "1":
            update_prices(directory=username)
        elif task == "2":
            update_symbol(directory=username)
        prompt_again = True


def update_symbol(directory):
    """Update a single symbol's price in the user's price file.

    Args:
        directory (str): the username used to locate files.

    Returns:
        None
    """
    currencies, file_path, i = print_watchlist(directory, "Watchlist")
    selection = int(get_string("\nChoice: ", f"^[0-{i+1}]$"))
    if selection != i + 1:
        symbols = group_symbols([currencies[selection]], dict_value="Stocks")
        base_currency, quote_currency = symbols[0]
        price, date = update_symbol_data(base_currency, quote_currency)

        prices_list = read_file(
            Path(account_files_path(directory).joinpath("Prices.csv"))
        )
        prices_list[selection]["price"] = price
        prices_list[selection]["date"] = date

        rewrite_prices_file(directory, prices_list)


def print_update_price_submenu():
    """Display the submenu for the price update options."""
    print("""2) Update prices
    1) Update all watchlist symbols (latest)
    2) Update one symbol
    3) Main options
    """)


def watchlist(username, task):
    """Handle the watchlist submenu actions.

    Args:
        username (str): user identifier.
        task (str): selected submenu option or None.

    Returns:
        None
    """
    clear_terminal()
    prompt_again = False
    while task != "4":
        if prompt_again is True or task is None:
            print_watchlist_submenu()
            task = prompt_task(limit=4)
            clear_terminal()
        if task == "1":
            print_watchlist(username, "Watchlist")
        elif task == "2":
            add_symbol(username)
        elif task == "3":
            remove_symbol(username)
        prompt_again = True


def remove_symbol(directory):
    """Remove a symbol from the user's watchlist and prices.

    Args:
        directory (str): the username used internally as folder name.

    Returns:
        None
    """
    symbols, file_path, i = print_watchlist(directory, "Remove symbol")
    content: list = read_file(Path(account_files_path(directory).joinpath("Prices.csv")))
    selection = int(get_string("\nChoice: ", f"^[0-{i+1}]$"))
    if selection != i + 1:
        symbols.pop(selection)
        content.pop(selection)
        rewrite_watchlist_file(directory, symbols)
        rewrite_prices_file(directory, content)


def print_watchlist(username, filetype):
    """Print the user's watchlist to the console.

    Args:
        username (str): account name.
        filetype (str): title to display (e.g. "Watchlist").

    Returns:
        tuple[list, Path, int]: symbols list, path to csv, last index printed.
    """
    file_path = Path(account_files_path(username).joinpath("Watchlist.csv"))
    symbols = read_file(file_path)
    print(f"""
=====================================
            {filetype}
=====================================
              
  #   Symbol       
-------------------------------------""")
    for index, line in enumerate(symbols):
        print(f"  {index}   {line["Stocks"]}")
    print(f"  {index+1}   Main menu")
    print("-------------------------------------\n\n")
    return symbols, file_path, index


def print_prices(username):
    """Display prices stored for the user.

    Args:
        username (str): account identifier.

    Returns:
        tuple[list, Path, int]: loaded prices list, file path, last index.
    """
    file_path = Path(account_files_path(username).joinpath("Prices.csv"))
    prices = read_file(file_path)
    symbols = group_symbols(prices)
    print(f"""
=====================================
            Prices
=====================================
              
  #   Symbol     Price       Date           Source       
-------------------------------------------------------------------""")
    for index, line in enumerate(prices):
        print(
            f"  {index}   {symbols[index][0]}{symbols[index][1]}     {line['price']}     {line['date']}     {line['source']}"
        )
    print("-------------------------------------------------------------------\n\n")
    return prices, file_path, index


def print_watchlist_submenu():
    """Print options for managing the watchlist."""
    print("""1) Watchlist
    1) View watchlist
    2) Add symbol (e.g., FX:USDSEK)
    3) Remove symbol
    4) Main menu
          """)


def account(user, task):
    """Handle account-related menu selections.

    Args:
        user (dict): current user data.
        task (str): submenu task or None.

    Returns:
        None
    """
    clear_terminal()
    get_chioce = False
    while task != "5":
        if get_chioce is True or task is None:
            print_account_submenu()
            task = prompt_task(limit=5)
        if task == "1":
            account_info(user)
        elif task == "2":
            change_email(user)
        elif task == "3":
            change_password(user)
        elif task == "4":
            pass
        get_chioce = True
    clear_terminal()


def print_account_submenu():
    """Display account menu options."""
    print("""6) Account
   1) Show account info (username/email)
   2) Change email (optional)
   3) Change password (optional)
   4) Delete account (danger)
   5) Main options
""")


def change_email(user):
    """Prompt the user to update their email address.

    Args:
        user (dict): contains existing email to replace.

    Returns:
        None (user dict modified in-place).
    """
    while True:
        new_email = enter_email()
        if new_email is None:
            break
        print(
            f"Old Email: {user["email"]}\nNew Email: {new_email}\n\nDo you want to change?"
        )
        if prompt_confirmation():
            user["email"] = new_email
            break


def change_password(user):
    """Interactively change the user's password.

    Args:
        user (dict): user data to update.

    Returns:
        None (user dict modified in-place).
    """
    while True:
        new_password = get_string("New Password: ", r".{3,24}").strip()
        if new_password == "":
            break
        repeated_password = input("Enter the new password again: ").strip()
        if new_password != repeated_password:
            print("\nPASSWORD DONT MATCHED\n")
            continue
        if prompt_confirmation():
            user["password"] = new_password
            break


def account_info(user):
    """Print the account information for the given user dictionary.

    Args:
        user (dict): must contain username, password, email, date.

    Returns:
        None
    """
    print(
        f"\nUsername:{user["username"]}\nPassword:{user["password"]}\nEmail:{user["email"]}\nDate:{user["date"]}"
    )


if __name__ == "__main__":
    user = {
        "username": "Parsa Garmabaki",
        "password": "parsa2006",
        "email": "parsa.garmabaki@gmail.com",
        "date": "02/23/26",
    }
    user_menu(user)

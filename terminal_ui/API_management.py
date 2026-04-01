"""API management module for the MarketWatch application.

This module handles interactions with the Frankfurter currency API,
manages watchlist and price data files, and provides currency selection
and confirmation prompts.
"""

import requests
from login_management import get_string, account_files_path, read_file
import csv
import os
from pathlib import Path
import re
from datetime import date, timedelta


def frankfurter_api(
    base: str = "USD",
    symbols: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict | None:
    """Query the Frankfurter currency API for exchange rates.

    Supports both latest rates and historical rate ranges. Handles connection
    errors gracefully by returning None instead of raising an exception.

    Args:
        base (str): Base currency code (default: "USD").
        symbols (str | None): Target currency code (e.g., "EUR", "SEK").
        start_date (str | None): Start date in YYYY-MM-DD format. If provided,
            fetches historical data from this date.
        end_date (str | None): End date in YYYY-MM-DD format. Only used with
            start_date for date range queries.

    Returns:
        dict | None: Parsed JSON response with rates data, or None if connection fails.
    """
    if start_date:
        url = f"https://api.frankfurter.app/{start_date}?from={base}&to={symbols}"
        if end_date:
            url = f"https://api.frankfurter.app/{start_date}..{end_date}?from={base}&to={symbols}"
    else:
        url = f"https://api.frankfurter.dev/v1/latest?base={base}&symbols={symbols}"
    try:
        response = requests.get(url)
    except requests.exceptions.ConnectionError:
       return 
    return response.json()


def print_connection_error() -> None:
    """Display an error message when no internet connection is detected.

    Prints a formatted error message informing the user about connection issues
    and waits for user acknowledgment before continuing.

    Returns:
        None
    """
    print("""\n----------------------------------------
ERROR: No internet connection.
Check your network and try again.
----------------------------------------""")
    input("\nPress Enter to continue...")


def get_asset() -> str:
    """Prompt user to select an asset type.

    Returns:
        str: Choice '1' (Forex) or '2' (Back).
    """
    print("\nSelect asset type:\n1) Forex\n2) Back")
    return get_string("\nChoice: ", "^[1-2]$")


def print_currency(currency_type: str = "base", currencies:list=None) -> None:
    """Display currency selection menu for base or quote currency.

    Prints a numbered list of available currencies plus a 'Back' option.
    The menu title adjusts based on whether the user is selecting the
    base or quote currency.

    Args:
        currency_type (str): Either 'base' or 'quote' to adjust the menu wording.
        currencies (list): List of currency codes to display.

    Returns:
        None
    """
    for i, currency in enumerate(currencies):
        print(f"{i+1}) {currency}")
    print(f"{i+2}) Back")


def clear_terminal():
    """Clear the terminal screen (cross-platform)."""
    os.system("cls" if os.name == "nt" else "clear")


def add_symbol(username: str) -> None:
    """Add a new FX symbol to the user's watchlist and prices.

    Prompts the user to select base and quote currencies, fetches the current
    exchange rate from the Frankfurter API, and appends entries to both the
    Watchlist.csv and Prices.csv files.

    Args:
        username (str): Account folder name.

    Returns:
        None
    """
    asset_choice = get_asset()
    if asset_choice == "1":
        base_currency, quote_currency = prompt_currencies()
        if base_currency and quote_currency:
            api_response = frankfurter_api(base=base_currency, symbols=quote_currency)
            if not api_response:
                print_connection_error()
                return
            for file_type in ["Watchlist", "Prices"]:
                if file_type == "Watchlist":
                    append_to_watchlist(
                        username=username,
                        base_currency=base_currency,
                        quote_currency=quote_currency,
                    )
                elif file_type == "Prices":
                    append_price_entry(
                        username=username,
                        base_currency=base_currency,
                        quote_currency=quote_currency,
                        api_content=api_response,
                    )
            input("\nSymbol added successfully.\nPress Enter to continue...")


def append_to_watchlist(username: str, base_currency: str, quote_currency: str) -> None:
    """Append a forex symbol string to the watchlist CSV.

    Writes a new row to the user's Watchlist.csv with the formatted symbol
    string (e.g., "FX:USDSEK").

    Args:
        username (str): Username directory name.
        base_currency (str): Base currency code (e.g., "USD").
        quote_currency (str): Quote currency code (e.g., "SEK").

    Returns:
        None
    """
    with open(
        Path(account_files_path(username)).joinpath("Watchlist.csv"),
        "a",
        newline="",
    ) as file:
        writer = csv.DictWriter(file, fieldnames=["Stocks"])
        writer.writerow({"Stocks": f"FX:{base_currency}{quote_currency}"})


def update_prices(username: str) -> None:
    """Refresh all prices for currencies listed in user's prices file.

    Args:
        username (str): Username directory.

    Returns:
        None: this function rewrites the prices CSV with current data.  If the
        prices file is empty a message is displayed and the function exits
        early without modifying any files.
    """
    file_path = Path(account_files_path(username).joinpath("Prices.csv"))
    price_records = read_file(file_path)
    if not price_records:
        input("Press Enter to continue...")
        return None
    symbols: list = group_symbols(price_records)
    updated_content = update_data(symbols)
    if not updated_content:
        print_connection_error()
        return None
    clear_prices_file(username)
    updating_data(symbols, username, updated_content)
    print("\nCurrency Pairs Updated")
    input("Press Enter to continue...")


def clear_prices_file(username: str) -> None:
    """Overwrite the Prices.csv with only header (clear contents).

    Args:
        username (str): Username directory.

    Returns:
        None
    """
    with open(
        Path(account_files_path(username).joinpath("Prices.csv")), "w", newline=""
    ) as file:
        writer = csv.DictWriter(file, fieldnames=["symbol", "price", "date", "source"])
        writer.writeheader()


def updating_data(
    symbols: list[tuple[str, str]], username: str, updated_content: list[dict]
) -> None:
    """Write updated price entries back into Prices.csv.

    Args:
        symbols (list of tuples): List of (base, quote) currency tuples.
        username (str): Username directory.
        updated_content (list of dicts): Updated price data from API.

    Returns:
        None
    """
    for index, (base_currency, quote_currency) in enumerate(symbols):
        append_price_entry(
            username, base_currency, quote_currency, updated_content[index]
        )


def group_symbols(
    currencies: list[dict], symbol_key: str = "symbol"
) -> list[tuple[str, str]]:
    """Convert list of currency dicts to list of (base, quote) tuples.

    Parses FX symbol strings in format "FX:XXXYYY" into tuple pairs.

    Args:
        currencies (list[dict]): List of currency records.
        symbol_key (str): Dictionary key containing the symbol string.

    Returns:
        list[tuple[str, str]]: List of (base_currency, quote_currency) tuples.
    """
    symbols = []
    for currency in currencies:
        symbols.append(
            re.fullmatch(r"FX:(\w{3})(\w{3})", currency[symbol_key]).groups()
        )
    return symbols


def update_data(symbols: list[tuple[str, str]]) -> list[dict] | None:
    """Fetch fresh API data for each symbol tuple in the list.

    Iterates through the provided currency pairs and queries the Frankfurter API
    for the latest exchange rates. Returns None if any API call fails.

    Args:
        symbols (list[tuple[str, str]]): List of (base_currency, quote_currency) tuples.

    Returns:
        list[dict] | None: List of API response dictionaries, or None if connection fails.
    """
    updated_currencies = []
    for base_currency, quote_currency in symbols:
        data = frankfurter_api(base_currency, quote_currency)
        if not data:
            return None
        updated_currencies.append(data)
    return updated_currencies


def update_symbol_data(base_currency: str, quote_currency: str) -> tuple[float | None, str | None]:
    """Retrieve current price and date for a single forex pair.

    Queries the Frankfurter API for the latest exchange rate between the
    specified currency pair.

    Args:
        base_currency (str): Base currency code (e.g., "USD").
        quote_currency (str): Quote currency code (e.g., "SEK").

    Returns:
        tuple[float | None, str | None]: Tuple of (price, date), or (None, None) if connection fails.
    """
    api_response = frankfurter_api(base_currency, quote_currency)
    if not api_response:
        print_connection_error()
        return None, None
    return api_response["rates"][quote_currency], api_response["date"]


def append_price_entry(
    username: str, base_currency: str, quote_currency: str, api_content: dict
) -> None:
    """Append one price record to Prices.csv from API content.

    Args:
        username (str): Username directory.
        base_currency (str): Base currency code.
        quote_currency (str): Quote currency code.
        api_content (dict): API response data.

    Returns:
        None
    """
    with open(
        Path(account_files_path(username)).joinpath("Prices.csv"),
        "a",
        newline="",
    ) as file:
        writer = csv.DictWriter(file, fieldnames=["symbol", "price", "date", "source"])
        writer.writerow(
            {
                "symbol": f"FX:{base_currency}{quote_currency}",
                "price": api_content["rates"][quote_currency],
                "date": api_content["date"],
                "source": "Frankfurter",
            }
        )


def rewrite_prices_file(username: str, content: list[dict]) -> None:
    """Rewrite entire Prices.csv using provided list of records.

    Args:
        username (str): Username directory.
        content (list[dict]): List of price record dictionaries.

    Returns:
        None
    """
    with open(
        Path(account_files_path(username).joinpath("Prices.csv")), "w", newline=""
    ) as file:
        writer = csv.DictWriter(file, fieldnames=["symbol", "price", "date", "source"])
        writer.writeheader()
        for element in content:
            writer.writerow(
                {
                    "symbol": element["symbol"],
                    "price": element["price"],
                    "date": element["date"],
                    "source": element["source"],
                }
            )


def rewrite_watchlist_file(username: str, symbols: list[dict]) -> None:
    """Rewrite the watchlist CSV with given symbol records.

    Args:
        username (str): Username directory.
        symbols (list[dict]): List of symbol record dictionaries.

    Returns:
        None
    """
    with open(
        Path(account_files_path(username).joinpath("Watchlist.csv")),
        "w",
        newline="",
    ) as file:
        writer = csv.DictWriter(file, fieldnames=["Stocks"])
        writer.writeheader()
        for symbol in symbols:
            writer.writerow({"Stocks": symbol["Stocks"]})


def prompt_currencies() -> tuple[str, str]:
    """Interactively choose base and quote currencies from list.

    Returns:
        tuple[str, str]: Selected base and quote currency codes.
    """
    available_currencies: list[str] = ["USD", "EUR", "GBP", "SEK", "DKK", "NOK"]

    print_currency(currencies=available_currencies)
    try:
        index=int(get_string("Choice: ", "^[1-7]$")) - 1
        base_currency = available_currencies[index]
        available_currencies.pop(index)
    except IndexError:
        return None, None
    print("\nBase currency: ", base_currency)

    print_currency(currency_type="quote",currencies=available_currencies)
    try:
        quote_currency = available_currencies[
            int(get_string("Choice: ", "^[1-6]$")) - 1
        ]
    except IndexError:
        return None, None
    print(f"\nBase currency: {base_currency}\nQuote currency: {quote_currency}")
    return base_currency, quote_currency


def prompt_confirmation():
    """Ask user for a confirmation and interpret a few affirmative replies.

    Returns:
        bool
    """
    return input("Are You Sure: ").lower().strip() in ["yes", "yeah", "ja", "are"]


def get_currency_data() -> tuple[str, str, dict] | tuple[None, None, None]:
    """Fetch historical rate data for a chosen currency pair with range options.

    Prompts the user to select currencies and a date range option, then queries
    the Frankfurter API for historical exchange rate data.

    Returns:
        tuple[str, str, dict] | tuple[None, None, None]: Tuple of (base_currency,
        quote_currency, rates_dict) on success, or (None, None, None) if user
        cancels or connection fails.
    """
    base_currency, quote_currency = prompt_currencies()
    clear_terminal()
    if base_currency and quote_currency:
        print_currency_data_submenu(base_currency, quote_currency)
        date_range_option = prompt_task(4)
        end_date = date.today().isoformat()
        if date_range_option == "1":
            days = int(get_string("Enter the range of days: ", r"^\d\d?$"))
            start_date = last_n_day(business_days=days)
        elif date_range_option == "2":
            start_date = last_n_day(business_days=7)
        elif date_range_option == "3":
            start_date = get_string(
                "Enter start date (YYYY-MM-DD): ", r"^\d{4}-\d\d-\d\d$"
            )
            end_date = get_string(
                "Enter end date press enter to skip: ", r"^(\d{4}-\d\d-\d\d)?$"
            )
            if not end_date:
                end_date = None
        elif date_range_option == "4":
            clear_terminal()
            return None, None, None
        api_response = frankfurter_api(
            base_currency, quote_currency, start_date, end_date
        )
        if not api_response:
            print_connection_error()
            return None, None, None
        return base_currency, quote_currency, api_response["rates"]
    return None, None, None


def print_currency_data_submenu(base_currency: str, quote_currency: str) -> None:
    """Display submenu when showing currency data range options.

    Args:
        base_currency (str): Base currency code.
        quote_currency (str): Quote currency code.

    Returns:
        None
    """
    print(f"""Show prices for a symbol
Symbol: {base_currency}{quote_currency}

Choose range option:
  1) Last n days (business days buffer)
  2) Last week (7 business days buffer)
  3) Enter start date (YYYY-MM-DD), optional end date
  4) Back
""")


def last_n_day(business_days: int) -> date:
    """Calculate the date N business days before today.

    Args:
        business_days (int): Number of business days to go back.

    Returns:
        date: The calculated date N business days ago.
    """
    current_date = date.today()
    remaining_days = business_days
    while remaining_days != 0:
        current_date -= timedelta(days=1)
        if current_date.weekday() in [5, 6]:
            continue
        remaining_days -= 1
    return current_date


def prompt_task(limit: int) -> str:
    """Prompt for a numeric menu choice up to a given limit.

    Args:
        limit (int): Maximum valid option number.

    Returns:
        str: The chosen option as a string.
    """
    return get_string("Choice: ", f"^[1-{limit}]$")

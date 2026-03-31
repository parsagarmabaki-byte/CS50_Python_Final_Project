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
from pprint import pprint


def frankfurter_api(
    base: str = "USD",
    symbols: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict:
    """Query the Frankfurter currency API for exchange rates.

    Args:
        base (str): Base currency code (default: "USD").
        symbols (str | None): Target currency codes, comma-separated.
        start_date (str | None): Start date in YYYY-MM-DD format or range start.
        end_date (str | None): End date in YYYY-MM-DD format.

    Returns:
        dict: Parsed JSON response from the API.
    """
    if start_date:
        url = f"https://api.frankfurter.app/{start_date}?from={base}&to={symbols}"
        if end_date:
            url = f"https://api.frankfurter.app/{start_date}..{end_date}?from={base}&to={symbols}"
    else:
        url = f"https://api.frankfurter.dev/v1/latest?base={base}&symbols={symbols}"

    response = requests.get(url)
    return response.json()


def get_asset() -> str:
    """Prompt user to select an asset type.

    Returns:
        str: Choice '1' (Forex) or '2' (Back).
    """
    print("Select asset type:\n1) Forex\n2) Back")
    return get_string("Choice: ", "^[1-2]$")


def print_currency(currency_type: str = "base") -> None:
    """Display currency selection menu.

    Args:
        currency_type (str): Either 'base' or 'quote' to adjust wording.

    Returns:
        None
    """
    print(
        f"\nSelect the {currency_type} currency:\n1) USD\n2) EUR\n3) GBP\n4) SEK\n5) DKK\n6) NOK\n7) Back"
    )


def clear_terminal():
    """Clear the terminal screen (cross-platform)."""
    os.system("cls" if os.name == "nt" else "clear")


def add_symbol(username: str) -> None:
    """Add a new FX symbol to the user's watchlist and prices.

    Args:
        username (str): Account folder name.

    Returns:
        None
    """
    asset_choice = get_asset()
    if asset_choice == "1":
        base_currency, quote_currency = prompt_currencies()
        if prompt_confirmation():
            api_response = frankfurter_api(base=base_currency, symbols=quote_currency)
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


def append_to_watchlist(username: str, base_currency: str, quote_currency: str) -> None:
    """Append a forex symbol string to the watchlist CSV.

    Args:
        username (str): Username directory.
        base_currency (str): Base currency code.
        quote_currency (str): Quote currency code.

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
        return None
    symbols: list = group_symbols(price_records)
    updated_content = update_data(symbols)
    clear_prices_file(username)
    updating_data(symbols, username, updated_content)


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


def update_data(symbols: list[tuple[str, str]]) -> list[dict]:
    """Fetch fresh API data for each symbol tuple in list.

    Args:
        symbols (list[tuple[str, str]]): List of (base_currency, quote_currency) tuples.

    Returns:
        list[dict]: List of API response dictionaries.
    """
    updated_currencies = []
    for base_currency, quote_currency in symbols:
        updated_currencies.append(frankfurter_api(base_currency, quote_currency))
    return updated_currencies


def update_symbol_data(base_currency: str, quote_currency: str) -> tuple[float, str]:
    """Retrieve current price and date for a single forex pair.

    Args:
        base_currency (str): Base currency code.
        quote_currency (str): Quote currency code.

    Returns:
        tuple[float, str]: Current exchange rate price and date string.
    """
    api_response = frankfurter_api(base_currency, quote_currency)
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

    print_currency()
    base_currency = available_currencies[int(get_string("Choice: ", "^[1-7]$")) - 1]

    print("\nBase currency: ", base_currency)

    print_currency(currency_type="quote")
    quote_currency = available_currencies[int(get_string("Choice: ", "^[1-7]$")) - 1]
    clear_terminal()
    print(f"Base currency: {base_currency}\nQuote currency: {quote_currency}")
    return base_currency, quote_currency


def prompt_confirmation():
    """Ask user for a confirmation and interpret a few affirmative replies.

    Returns:
        bool
    """
    return input("Are You Sure: ").lower().strip() in ["yes", "yeah", "ja", "are"]


def get_currency_data() -> tuple[str, str, dict]:
    """Fetch historical rate data for a chosen currency pair with range options.

    Returns:
        tuple[str, str, dict]: Base currency, quote currency, and rates dictionary.
    """
    base_currency, quote_currency = prompt_currencies()
    clear_terminal()
    print_currency_data_submenu(base_currency, quote_currency)
    date_range_option = prompt_task(3)
    end_date = date.today().isoformat()
    if date_range_option == "1":
        days = int(get_string("Enter the range of days: ", r"^\d\d?$"))
        start_date = last_n_day(business_days=days)
    elif date_range_option == "2":
        start_date = last_n_day(business_days=7)
    elif date_range_option == "3":
        start_date = get_string("Enter start date (YYYY-MM-DD): ", r"^\d{4}-\d\d-\d\d$")
        end_date = get_string(
            "Enter end date press enter to skip: ", r"^(\d{4}-\d\d-\d\d)?$"
        )
        if not end_date:
            end_date = None
    api_response = frankfurter_api(base_currency, quote_currency, start_date, end_date)
    return base_currency, quote_currency, api_response["rates"]


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


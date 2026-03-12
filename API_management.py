import requests
from login_management import get_string, account_files_path, read_file
import csv, os
from pathlib import Path
import re
from pprint import pprint
from datetime import date, timedelta


def frankfurter_api(base="USD", symbols=None, start_date=None, end_date=None):
    """Query the Frankfurter currency API for exchange rates.

    Args:
        base (str): base currency code.
        symbols (str|None): target currency codes comma-separated.
        start_date (str|None): YYYY-MM-DD or range start.
        end_date (str|None): YYYY-MM-DD or range end.

    Returns:
        dict: parsed JSON response.
    """
    if start_date:
        url = f"https://api.frankfurter.app/{start_date}?from={base}&to={symbols}"
        if end_date:
            url = f"https://api.frankfurter.app/{start_date}..{end_date}?from={base}&to={symbols}"
    else:
        url = f"https://api.frankfurter.dev/v1/latest?base={base}&symbols={symbols}"

    response = requests.get(url)
    return response.json()


def get_asset():
    """Prompt user to select an asset type.

    Returns:
        str: choice '1','2', or '3'.
    """
    print("Select asset type:\n1) Forex\n2) Crypto\n3) Back")
    return get_string("Choice: ", "^[1-3]$")


def print_currency(type="base"):
    """Display currency selection menu.

    Args:
        type (str): either 'base' or 'quote' to adjust wording.

    Returns:
        None
    """
    print(
        f"\nSelect the {type} currency:\n1) USD\n2) EUR\n3) GBP\n4) SEK\n5) DKK\n6) NOK\n7) Back"
    )


def clear_terminal():
    """Clear the Windows terminal screen."""
    os.system("cls")


def add_symbol(username):
    """Add a new FX symbol to the user's watchlist and prices.

    Args:
        username (str): account folder name.

    Returns:
        None
    """
    asset = get_asset()
    if asset == "1":
        base_currency, quote_currency = prompt_currencies()
        if prompt_confirmation():
            content = frankfurter_api(base=base_currency, symbols=quote_currency)
            for file_type in ["Watchlist", "Prices"]:
                if file_type == "Watchlist":
                    append_to_watchlist(
                        directory=username,
                        base_currency=base_currency,
                        quote_currency=quote_currency,
                    )
                elif file_type == "Prices":
                    append_price_entry(
                        directory=username,
                        base_currency=base_currency,
                        quote_currency=quote_currency,
                        api_content=content,
                    )


def append_to_watchlist(directory, base_currency, quote_currency):
    """Append a forex symbol string to the watchlist CSV.

    Args:
        directory (str): username directory.
        base_currency (str)
        quote_currency (str)

    Returns:
        None
    """
    with open(
        Path(account_files_path(directory)).joinpath("Watchlist.csv"),
        "a",
        newline="",
    ) as file:
        writer = csv.DictWriter(file, fieldnames=["Stocks"])
        writer.writerow({"Stocks": f"FX:{base_currency}{quote_currency}"})


def update_prices(directory):
    """Refresh all prices for currencies listed in user's prices file.

    Args:
        directory (str): username directory.

    Returns:
        None
    """
    file_path = Path(account_files_path(directory).joinpath("Prices.csv"))
    currencies = read_file(file_path)
    symbols: list = group_symbols(currencies)
    updated_content = update_data(symbols)
    clear_prices_file(directory)
    updating_data(symbols, directory, updated_content)


def clear_prices_file(directory):
    """Overwrite the Prices.csv with only header (clear contents).

    Args:
        directory (str)

    Returns:
        None
    """
    with open(
        Path(account_files_path(directory).joinpath("Prices.csv")), "w", newline=""
    ) as file:
        writer = csv.DictWriter(file, fieldnames=["symbol", "price", "date", "source"])
        writer.writeheader()


def updating_data(symbols, directory, updated_content):
    """Write updated price entries back into Prices.csv.

    Args:
        symbols (list of tuples)
        directory (str)
        updated_content (list of dicts)

    Returns:
        None
    """
    for i in range(len(symbols)):
        base_currency, quote_currency = symbols[i]
        append_price_entry(directory, base_currency, quote_currency, updated_content[i])


def group_symbols(currencies, dict_value="symbol"):
    """Convert list of currency dicts to list of (base,quote) tuples.

    Args:
        currencies (list[dict])
        dict_value (str): key where symbol string is stored.

    Returns:
        list[tuple[str,str]]
    """
    symbols = []
    for currency in currencies:
        symbols.append(
            re.fullmatch(r"FX:(\w{3})(\w{3})", currency[dict_value]).groups()
        )
    return symbols


def update_data(symbols):
    """Fetch fresh API data for each symbol tuple in list.

    Args:
        symbols (list of (base,quote) tuples)

    Returns:
        list: API responses (dicts).
    """
    updated_currencies = []
    for i in range(len(symbols)):
        base_currency, quote_currency = symbols[i]
        updated_currencies.append(frankfurter_api(base_currency, quote_currency))
    return updated_currencies


def update_symbol_data(base_currency, quote_currency):
    """Retrieve current price and date for single forex pair.

    Returns:
        tuple: (price, date_string)
    """
    content = frankfurter_api(base_currency, quote_currency)
    return content["rates"][quote_currency], content["date"]


def append_price_entry(directory, base_currency, quote_currency, api_content):
    """Append one price record to Prices.csv from API content.

    Args:
        directory (str)
        base_currency (str)
        quote_currency (str)
        api_content (dict)

    Returns:
        None
    """
    with open(
        Path(account_files_path(directory)).joinpath("Prices.csv"),
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


def rewrite_prices_file(directory, content):
    """Rewrite entire Prices.csv using provided list of records.

    Args:
        directory (str)
        content (list[dict])

    Returns:
        None
    """
    with open(
        Path(account_files_path(directory).joinpath("Prices.csv")), "w", newline=""
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


def rewrite_watchlist_file(directory, symbols):
    """Rewrite the watchlist CSV with given symbol records.

    Args:
        directory (str)
        symbols (list[dict])

    Returns:
        None
    """
    with open(
        Path(account_files_path(directory).joinpath("Watchlist.csv")),
        "w",
        newline="",
    ) as file:
        writer = csv.DictWriter(file, fieldnames=["Stocks"])
        writer.writeheader()
        for symbol in symbols:
            writer.writerow({"Stocks": symbol["Stocks"]})


def prompt_currencies():
    """Interactively choose base and quote currencies from list.

    Returns:
        tuple[str,str]: selected base and quote currency codes.
    """
    currencies: list = ["USD", "EUR", "GBP", "SEK", "DKK", "NOK"]

    print_currency()
    base_currency = currencies[int(get_string("Choice: ", "^[1-7]$")) - 1]

    print("\nBase currency: ", base_currency)

    print_currency(type="quote")
    quote_currency = currencies[int(get_string("Choice: ", "^[1-7]$")) - 1]
    clear_terminal()
    print(f"Base currency: {base_currency}\nQuote currency: {quote_currency}")
    return base_currency, quote_currency


def prompt_confirmation():
    """Ask user for a confirmation and interpret a few affirmative replies.

    Returns:
        bool
    """
    return input("Are You Sure: ").lower().strip() in ["yes", "yeah", "ja", "are"]


def get_currency_data():
    """Fetch historical rate data for a chosen currency pair with range options.

    Returns:
        tuple: (base_currency, quote_currency, rates_dict)
    """
    base_currency, quote_currency = prompt_currencies()
    clear_terminal()
    print_currency_data_submenu(base_currency, quote_currency)
    task = prompt_task(3)
    end_date = date.today().isoformat()
    if task == "1":
        days = int(get_string("Enter the range of days:", r"^\d\d?$"))
        start_date = last_n_day(total_days=days)
    elif task == "2":
        start_date = last_n_day(total_days=7)
    elif task == "3":
        start_date = get_string("Enter start date (YYYY-MM-DD): ", r"^\d{4}-\d\d-\d\d$")
        end_date = get_string(
            "Enter end date press enter to skip: ", r"^(\d{4}-\d\d-\d\d)?$"
        )
        if end_date == "":
            end_date = None
    content = frankfurter_api(base_currency, quote_currency, start_date, end_date)
    return base_currency, quote_currency, content["rates"]


def print_currency_data_submenu(base_currency, quote_currency):
    """Display submenu when showing currency data range options.

    Args:
        base_currency (str)
        quote_currency (str)

    Returns:
        None
    """
    print(f"""Show prices for a symbol
Symbol: {base_currency}{quote_currency}

Choose range option:
  1) Last n days (buisness days buffer)
  2) Last week (7 business days buffer)
  3) Enter start date (YYYY-MM-DD), optional end date
  4) Back
""")


def last_n_day(total_days):
    """Calculate the date N business days before today.

    Args:
        total_days (int): number of business days to go back.

    Returns:
        date
    """
    today = date.today()
    while total_days != 0:
        today -= timedelta(days=1)
        if today.weekday() in [5, 6]:
            continue
        total_days -= 1
    return today


def prompt_task(limit):
    """Prompt for a numeric menu choice up to a given limit.

    Args:
        limit (int)

    Returns:
        str: chosen option.
    """
    return get_string("Choice: ", f"^[1-{limit}]$")


if __name__ == "__main__":
    get_currency_data()
    # print(last_n_day(7))

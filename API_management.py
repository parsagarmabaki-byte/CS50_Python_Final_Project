import requests
from login_management import get_string, acount_files_path
import csv, os
from pathlib import Path


def frankfurter_api(base="USD", symbols=None, start_date=None, end_date=None):
    if start_date:
        url = f"https://api.frankfurter.app/{start_date}?from={base}&to={symbols}"
        if end_date:
            url = f"https://api.frankfurter.app/{start_date}..{end_date}?from={base}&to={symbols}"
    else:
        url = f"https://api.frankfurter.dev/v1/latest?base={base}&symbols={symbols}"

    response = requests.get(url)
    return response.json()


def get_asset():
    print("Select asset type:\n1) Forex\n2) Crypto\n3) Back")
    return get_string("Choice: ", "^[1-3]$")


def print_currency(type="base"):
    print(
        f"\nSelect the {type} currency:\n1) USD\n2) EUR\n3) GBP\n4) SEK\n5) DKK\n6) NOK\n7) Back"
    )


def clear_terminal():
    os.system("cls")


def add_symbol(username):
    asset = get_asset()
    if asset == "1":
        base_currency, quote_currency = get_currencies()
        if get_confirmation():
            content = frankfurter_api(base=base_currency, symbols=quote_currency)
            for file_type in ["Watchlist", "Prices"]:
                if file_type == "Watchlist":
                    appending_watchlist(
                        directory=username,
                        base_currency=base_currency,
                        quote_currency=quote_currency,
                    )
                elif file_type == "Prices":
                    appending_Prices(
                        directory=username,
                        base_currency=base_currency,
                        quote_currency=quote_currency,
                        api_content=content,
                    )


def appending_watchlist(directory, base_currency, quote_currency):
    with open(
        Path(acount_files_path(directory)).joinpath("Watchlist.csv"),
        "a",
        newline="",
    ) as file:
        writer = csv.DictWriter(file, fieldnames=["Stocks"])
        writer.writerow({"Stocks": f"FX:{base_currency}{quote_currency}"})


def appending_Prices(directory, base_currency, quote_currency, api_content):
    with open(
        Path(acount_files_path(directory)).joinpath("Prices.csv"),
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


def get_currencies():
    currencies: list = ["USD", "EUR", "GBP", "SEK", "DKK", "NOK"]

    print_currency()
    base_currency = currencies[int(get_string("Choice: ", "^[1-7]$")) - 1]

    print("\nBase currency: ", base_currency)

    print_currency(type="quote")
    quote_currency = currencies[int(get_string("Choice: ", "^[1-7]$")) - 1]
    clear_terminal()
    print(f"Base currency: {base_currency}\nQuote currency: {quote_currency}")
    return base_currency, quote_currency


def get_confirmation():
    return input("Are You Sure: ").lower().strip() in ["yes", "yeah", "ja", "are"]


if __name__ == "__main__":
    add_symbol("Parsa Garmabaki")

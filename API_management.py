import requests
from login_management import get_string, acount_files_path, read_file
import csv, os
from pathlib import Path
import re
from pprint import pprint 
from datetime import date,timedelta


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


def update_prices(directory):
    file_path = Path(acount_files_path(directory).joinpath("Prices.csv"))
    currencies = read_file(file_path)
    symbols: list = group_symbols(currencies)
    updated_content = update_data(symbols)
    clearing_prices(directory)
    updating_data(symbols, directory, updated_content)


def clearing_prices(directory):
    with open(Path(acount_files_path(directory).joinpath("Prices.csv")), "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["symbol", "price", "date", "source"])
        writer.writeheader()


def updating_data(symbols, directory, updated_content):
    for i in range(len(symbols)):
        base_currency, quote_currency = symbols[i]
        appending_Prices(directory, base_currency, quote_currency, updated_content[i])


def group_symbols(currencies,dict_value="symbol"):
    symbols = []
    for currency in currencies:
        symbols.append(re.fullmatch(r"FX:(\w{3})(\w{3})", currency[dict_value]).groups())
    return symbols


def update_data(symbols):
    updated_currencies = []
    for i in range(len(symbols)):
        base_currency, qoute_currency = symbols[i]
        updated_currencies.append(frankfurter_api(base_currency, qoute_currency))
    return updated_currencies


def update_symbol_data(base_currency,quote_currency):
    content = frankfurter_api(base_currency,quote_currency)
    return content['rates'][quote_currency],content['date']


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


def clearing_writing_content(directory,content):
    with open (Path(acount_files_path(directory).joinpath("Prices.csv")),'w',newline='') as file:
            writer=csv.DictWriter(file,fieldnames=['symbol','price','date','source'])
            writer.writeheader()
            for element in content:
                writer.writerow({
                    'symbol':element['symbol'],
                    'price':element['price'],
                    'date':element['date'],
                    'source':element['source']
                })


def clearing_writing_watchlist(directory,symbols):
    with open(Path(acount_files_path(directory).joinpath("Watchlist.csv")),'w',newline='',) as file:
            writer = csv.DictWriter(file, fieldnames=["Stocks"])
            writer.writeheader()
            for symbol in symbols:
                writer.writerow({"Stocks": symbol["Stocks"]})


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


def get_currency_data():
    base_currency, quote_currency=get_currencies()
    clear_terminal()
    print_currency_data_submenu(base_currency,quote_currency)
    task=get_task(3)
    end_date=date.today().isoformat()
    if task == '1':
        days=int(get_string("Enter the range of days:",r"^\d\d?$"))
        start_date=last_n_day(total_days=days)
    elif task == '2':
        start_date=last_n_day(total_days=7)
    elif task == '3':
        start_date = get_string("Enter start date (YYYY-MM-DD): ",r"^\d{4}-\d\d-\d\d$")
        end_date = get_string("Enter end date press enter to skip: ",r"^(\d{4}-\d\d-\d\d)?$")
        if end_date == '':
            end_date=None
    content=frankfurter_api(base_currency,quote_currency,start_date,end_date)
    return base_currency,quote_currency,content['rates']
    

def print_currency_data_submenu(base_currency,quote_currency):
     print(f"""Show prices for a symbol
Symbol: {base_currency}{quote_currency}

Choose range option:
  1) Last n days (buisness days buffer)
  2) Last week (7 business days buffer)
  3) Enter start date (YYYY-MM-DD), optional end date
  4) Back
""")

def last_n_day(total_days):
   today=date.today()
   while total_days != 0:
       today-=timedelta(days=1)
       if today.weekday() in [5,6]:
           continue
       total_days-=1
   return today
       
def get_task(limit):
    return get_string("Choice: ", f"^[1-{limit}]$")

if __name__ == "__main__":
    get_currency_data()
    # print(last_n_day(7))

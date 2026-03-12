from login_management import get_string, read_file, enter_email, acount_files_path
from API_management import add_symbol, clear_terminal, get_confirmation, update_prices,update_symbol_data,group_symbols,clearing_writing_watchlist,get_task,clearing_writing_content,get_currency_data
import sys
from pathlib import Path
import csv
from pprint import pprint


def print_user_menu(username: str) -> None:
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


def user_menu(user):
    submenu: str = None
    task: str = None
    while submenu != "0":
        print_user_menu(user["username"])
        submenu, task = get_choice()
        menu(user, submenu, task)
    return user


def get_choice():
    while True:
        choice: tuple = get_string(
            "Choice: ",
            r"^(?:(1)(?:\.?([123]))?|(2)(?:\.([12]))?|(3)(?:\.([123]))?|(4)(?:\.([12]))?|(5)(?:\.([12]))?|(6)(?:\.([1234]))?|([0Q]))$",
            get_groups=True,
        )
        if choice[0] == "Q":
            sys.exit("System Exited")
        if len(choice) == 2:
            return choice[0], choice[1]
        else:
            return choice[0], None


def menu(user, submenu, task):
    if submenu == "1":
        watchlist(user["username"], task)
    elif submenu == "2":
        update_price_menu(task, user["username"])
    elif submenu == "3":
        view_prices(task,user['username'])
    elif submenu == "4":
        summary_analysis(task)
    elif submenu == "5":
        export_data(task)
    elif submenu == "6":
        acount(user, task)


def view_prices(task,username):
    clear_terminal()
    get_choice = False
    while task != "4":
        if get_choice is True or task is None:
            print_view_prices_submenu()
            task = get_task(limit=3)
            clear_terminal()
        if task == "1":
            base_currency,qoute_currency,data=get_currency_data()
            print_rates(data,base_currency,qoute_currency)
        elif task == "2":
            print_prices(username)
        get_choice = True


def print_view_prices_submenu():
    print("""View Prices
    1) Show prices for date range (optional)
    2) Show Watchlist prices
    3) Main options
""")


def print_rates(data,base_currency,quote_currency):
    print(f"""
=====================================
             {base_currency}/{quote_currency}
=====================================
              
  #   Date           Prices     
--------------------------------------------""")
    for i,(date,rates) in enumerate(data.items(),1):
        print(f"  {i}   {date}     {rates[quote_currency]}")
    


def update_price_menu(task, username):
    clear_terminal()
    get_choice = False
    while task != "3":
        if get_choice is True or task is None:
            print_update_price_submenu()
            task = get_task(limit=3)
            clear_terminal()
        if task == "1":
            update_prices(directory=username)
        elif task == "2":
            update_symbol(directory=username)
        get_choice = True

def update_symbol(directory):
    currencies,file_path,i=print_watchlist(directory,"Watchlist")
    choice = int(get_string("\nChoice: ", f"^[0-{i+1}]$"))
    if choice != i+1:
        symbols=group_symbols([currencies[choice]],dict_value="Stocks")
        base_currency,quote_currency=symbols[0]
        price,date=update_symbol_data(base_currency,quote_currency)

        prices_list=read_file(Path(acount_files_path(directory).joinpath("Prices.csv")))
        prices_list[choice]['price']=price
        prices_list[choice]['date']=date

        clearing_writing_content(directory,prices_list)
            



def print_update_price_submenu():
    print("""2) Update prices
    1) Update all watchlist symbols (latest)
    2) Update one symbol
    3) Main options
    """)


def watchlist(username, task):
    clear_terminal()
    get_choice = False
    while task != "4":
        if get_choice is True or task is None:
            print_watchlist_submenu()
            task = get_task(limit=4)
            clear_terminal()
        if task == "1":
            print_watchlist(username, "Watchlist")
        elif task == "2":
            add_symbol(username)
        elif task == "3":
            remove_symbol(username)
        get_choice = True


def remove_symbol(directory):
    symbols, file_path, i = print_watchlist(directory, "Remove symbol")
    content:list=read_file(Path(acount_files_path(directory).joinpath("Prices.csv")))
    choice = int(get_string("\nChoice: ", f"^[0-{i+1}]$"))
    if choice != i + 1:
        symbols.pop(choice)
        content.pop(choice)
        clearing_writing_watchlist(directory,symbols)    
        clearing_writing_content(directory,content)


def print_watchlist(username, filetype):
    file_path = Path(acount_files_path(username).joinpath("Watchlist.csv"))
    symbols = read_file(file_path)
    print(f"""
=====================================
            {filetype}
=====================================
              
  #   Symbol       
-------------------------------------""")
    for i, line in enumerate(symbols):
        print(f"  {i}   {line["Stocks"]}")
    print(f"  {i+1}   Main menu")
    print("-------------------------------------\n\n")
    return symbols, file_path, i

def print_prices(username):
    file_path = Path(acount_files_path(username).joinpath("Prices.csv"))
    prices=read_file(file_path)
    symbols=group_symbols(prices)
    print(f"""
=====================================
            Prices
=====================================
              
  #   Symbol     Price       Date           Source       
-------------------------------------------------------------------""")
    for i, line in enumerate(prices):
        print(f"  {i}   {symbols[i][0]}{symbols[i][1]}     {line['price']}     {line['date']}     {line['source']}")
    print("-------------------------------------------------------------------\n\n")
    return prices, file_path, i

def print_watchlist_submenu():
    print("""1) Watchlist
    1) View watchlist
    2) Add symbol (e.g., FX:USDSEK)
    3) Remove symbol
    4) Main menu
          """)


def acount(user, task):
    clear_terminal()
    get_chioce = False
    while task != "5":
        if get_chioce is True or task is None:
            print_acount_submenu()
            task = get_task(limit=5)
        if task == "1":
            acount_info(user)
        elif task == "2":
            change_email(user)
        elif task == "3":
            change_password(user)
        elif task == "4":
            pass
        get_chioce = True
    clear_terminal()


def print_acount_submenu():
    print("""6) Account
   1) Show account info (username/email)
   2) Change email (optional)
   3) Change password (optional)
   4) Delete account (danger)
   5) Main options
""")


def change_email(user):
    while True:
        new_email = enter_email()
        if new_email is None:
            break
        print(
            f"Old Email: {user["email"]}\nNew Email: {new_email}\n\nDo you want to change?"
        )
        if get_confirmation():
            user["email"] = new_email
            break


def change_password(user):
    while True:
        new_password = get_string("New Password: ", r".{3,24}").strip()
        if new_password == "":
            break
        repeated_password = input("Enter the new password again: ").strip()
        if new_password != repeated_password:
            print("\nPASSWORD DONT MATCHED\n")
            continue
        if get_confirmation():
            user["password"] = new_password
            break


def acount_info(user):
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

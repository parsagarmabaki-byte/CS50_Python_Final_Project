from login_management import get_string, read_file, enter_email,acount_files_path
from API_management import add_symbol,clear_terminal,get_confirmation
import sys
from pathlib import Path
import csv

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
   3.1) Show last N records for a symbol
   3.2) Show prices for date range (optional)

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
            r"^(?:(1)(?:\.?([123]))?|(2)(?:\.([12]))?|(3)(?:\.([12]))?|(4)(?:\.([123]))?|(5)(?:\.([12]))?|(6)(?:\.([1234]))?|([0Q]))$",
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
        watchlist(user["username"],task)
    elif submenu == "2":
        update_prices(task)
    elif submenu == "3":
        view_prices(task)
    elif submenu == "4":
        summary_analysis(task)
    elif submenu == "5":
        export_data(task)
    elif submenu == "6":
        acount(user, task)


def watchlist(username,task):
    clear_terminal()
    get_choice = False
    while task != "4":
        if get_choice is True or task is None:
            print_watchlist_submenu()
            task = get_task(limit=4)
            clear_terminal()
        if task == "1":
            print_watchlist(username,"Watchlist")
        elif task == "2":
            add_symbol(username)
        elif task == "3":
            remove_symbol(username)
        get_choice=True


def remove_symbol(directory):
    symbols,file_path,i=print_watchlist(directory,"Remove symbol")
    choice=int(get_string("\nChoice: ",f"^[0-{i+1}]$"))
    if choice != i+1:
        symbols.pop(choice)
        with open(file_path.joinpath("Watchlist.csv"),"w",newline='') as file:
            writer=csv.DictWriter(file,fieldnames=["Stocks"])
            writer.writeheader()
            for symbol in symbols:
                writer.writerow({"Stocks":symbol["Stocks"]})


def print_watchlist(username,filetype):
    file_path=Path(acount_files_path(username).joinpath("Watchlist.csv"))
    symbols=read_file(file_path)
    print(f"""
=====================================
            {filetype}
=====================================
              
  #   Symbol       
-------------------------------------""")
    for i,line in enumerate(symbols):
        print (f"  {i}   {line["Stocks"]}")
    print(f"  {i+1}   Main menu")
    print("-------------------------------------\n\n")
    return symbols,file_path,i


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


def get_task(limit):
    return get_string("Choice: ", f"^[1-{limit}]$")


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

# final_project/cli.py
import argparse
from pathlib import Path
from .repositories import CSVAccountRepository, CSVWatchlistRepository, CSVPricesRepository
from .api_clients import FrankfurterClient
from .services import AccountService, WatchlistService
from .config import DATA_DIR

def build_services(data_dir: Path = DATA_DIR):
    account_repo = CSVAccountRepository(data_dir / "Accounts.csv")
    watch_repo = CSVWatchlistRepository(data_dir)
    prices_repo = CSVPricesRepository(data_dir)
    api_client = FrankfurterClient()
    return AccountService(account_repo), WatchlistService(watch_repo, prices_repo, api_client)

def run_cli():
    acc_svc, watch_svc = build_services()
    parser = argparse.ArgumentParser(prog="final_project")
    parser.add_argument("--demo-register", nargs=3, metavar=("username","password","email"), help="register a demo user")
    parser.add_argument("--demo-add-symbol", nargs=3, metavar=("username","base","quote"), help="add symbol for user")
    args = parser.parse_args()
    if args.demo_register:
        username, password, email = args.demo_register
        acc = acc_svc.register(username, password, email)
        print(f"Registered: {acc.username} created={acc.created}")
    if args.demo_add_symbol:
        username, base, quote = args.demo_add_symbol
        pr = watch_svc.add_symbol(username, base, quote)
        print(f"Added symbol {pr.symbol} price={pr.price} date={pr.date}")

if __name__ == "__main__":
    run_cli()

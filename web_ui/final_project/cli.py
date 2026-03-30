# final_project/cli.py
"""Command-line interface for the final project application.

This module provides CLI functions and argument parsing for registering users,
adding symbols to watchlists, and building service instances.
"""
import argparse
from pathlib import Path
from .repositories import CSVAccountRepository, CSVWatchlistRepository, CSVPricesRepository
from .api_clients import FrankfurterClient
from .services import AccountService, WatchlistService
from .config import DATA_DIR, ACCOUNT_DIR


def build_services(data_dir: Path = DATA_DIR):
    """Build and return service instances with their dependencies.

    Creates all repository instances and the API client, then constructs
    AccountService and WatchlistService with the appropriate dependencies.

    Args:
        data_dir: The directory where CSV data files are stored.
                  Defaults to DATA_DIR.

    Returns:
        A tuple of (AccountService, WatchlistService) instances.
    """
    account_repo = CSVAccountRepository(data_dir / "Accounts.csv")
    # Watchlist and Prices repos use ACCOUNT_DIR (data_dir/account_directory)
    watch_repo = CSVWatchlistRepository(ACCOUNT_DIR)
    prices_repo = CSVPricesRepository(ACCOUNT_DIR)
    api_client = FrankfurterClient()
    return AccountService(account_repo), WatchlistService(watch_repo, prices_repo, api_client)


def run_cli():
    """Run the command-line interface with demo arguments.

    Parses command-line arguments for registering demo users and adding
    symbols to watchlists, then executes the corresponding operations.
    """
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
